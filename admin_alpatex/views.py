from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from index.models import Producto, Perfil,  CalificacionVendedor, CalificacionCliente, ReporteVendedor
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




def dashboard(request):
    return render(request, 'admin_alpatex/home_admin.html')

def home_admin(request):
    usuarios = User.objects.all()
    productos = Producto.objects.all()  # Obtener todos los productos
    context = {"usuarios": usuarios, "productos": productos}  # Pasar la variable 'productos'
    return render(request, 'admin_alpatex/home_admin.html', context)

@login_required
def menu(request):
    request.session["usuario"]="cgarcia"
    usuario=request.session["usuario"]
    context={'usuario':usuario}
    return render(request, 'admin_alpatex/home_admin.html', context)




def gestionar_productos(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        accion = request.POST.get('accion')
        print(f"Producto ID recibido: {producto_id}, Acción: {accion}")

        # Validar si viene producto_id vacío
        if not producto_id:
            messages.error(request, "Error: No se recibió el ID del producto.")
            return redirect('gestionar_productos')

        producto = get_object_or_404(Producto, id_producto=producto_id)

        if accion == 'aceptar':
            producto.estado_revision = 'Aceptado'
            producto.save()
            messages.success(request, "Producto aceptado correctamente.")
        elif accion == 'rechazar':
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

    # Obtener productos pendientes y ordenarlos por prioridad
    productos_pendientes = Producto.objects.filter(estado_revision='Pendiente')
    productos_pendientes = sorted(productos_pendientes, key=lambda p: p.prioridad_verificacion)

    return render(request, 'admin_alpatex/gestion_productos.html', {'productos_pendientes': productos_pendientes})

@login_required
def reporte_productos(request):
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


def usuarios(request):
    query = request.GET.get('q')
    membresia = request.GET.get('membresia')

    usuarios = User.objects.select_related('perfil').filter(
        perfil__fecha_eliminacion__isnull=True,
        is_superuser=False,
        is_staff=False
    )
    if query:
        usuarios = usuarios.filter(username__icontains=query)
    if membresia:
        if membresia == 'Sin':
            usuarios = usuarios.filter(perfil__membresia__isnull=True)
        else:
            usuarios = usuarios.filter(perfil__membresia__nombre=membresia)

    return render(request, 'admin_alpatex/usuarios.html', {'usuarios': usuarios})
def reactivar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    perfil = user.perfil

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

def usuarios_eliminados(request):
    perfiles = Perfil.objects.filter(fecha_eliminacion__isnull=False)
    return render(request, 'admin_alpatex/usuarios_eliminados.html', {'perfiles': perfiles})



@login_required
def perfil_usuario(request, username):
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=usuario)
    
    opiniones = []

    # Calificaciones vendedor
    calificaciones_vendedor = CalificacionVendedor.objects.filter(vendedor=usuario).select_related('comprador', 'producto')
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

    # Calificaciones cliente (si quieres incluirlas también)
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
    membresias = Membresia.objects.all()
    return render(request, 'admin_alpatex/membresia_list.html', {'membresias': membresias})

# Crear
def crear_membresia(request):
    if request.method == 'POST':
        form = MembresiaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    else:
        form = MembresiaForm()
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})
@login_required
@user_passes_test(lambda u: u.is_staff)
def ver_producto_admin(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)
    return render(request, 'admin_alpatex/ver_producto.html', {'producto': producto})
# Editar
def editar_membresia(request, membresia_id):
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    if request.method == 'POST':
        form = MembresiaForm(request.POST, instance=membresia)
        if form.is_valid():
            form.save()
            return redirect('listar_membresias')
    else:
        form = MembresiaForm(instance=membresia)
    return render(request, 'admin_alpatex/membresia_form.html', {'form': form})

# Eliminar
def eliminar_membresia(request, membresia_id):
    membresia = get_object_or_404(Membresia, pk=membresia_id)
    membresia.delete()
    return redirect('listar_membresias')

def eliminar_usuario(request, user_id):
    user = get_object_or_404(User, id=user_id)
    perfil = user.perfil

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

        return redirect('usuarios')  # ✅ CORRECTO
    # 🚫 NUNCA devuelvas usuarios.html directamente desde aquí
    return redirect('usuarios')
@login_required
def usuarios_reportados(request):
    # Obtener usuarios que han sido reportados al menos una vez
    usuarios = User.objects.filter(reportes_recibidos__isnull=False).annotate(
        num_reportes=Count('reportes_recibidos')
    ).distinct()

    return render(request, 'admin_alpatex/usuarios_reportados.html', {
        'usuarios': usuarios
    })

def reporte_usuarios(request):
    # Filtrar usuarios que no sean admin (superusuario) o staff
    usuarios = User.objects.filter(
        Q(is_superuser=False) & Q(is_staff=False)
    )
    
    # Aplicar filtros de búsqueda si vienen en GET (ejemplo)
    username = request.GET.get('username')
    email = request.GET.get('email')
    estado = request.GET.get('estado')

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


def export_to_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
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

    def truncar(texto, max_len=25):
        texto = str(texto)
        return texto if len(texto) <= max_len else texto[:max_len-3] + "..."

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
def export_usuarios_to_excel(request):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reporte de Usuarios"

    # Títulos de columnas
    ws.append(['Username', 'Email', 'Fecha de creación', 'Estado', 'Fecha eliminación'])

    usuarios = User.objects.filter(
        Q(is_superuser=False) & Q(is_staff=False)
    )

    for user in usuarios:
        perfil = getattr(user, 'perfil', None)
        fecha_eliminacion = perfil.fecha_eliminacion if perfil else None
        estado = 'Eliminado' if fecha_eliminacion else 'Activo'

        ws.append([
            user.username,
            user.email,
            user.date_joined.strftime('%d %b %Y'),
            estado,
            fecha_eliminacion.strftime('%d %b %Y') if fecha_eliminacion else 'N/A',
        ])

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=reporte_usuarios.xlsx'
    wb.save(response)
    return response

def export_usuarios_to_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
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

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')