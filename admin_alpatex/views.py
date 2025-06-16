from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from index.models import Producto, Perfil,  CalificacionVendedor, CalificacionCliente, ReporteVendedor, ReporteUsuario
from django.db.models import Avg
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib.auth.models import User
import openpyxl
from django.utils.timezone import now
from django.http import HttpResponse
from datetime import datetime
from .models import Membresia
from .forms import MembresiaForm
from django.core.mail import  EmailMultiAlternatives
from django.conf import settings
from django.db.models import Count, Q
from io import BytesIO
from reportlab.lib.pagesizes import letter # type: ignore
import os
from reportlab.pdfgen import canvas  # type: ignore
from reportlab.lib.utils import ImageReader # type: ignore
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
from Dm.utils import contar_mensajes_no_leidos


#renderiza la plantilla home_admin.html
def dashboard(request):
    return render(request, 'admin_alpatex/home_admin.html')

#vista que renderiza la plantilla home_admin.html
#Recopila y calcula datos del sistema para mostrarlos en la página principal del admin
def home_admin(request):
    # Totales y otros datos
    mensajes_no_leidos = contar_mensajes_no_leidos(request.user)

    #calcula la cantidad de usuarios, productos, reportes y promedios de calificaciones
    total_usuarios = User.objects.count()
    total_productos = Producto.objects.count()
    productos_pendientes = Producto.objects.filter(estado_revision='Pendiente').count()
    
    total_reportes_vendedor = ReporteVendedor.objects.count()
    total_reportes_usuario = ReporteUsuario.objects.count()

    # Promedios individuales
    promedio_puntaje_vendedor = CalificacionVendedor.objects.aggregate(avg=Avg('puntaje'))['avg'] or 0
    promedio_puntaje_cliente = CalificacionCliente.objects.aggregate(avg=Avg('puntaje'))['avg'] or 0

    # Promedio general ponderado
    count_vendedor = CalificacionVendedor.objects.count()
    count_cliente = CalificacionCliente.objects.count()
    total_calificaciones = count_vendedor + count_cliente

    if total_calificaciones > 0:
        promedio_puntaje_usuarios = (
            (promedio_puntaje_vendedor * count_vendedor) + 
            (promedio_puntaje_cliente * count_cliente)
        ) / total_calificaciones
    else:
        promedio_puntaje_usuarios = 0

    # Mejor vendedor promedio (usuario con mayor promedio en CalificacionVendedor)
    mejor_vendedor = CalificacionVendedor.objects.values('vendedor__id', 'vendedor__username') \
        .annotate(promedio=Avg('puntaje')) \
        .order_by('-promedio').first()

    # Mejor cliente promedio (usuario con mayor promedio en CalificacionCliente)
    mejor_cliente = CalificacionCliente.objects.values('cliente__id', 'cliente__username') \
        .annotate(promedio=Avg('puntaje')) \
        .order_by('-promedio').first()

    # Aquí combinamos ambos para obtener el mejor usuario general (el que tenga mayor promedio entre ambos)
    mejor_usuario = None
    if mejor_vendedor and mejor_cliente:
        if mejor_vendedor['promedio'] >= mejor_cliente['promedio']:
            mejor_usuario = {'username': mejor_vendedor['vendedor__username'], 'promedio': mejor_vendedor['promedio']}
        else:
            mejor_usuario = {'username': mejor_cliente['cliente__username'], 'promedio': mejor_cliente['promedio']}
    elif mejor_vendedor:
        mejor_usuario = {'username': mejor_vendedor['vendedor__username'], 'promedio': mejor_vendedor['promedio']}
    elif mejor_cliente:
        mejor_usuario = {'username': mejor_cliente['cliente__username'], 'promedio': mejor_cliente['promedio']}

    # Lista de productos pendientes (los 5 más recientes)
    # Se ordenan por fecha de creación descendente 
    productos_pendientes_list = Producto.objects.filter(estado_revision='Pendiente').order_by('-fecha_creacion')[:5]

    context = {
        'total_usuarios': total_usuarios,
        'total_productos': total_productos,
        'productos_pendientes': productos_pendientes,
        'total_reportes_vendedor': total_reportes_vendedor,
        'total_reportes_usuario': total_reportes_usuario,
        'promedio_puntaje_usuarios': round(promedio_puntaje_usuarios, 2),
        'mejor_usuario': mejor_usuario,
        'productos_pendientes_list': productos_pendientes_list,
        'mensajes_no_leidos': mensajes_no_leidos

    }
    return render(request, 'admin_alpatex/home_admin.html', context)

@login_required
def menu(request):
    request.session["usuario"]="cgarcia"
    usuario=request.session["usuario"]
    context={'usuario':usuario}
    return render(request, 'admin_alpatex/home_admin.html', context)

#permite al administrador aceptar o rechazar productos que están pendientes de revisión
def gestionar_productos(request):
    if request.method == 'POST':
        # Obtener el ID del producto y la acción desde el formulario
        # Se espera que el formulario envíe un campo 'producto_id' y 
        # 'accion'puede ser 'aceptar' o 'rechazar'
        producto_id = request.POST.get('producto_id')
        accion = request.POST.get('accion')
        print(f"Producto ID recibido: {producto_id}, Acción: {accion}")

        # Validar si viene producto_id vacío
        if not producto_id:
            messages.error(request, "Error: No se recibió el ID del producto.")
            return redirect('gestionar_productos')

        # Obtener el producto por ID, o mostrar un error 404 si no existe
        producto = get_object_or_404(Producto, id_producto=producto_id)

        # Validar la acción recibida
        if accion == 'aceptar':
            # Acepta el producto, cambia su estado de revisión
            producto.estado_revision = 'Aceptado'
            producto.save()
            messages.success(request, "Producto aceptado correctamente.")
        elif accion == 'rechazar':
            # Rechaza el producto, cambia su estado de revisión y guarda el motivo
            # Se espera que el formulario envíe un campo 'motivo'
            motivo = request.POST.get('motivo')
            if motivo:
                producto.estado_revision = 'Rechazado'
                producto.motivo_rechazo = motivo
                producto.save()
                messages.success(request, "Producto rechazado correctamente.")
            else:
                messages.error(request, "Debes indicar el motivo de rechazo.")
        else:
            messages.error(request, "Acción no válida.")        
        return redirect('gestionar_productos')

    # Obtener productos pendientes y ordenarlos por prioridad (por los planes de membresía)
    productos_pendientes = Producto.objects.filter(estado_revision='Pendiente')
    productos_pendientes = sorted(productos_pendientes, key=lambda p: p.prioridad_verificacion)

    return render(request, 'admin_alpatex/gestion_productos.html', {'productos_pendientes': productos_pendientes})


@login_required
def reporte_productos(request):
    # Obtiene todos los productos de la base de datos
    productos = Producto.objects.all()

    # Filtrado por nombre de producto
    nombre = request.GET.get('nombre', '')
    if nombre:
        productos = productos.filter(nombre__icontains=nombre)

    # Filtrado por fecha de creación
    fecha_inicio = request.GET.get('fecha_inicio', '')
    fecha_fin = request.GET.get('fecha_fin', '')
    if fecha_inicio and fecha_fin:
        productos = productos.filter(fecha_creacion__range=[fecha_inicio, fecha_fin])

    # Filtrado por nombre de usuario
    nombre_usuario = request.GET.get('usuario', '')
    if nombre_usuario:
        productos = productos.filter(usuario__username__icontains=nombre_usuario)

    # Si el parámetro "exportar" está presente en la URL, generar el archivo Excel
    if request.GET.get('exportar', '') == 'excel':
        return export_to_excel(request)

    return render(request, 'admin_alpatex/reporte_productos.html', {'productos': productos})


# Función para exportar los productos a un archivo Excel
def export_to_excel(request):
    # Crea un libro de trabajo de Excel
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Productos"
    
    # Títulos de las columnas
    ws.append(['Nombre', 'Usuario', 'Fecha de Creación', 'Dirección', 'Estado de Revisión', 'Motivo de Rechazo'])
    
    # Obtener los productos desde la base de datos
    productos = Producto.objects.all()

    # Añadir los datos a las filas
    for producto in productos:
        ws.append([ 
            producto.nombre,
            producto.usuario.username,
            producto.fecha_creacion.strftime('%d %b %Y'),
            producto.usuario.perfil.direccion,
            producto.estado_revision,
            producto.motivo_rechazo if producto.estado_revision == 'Rechazado' else 'N/A',
        ])
    
    # Crea una respuesta HTTP para descargar el archivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=report.xlsx'
    wb.save(response)
    return response

# Permite buscar y filtrar usuarios normales por nombre y membresía 
# para gestionarlos desde el panel de admin
def usuarios(request):
    # Se obtienen los parámetros de la solicitud GET
    query = request.GET.get('q')
    membresia = request.GET.get('membresia')

    # Filtra los usuarios que no son superusuarios ni staff, y que no tienen fecha de eliminación
    usuarios = User.objects.select_related('perfil').filter(
        perfil__fecha_eliminacion__isnull=True,
        is_superuser=False,
        is_staff=False
    )
    # Si se proporciona un término de búsqueda, filtra los usuarios por nombre de usuario
    # Si se proporciona una membresía, filtra los usuarios por la membresía asociada
    if query:
        usuarios = usuarios.filter(username__icontains=query)
    if membresia:
        if membresia == 'Sin':
            usuarios = usuarios.filter(perfil__membresia__isnull=True)
        else:
            usuarios = usuarios.filter(perfil__membresia__nombre=membresia)
    return render(request, 'admin_alpatex/usuarios.html', {'usuarios': usuarios})

# Permite al administrador eliminar un usuario normal, marcando su perfil como eliminado
def reactivar_usuario(request, user_id):
    # Verifica que el usuario tenga permisos de administrador
    user = get_object_or_404(User, id=user_id)
    # Verifica que el usuario tenga un perfil asociado
    perfil = user.perfil

    # Verifica que el perfil tenga una fecha de eliminación
    # si no tiene fecha de eliminación, redirige a la lista de usuarios eliminados
    # si tiene fecha de eliminación, procede a reactivarlo
    if request.method == 'POST':
        perfil.fecha_eliminacion = None
        perfil.motivo_eliminacion = ''
        perfil.save()
        user.is_active = True
        user.save()

        # Contexto para el correo
        context = {
            'username': user.username,
            'site_url': request.build_absolute_uri('/'),
        }

        html_content = render_to_string('admin_alpatex/cuenta_reactivada.html', context)
        subject = "Tu cuenta fue reactivada - Alpatex"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]
        text = (
            f"Hola {user.username},\n\n"
            "Tu cuenta en Alpatex ha sido reactivada.\n\n"
            "Saludos,\nEquipo Alpatex"
        )

        # Enviar correo electrónico
        msg = EmailMultiAlternatives(subject, text, from_email, to)
        msg.attach_alternative(html_content, "text/html")

        # Adjuntar imagen
        logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'alpatex-v2-tipografía.png')
        with open(logo_path, 'rb') as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', '<logo_alpatex>')
            mime_image.add_header('Content-Disposition', 'inline', filename='alpatex-v2-tipografía.png')
            msg.attach(mime_image)
        msg.send()

        return redirect('usuarios_eliminados')
    return redirect('usuarios_eliminados')


# Permite al administrador ver los usuarios eliminados
# los que tienen una fecha de eliminación en su perfil
def usuarios_eliminados(request):
    # Obtiene todos los perfiles de usuario que tienen una fecha de eliminación
    perfiles = Perfil.objects.filter(fecha_eliminacion__isnull=False)
    # Se ordenan por fecha de eliminación descendente
    return render(request, 'admin_alpatex/usuarios_eliminados.html', {'perfiles': perfiles})

# Permite al administrador ver el perfil de un usuario normal
# incluyendo sus calificaciones y reportes recibidos
@login_required
def perfil_usuario(request, username):
    # Obtiene el usuario por su nombre de usuario
    # Si no existe, devuelve un error 404
    usuario = get_object_or_404(User, username=username)
    # Verifica que el usuario tenga un perfil asociado
    perfil = get_object_or_404(Perfil, user=usuario)
    
    opiniones = []

    # Calificaciones vendedor
    calificaciones_vendedor = CalificacionVendedor.objects.filter(vendedor=usuario).select_related('comprador', 'producto')
    # Se obtienen las calificaciones del vendedor y se agregan a la lista de opiniones
    for calificacion in calificaciones_vendedor:
        perfil_comprador = getattr(calificacion.comprador, 'perfil', None)
        foto = perfil_comprador.get_foto_perfil_url() if perfil_comprador else None
        opiniones.append({
            'tipo': 'calificacion',
            'usuario': calificacion.comprador.username,
            'foto': foto,
            'puntaje': calificacion.puntaje,
            'comentario': calificacion.comentario,
            'producto': calificacion.producto.nombre,
            'fecha': calificacion.fecha_creacion,
        })

    # Calificaciones cliente 
    calificaciones_cliente = CalificacionCliente.objects.filter(cliente=usuario).select_related('vendedor', 'producto')
    for calificacion in calificaciones_cliente:
        perfil_vendedor = getattr(calificacion.vendedor, 'perfil', None)
        foto = perfil_vendedor.get_foto_perfil_url() if perfil_vendedor else None
        opiniones.append({
            'tipo': 'calificacion_cliente',
            'usuario': calificacion.vendedor.username,
            'foto': foto,
            'puntaje': calificacion.puntaje,
            'comentario': calificacion.comentario,
            'producto': calificacion.producto.nombre,
            'fecha': calificacion.fecha,
        })

    # Reportes recibidos
    reportes_recibidos = ReporteVendedor.objects.filter(vendedor=usuario).select_related('comprador')
    for reporte in reportes_recibidos:
        perfil_comprador = getattr(reporte.comprador, 'perfil', None)
        foto = perfil_comprador.get_foto_perfil_url() if perfil_comprador else None
        opiniones.append({
            'tipo': 'reporte',
            'usuario': reporte.comprador.username,
            'foto': foto,
            'puntaje': reporte.puntaje,
            'motivo': reporte.motivo,
            'fecha': reporte.fecha_reporte,
        })

    # Ordenar opiniones por fecha descendente
    opiniones.sort(key=lambda x: x['fecha'], reverse=True)
    
    context = {
        'perfil': perfil,
        'usuario': usuario,
        'opiniones': opiniones,
    }
    
    return render(request, 'admin_alpatex/perfil.html', context)


#Membresias
# Listado
def listar_membresias(request):
    # Obtiene todas las membresías disponibles
    # y las pasa al contexto para renderizar la plantilla
    membresias = Membresia.objects.all()
    return render(request, 'admin_alpatex/membresia_list.html', {'membresias': membresias})

# Crear
def crear_membresia(request):
    # Si la solicitud es POST, se procesa el formulario
    # Si es GET, se muestra un formulario vacío para crear una nueva membresía
    if request.method == 'POST':
        # Crea una instancia del formulario con los datos POST
        # y valida los datos ingresados
        form = MembresiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    
    # Si la solicitud es GET, se muestra un formulario vacío
    # para crear una nueva membresía
    else:
        form = MembresiaForm()
    # Renderiza la plantilla con el formulario
    # para crear o editar una membresía
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})

# Editar una membresia existente
def editar_membresia(request, membresia_id):
    # Obtiene la membresía por su ID, o devuelve un error 404 si no existe
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    # Si la solicitud es POST, se procesa el formulario
    if request.method == 'POST':
        # Crea una instancia del formulario con los datos POST
        # y la instancia de la membresía para editar
        form = MembresiaForm(request.POST, instance=membresia)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    # Si la solicitud es GET, se muestra el formulario con los datos de la membresía para editar
    else:
        form = MembresiaForm(instance=membresia)
    # Renderiza la plantilla con el formulario para editar la membresía
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})

# Eliminar una membresía existente
def eliminar_membresia(request, membresia_id):
    # Obtiene la membresía por su ID, o devuelve un error 404 si no existe
    # Luego la elimina y redirige a la lista de membresías
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    membresia.delete()
    return redirect('listar_membresias')

# Permite al administrador ver los detalles de un producto específico
# incluyendo su información, calificaciones y reportes recibidos
@login_required
@user_passes_test(lambda u: u.is_staff)
def ver_producto_admin(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)
    return render(request, 'admin_alpatex/ver_producto.html', {'producto': producto})

# Permite al administrador eliminar un usuario normal
# marcando su perfil como eliminado y enviando un correo de notificación
def eliminar_usuario(request, user_id):
    # Verifica que el usuario tenga permisos de administrador
    # Obtiene el usuario por su ID, o devuelve un error 404 si no existe
    user = get_object_or_404(User, id=user_id)
    perfil = user.perfil

    #con el metodo post, se marca el perfil como eliminado
    # y se guarda la fecha de eliminación y el motivo
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')

        perfil.fecha_eliminacion = now()
        perfil.motivo_eliminacion = motivo
        perfil.save()

        # Preparar correo
        context = {
            'username': user.username,
            'motivo': motivo,
            'site_url': request.build_absolute_uri('/'),
        }

        html_content = render_to_string('admin_alpatex/cuenta_eliminada.html', context)
        subject = "Cuenta eliminada - Alpatex"
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [user.email]
        text_content = (
            f"Hola {user.username},\n\n"
            "Tu cuenta ha sido eliminada de Alpatex por incumplir nuestras políticas.\n"
            f"Motivo: {motivo}\n\n"
            "Si crees que esto fue un error, contáctanos.\n\n"
            "Saludos,\nEquipo Alpatex"
        )

        msg = EmailMultiAlternatives(subject, text_content, from_email, to)
        msg.attach_alternative(html_content, "text/html")

        logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'alpatex-v2-tipografía.png')
        with open(logo_path, 'rb') as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', '<logo_alpatex>')
            mime_image.add_header('Content-Disposition', 'inline', filename='alpatex-v2-tipografía.png')
            msg.attach(mime_image)

        msg.send()

        return redirect('usuarios') 
    # NO devolver usuarios.html directamente desde aquí
    return redirect('usuarios')

# Permite al administrador ver los usuarios reportados
@login_required
def usuarios_reportados(request):
    # Contar reportes recibidos como vendedor y como usuario
    #filtra los usuarios que tienen al menos un reporte recibido
    # ya sea como vendedor o como usuario
    usuarios = User.objects.annotate(
        num_reportes_vendedor=Count('reportes_recibidos', distinct=True),
        num_reportes_usuario=Count('reportes_usuario', distinct=True)
    ).filter(
        Q(num_reportes_vendedor__gt=0) | Q(num_reportes_usuario__gt=0)
    )

    return render(request, 'admin_alpatex/usuarios_reportados.html', {
        'usuarios': usuarios
    })

# Permite al administrador generar un reporte de usuarios
def reporte_usuarios(request):
    # Filtrar usuarios que no sean admin (superusuario) o staff
    usuarios = User.objects.filter(
        Q(is_superuser=False) & Q(is_staff=False)
    )
    
    # Aplicar filtros de búsqueda si vienen en GET
    username = request.GET.get('username')
    email = request.GET.get('email')
    estado = request.GET.get('estado')

    # Filtrar por nombre de usuario, email y estado
    if username:
        usuarios = usuarios.filter(username__icontains=username)
    if email:
        usuarios = usuarios.filter(email__icontains=email)
    if estado:
        if estado == 'activo':
            usuarios = usuarios.filter(perfil__fecha_eliminacion__isnull=True)
        elif estado == 'eliminado':
            usuarios = usuarios.filter(perfil__fecha_eliminacion__isnull=False)

    context = {
        'usuarios': usuarios,
    }
    return render(request, 'admin_alpatex/reporte_usuarios.html', context)

# Permite al administrador exportar el reporte de productos a un archivo Excel
def export_to_pdf(request):
    # Crea un buffer en memoria para el PDF
    buffer = BytesIO()
    # Crea un objeto Canvas de ReportLab para generar el PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    # Obtiene el tamaño de la página
    width, height = letter

    # Ruta absoluta del logo
    logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'ALPATEX-V2-tipografía.jpg')

    # Posición centrada del logo (ancho 180)
    pos_x = (width - 180) / 2
    pos_y = height - 100  # margen arriba

    try:
        logo = ImageReader(logo_path)
        p.drawImage(logo, pos_x, pos_y, width=180, height=90, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Título centrado debajo del logo (asumiendo ancho del texto aprox 150)
# Título centrado debajo del logo (subido un poco)
    title = "Reporte de Productos"
    p.setFont("Helvetica-Bold", 16)
    text_width = p.stringWidth(title, "Helvetica-Bold", 16)
    title_x = (width - text_width) / 2
    p.drawString(title_x, pos_y - 8, title)  # <- menos distancia para subir


    # Encabezados de la tabla
    p.setFont("Helvetica-Bold", 10)
    headers = ['Nombre', 'Usuario', 'Fecha', 'Dirección', 'Estado', 'Motivo']
    x_list = [30, 130, 230, 330, 430, 510]
    y = pos_y - 70  # empieza debajo del título
    for i, header in enumerate(headers):
        p.drawString(x_list[i], y, header)

    # Datos de productos
    productos = Producto.objects.all()
    y -= 20
    p.setFont("Helvetica", 8)

    # Función para truncar el texto si es demasiado largo
    def truncar(texto, max_len=25):
        texto = str(texto)
        return texto if len(texto) <= max_len else texto[:max_len-3] + "..."

    # Itera sobre los productos y escribe sus datos en el PDF
    # Se truncan los textos
    for prod in productos:
        datos = [
            truncar(prod.nombre),
            truncar(prod.usuario.username),
            prod.fecha_creacion.strftime('%d %b %Y'),
            truncar(prod.usuario.perfil.direccion),
            truncar(prod.estado_revision, 15),
            truncar(prod.motivo_rechazo if prod.estado_revision == 'Rechazado' else 'N/A', 20),
        ]
        for i, dato in enumerate(datos):
            p.drawString(x_list[i], y, dato)
        y -= 15
        if y < 50:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 8)

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')

# Permite al administrador exportar el reporte de usuarios a un archivo Excel
def export_usuarios_to_excel(request):
    # Crea un libro de trabajo de Excel
    wb = openpyxl.Workbook()
    # Selecciona la hoja activa y le asigna un título
    ws = wb.active
    ws.title = "Reporte de Usuarios"

    # Títulos de columnas
    ws.append(['Username', 'Email', 'Fecha de creación', 'Estado', 'Fecha eliminación'])

    # Filtra los usuarios que no son superusuarios ni staff
    usuarios = User.objects.filter(
        Q(is_superuser=False) & Q(is_staff=False)
    )

    # Si hay filtros en la solicitud GET, aplica los filtros
    #filtra por nombre de usuario, email y estado
    for user in usuarios:
        perfil = getattr(user, 'perfil', None)
        fecha_eliminacion = perfil.fecha_eliminacion if perfil else None
        estado = 'Eliminado' if fecha_eliminacion else 'Activo'

        # Si el usuario tiene un perfil, se obtiene la fecha de eliminación
        # Si no tiene perfil, se considera que está activo
        ws.append([
            user.username,
            user.email,
            user.date_joined.strftime('%d %b %Y'),
            estado,
            fecha_eliminacion.strftime('%d %b %Y') if fecha_eliminacion else 'N/A',
        ])
    # Crea una respuesta HTTP para descargar el archivo Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=reporte_usuarios.xlsx'
    wb.save(response)
    return response

# Permite al administrador exportar el reporte de usuarios a un archivo PDF
def export_usuarios_to_pdf(request):
    # Crea un buffer en memoria para el PDF
    buffer = BytesIO()
    # Crea un objeto Canvas de ReportLab para generar el PDF
    p = canvas.Canvas(buffer, pagesize=letter)
    # Obtiene el tamaño de la página
    width, height = letter

    # Logo
    logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'ALPATEX-V2-tipografía.jpg')
    pos_x = (width - 180) / 2
    pos_y = height - 100

    try:
        logo = ImageReader(logo_path)
        p.drawImage(logo, pos_x, pos_y, width=180, height=90, preserveAspectRatio=True)
    except Exception as e:
        print(f"Error al cargar el logo: {e}")

    # Título
    title = "Reporte de Usuarios"
    p.setFont("Helvetica-Bold", 16)
    text_width = p.stringWidth(title, "Helvetica-Bold", 16)
    title_x = (width - text_width) / 2
    p.drawString(title_x, pos_y - 8, title)

    # Encabezados tabla
    p.setFont("Helvetica-Bold", 10)
    headers = ['Username', 'Email', 'Fecha creación', 'Estado', 'Fecha eliminación', 'Motivo de Eliminación']
    x_list = [15, 80, 200, 290, 350, 450]  # Posiciones X para las 6 columnas
    y = pos_y - 70
    for i, header in enumerate(headers):
        p.drawString(x_list[i], y, header)

    # Datos usuarios
    usuarios = User.objects.filter(
        Q(is_superuser=False) & Q(is_staff=False)
    )
    y -= 20
    p.setFont("Helvetica", 8)

    def truncar(texto, max_len=25):
        texto = str(texto)
        return texto if len(texto) <= max_len else texto[:max_len-3] + "..."

    # Itera sobre los usuarios y escribe sus datos en el PDF
    # Se truncan los textos para que no excedan el ancho de la columna
    for user in usuarios:
        perfil = getattr(user, 'perfil', None)
        fecha_eliminacion = perfil.fecha_eliminacion if perfil else None
        motivo_eliminacion = perfil.motivo_eliminacion if perfil and hasattr(perfil, 'motivo_eliminacion') else 'N/A'
        estado = 'Eliminado' if fecha_eliminacion else 'Activo'

        datos = [
            truncar(user.username),
            truncar(user.email, 30),
            user.date_joined.strftime('%d %b %Y'),
            estado,
            fecha_eliminacion.strftime('%d %b %Y') if fecha_eliminacion else 'N/A',
            truncar(motivo_eliminacion, 30),
        ]
        for i, dato in enumerate(datos):
            p.drawString(x_list[i], y, dato)
        y -= 15
        if y < 30:
            p.showPage()
            y = height - 50
            p.setFont("Helvetica", 8)
    
    # Finaliza el PDF y lo guarda en el buffer
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')