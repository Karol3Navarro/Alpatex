from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Producto, Perfil, CalificacionVendedor, ReporteVendedor, CalificacionCliente
from .Forms import PerfilForm, ProductoForm, ReporteVendedorForm
import json
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from email.mime.image import MIMEImage
import os
from django.core.serializers.json import DjangoJSONEncoder
from admin_alpatex.models import Membresia, SuscripcionMercadoPago
from django.db.models import F
from django.contrib.messages import get_messages
from Dm.models import ConfirmacionEntrega
from Dm.forms import ConfirmacionEntregaForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.contrib import messages
from django.conf import settings
from admin_alpatex.services import MercadoPagoService
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from admin_alpatex.mercadopago_config import (
    MERCADOPAGO_PUBLIC_KEY,
    MERCADOPAGO_PUBLIC_KEY_PROD
)



def map(request):
    productos = Producto.objects.select_related('usuario').filter(
        disponible=True,
        estado_revision='Aceptado',
        direccion__isnull=False
    )
    productos_data = []
    
    for producto in productos:
        if producto.direccion:  # Solo productos que tengan dirección
            productos_data.append({
                'id': producto.id_producto,
                'nombre': producto.nombre,
                'direccion': producto.direccion,
                'vendedor': producto.usuario.username  # Opcional, si quieres mostrar quién lo vende
            })

    productos_json = json.dumps(productos_data, cls=DjangoJSONEncoder)

    context = {
        'perfiles_json': productos_json  # Puedes cambiarle el nombre si quieres, pero no es necesario
    }
    return render(request, 'index/map.html', context)

def logout(request):
    context={}
    return render(request, 'index/index.html', context)

@login_required
def menu(request):
    request.session["usuario"]="cgarcia"
    usuario=request.session["usuario"]
    context={'usuario':usuario}
    return render(request, 'index/home.html', context)


def index(request):
    storage = get_messages(request)
    for _ in storage:
        pass
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                perfil = user.perfil
            except Perfil.DoesNotExist:
                perfil = None

            if perfil and perfil.fecha_eliminacion is not None:
                # Usuario eliminado, no puede ingresar
                error_message = "Tu cuenta ha sido eliminada y no puedes ingresar."
                messages.error(request, error_message)
                return render(request, 'index/index.html', {'error_message': error_message})

            # Usuario activo, permite login
            login(request, user)
            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('home')

        else:
            error_message = "Credenciales incorrectas, por favor intenta nuevamente."
            messages.error(request, error_message)
            return render(request, 'index/index.html', {'error_message': error_message})

    return render(request, 'index/index.html')

def home(request):
    usuarios = User.objects.all()

    productos = Producto.objects.select_related('usuario__perfil__membresia').filter(
        estado_revision='Aceptado',
        disponible=True,
    ).annotate(
        prioridad_visibilidad=F('usuario__perfil__membresia__prioridad_visibilidad')
    ).order_by('-prioridad_visibilidad', '-fecha_creacion')

    context = {
        "usuarios": usuarios,
        "productos": productos,
    }
    return render(request, 'index/home.html', context)

def ver_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)
    
    # Incrementar el contador de visitas
    producto.contador_visitas += 1
    producto.save()

    context = {
        'producto': producto,
    }
    return render(request, 'index/ver_producto.html', context)

def registrar_usuario(request):
    if request.method == 'POST':
        username = request.POST['nombre_usuario']
        nombre_completo = request.POST['nombre_completo']
        rut = request.POST['rut']
        direccion = request.POST['direccion']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if User.objects.filter(username=username).exists():
            return render(request, 'index/registro.html', {'error': 'El nombre de usuario ya está en uso.'})
        if User.objects.filter(email=email).exists():
            return render(request, 'index/registro.html', {'error': 'El correo ya está registrado.'})
        if Perfil.objects.filter(rut=rut).exists():
            return render(request, 'index/registro.html', {'error': 'El RUT ya está registrado.'})
        if password1 != password2:
            return render(request, 'index/index.html', {'error': 'Las claves no coinciden.'})


        # Crear usuario y perfil
        user = User.objects.create_user(username=username, email=email, password=password1)
        user.first_name = nombre_completo
        user.save()

        perfil = Perfil.objects.create(user=user, rut=rut, direccion=direccion)
        perfil.save()

        # Contexto del correo
        context = {
            'username': username,
            'site_url': request.build_absolute_uri('/')[:-1],  # URL base sin slash final
        }

        # Renderizar HTML
        html_content = render_to_string('index/bienvenida.html', context)

        subject = '¡Bienvenido a Alpatex!'
        from_email = settings.DEFAULT_FROM_EMAIL
        to = [email]

        msg = EmailMultiAlternatives(subject, 'Gracias por registrarte en Alpatex.', from_email, to)
        msg.attach_alternative(html_content, "text/html")

        # Adjuntar imagen embebida
        logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'alpatex-v2-tipografía.png')
        with open(logo_path, 'rb') as img:
            mime_image = MIMEImage(img.read())
            mime_image.add_header('Content-ID', '<logo_alpatex>')
            mime_image.add_header('Content-Disposition', 'inline', filename='alpatex-v2-tipografía.png')
            msg.attach(mime_image)

        msg.send()

        messages.success(request, 'Usuario registrado correctamente.')
        return redirect('index')

    return render(request, 'index/registro.html')


@login_required
def perfil_usuario(request):
    perfil, created = Perfil.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Perfil actualizado con éxito.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "Hubo un error al actualizar el perfil.")
    else:
        form = PerfilForm(instance=perfil, user=request.user)

    return render(request, 'index/perfil.html', {'perfil': perfil, 'form': form})

 

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user.perfil)
        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user.perfil)

    return render(request, 'perfil/editar_perfil.html', {'form': form})

@login_required
def perfil_usuario(request):
    perfil, _ = Perfil.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=perfil, user=request.user)
        if form.is_valid():
            form.save(user=request.user)
            messages.success(request, "Perfil actualizado con éxito.")
            return redirect('perfil_usuario')
        else:
            messages.error(request, "Hubo un error al actualizar el perfil.")
    else:
        form = PerfilForm(instance=perfil, user=request.user)

    return render(request, 'index/perfil.html', {'perfil': perfil, 'form': form})

 

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user.perfil)
        if form.is_valid():
            form.save()
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user.perfil)

    return render(request, 'perfil/editar_perfil.html', {'form': form})

@login_required
def productos_perfil(request):
    productos = Producto.objects.filter(usuario=request.user)  # Filtramos por el usuario actual
    if not productos:
        mensaje = "No tienes productos agregados."
    else:
        mensaje = None
    return render(request, 'index/productos_perf.html', {
        'productos': productos, 
        'mensaje': mensaje,
        'membresia': request.user.perfil.membresia
    })


@login_required
def producto_add_perf(request):
    productos = Producto.objects.all()
    direccion_usuario = ""

    # Obtener la dirección del usuario autenticado
    if request.user.is_authenticated:
        try:
            direccion_usuario = request.user.perfil.direccion or ""
        except Perfil.DoesNotExist:
            direccion_usuario = ""

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.usuario = request.user
            producto.estado_revision = "Pendiente"
            producto.save()
            messages.success(request, "Producto creado con éxito!")
            return redirect('productos_perf')
        else:
            messages.error(request, "Por favor corrige los errores en el formulario.")
    else:
        # Pasar la dirección del usuario al formulario como valor predeterminado
        form = ProductoForm(initial={'direccion': direccion_usuario})

    context = {
        'form': form,
        'productos': productos,
        'direccion_usuario': direccion_usuario,
    }

    return render(request, 'index/producto_add_perf.html', context)

@login_required
def ver_membresia_usuario(request):
    perfil = request.user.perfil
    membresias = Membresia.objects.all()
    mp_service = MercadoPagoService()

    if request.method == 'POST':
        cancelar_id = request.POST.get('cancelar')
        if cancelar_id:
            try:
                suscripciones = SuscripcionMercadoPago.objects.filter(perfil=perfil, estado="active")
                if suscripciones.count() == 0:
                    return JsonResponse({"success": False, "error": "No tienes una suscripción activa."}, status=400)
                elif suscripciones.count() > 1:
                    for suscripcion in suscripciones:
                        mp_service.cancelar_suscripcion(suscripcion)
                    return JsonResponse({"success": True, "warning": "Había más de una suscripción activa, todas han sido canceladas."})
                else:
                    mp_service.cancelar_suscripcion(suscripciones.first())
                    return JsonResponse({"success": True})
            except Exception as e:
                messages.error(request, f"Error al cancelar la suscripción: {str(e)}")
            return redirect('ver_membresia_usuario')

        nueva_id = request.POST.get('membresia_id')
        if nueva_id:
            try:
                membresia = Membresia.objects.get(id=nueva_id)
                token_tarjeta = request.POST.get('token_tarjeta')
                
                if not token_tarjeta:
                    messages.error(request, "Error: No se recibió el token de la tarjeta")
                    return redirect('ver_membresia_usuario')

                suscripcion = mp_service.crear_suscripcion(perfil, membresia, token_tarjeta)
                perfil.membresia = membresia
                perfil.save()
                messages.success(request, "¡Suscripción creada exitosamente!")
            except Exception as e:
                messages.error(request, f"Error al crear la suscripción: {str(e)}")
            return redirect('ver_membresia_usuario')

    # Obtener la suscripción vigente (estado active o cancelled y fecha_fin > ahora)
    now = timezone.now()
    suscripcion_vigente = SuscripcionMercadoPago.objects.filter(
        perfil=perfil,
        fecha_fin__gt=now,
        estado__in=["active", "cancelled"]
    ).order_by('-fecha_inicio').first()
    
    membresia_activa = None
    mostrar_mensaje_cancelada = False
    
    if suscripcion_vigente:
        membresia_activa = suscripcion_vigente.membresia
        perfil.membresia = membresia_activa
        perfil.save()
        
        # Verificar si la suscripción está cancelada pero aún vigente
        if suscripcion_vigente.estado == "cancelled" and suscripcion_vigente.fecha_fin > now:
            mostrar_mensaje_cancelada = True

    return render(request, 'index/ver_membresia.html', {
        'perfil': perfil,
        'membresias': membresias,
        'suscripcion_activa': suscripcion_vigente,
        'membresia_activa': membresia_activa,
        'mercadopago_public_key_sandbox': MERCADOPAGO_PUBLIC_KEY,
        'mostrar_mensaje_cancelada': mostrar_mensaje_cancelada,
    })

#Modificacion de Producto
def editar_producto(request, pk):
    producto = get_object_or_404(Producto, id_producto=pk)

    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            return redirect('productos_perf')
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'index/editar_producto.html', {'form': form, 'producto': producto})

def producto_findEdit(request, pk):
    producto = get_object_or_404(Producto, id_producto=pk)
    if request.method == "POST":
        form = ProductoForm(request.POST, request.FILES, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, "Producto modificado correctamente.")
            return redirect('productos_perf')
        else:
            messages.error(request, "Error al modificar el producto.")
    else:
        form = ProductoForm(instance=producto)

    return render(request, 'index/editar_producto.html', {'form': form, 'producto': producto})

#Eliminar Producto
def producto_del(request,pk):
    context={}
    try:
        producto=Producto.objects.get(id_producto=pk)

        producto.delete()
        mensaje ="Producto Eliminado Correctamente"
        productos =Producto.objects.all()
        context = {'productos':productos, 'mensaje':mensaje}
        return render(request, 'index/producto_perfi.html', context)
    except:
        mensaje="Error, producto no existe"
        productos =Producto.objects.all()
        context = {'productos':productos, 'mensaje':mensaje}
        return render(request, 'index/productos_perf.html', context)

def redirigir_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.categoria == "Libro":
        return redirect('index/videojuegos.html')
    elif producto.categoria == "Videojuego":
        return redirect('index/libros.html')
    else:
        return redirect('index/productos.html')
        
@login_required
def libros(request):
    libros = Producto.objects.filter(categoria='Libro', estado_revision='Aceptado')  
    return render(request, 'index/libros.html', {'libros': libros})

@login_required
def videojuegos(request):
    videojuegos = Producto.objects.filter(categoria='Videojuego', estado_revision='Aceptado')  
    return render(request, 'index/videojuegos.html', {'videojuegos': videojuegos})


@login_required
def productos(request):
    # Filtrar productos aprobados con estado_revision='Aceptado'
    productos = Producto.objects.filter(estado_revision='Aceptado')
    return render(request, 'index/productos.html', {'productos': productos})

def ver_todo(request):
    productos = Producto.objects.filter(estado_revision='Aceptado')

    categoria = request.GET.get('categoria')
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')

    if categoria:
        productos = productos.filter(categoria=categoria)
    if estado:
        productos = productos.filter(estado=estado)
    if tipo:
        productos = productos.filter(tipo=tipo)

    context={
        'productos': productos,
    }

    return render(request, 'index/productos.html', context)

@login_required
@require_POST
def guardar_confirmacion_entrega(request):
    form = ConfirmacionEntregaForm(request.POST)
    producto_id = request.POST.get("producto_id")
    canal_id = request.POST.get("canal_id")

    if form.is_valid() and producto_id and canal_id:
        confirmacion = form.save(commit=False)
        confirmacion.creador = request.user
        confirmacion.producto_id = producto_id
        confirmacion.canal_id = canal_id
        confirmacion.save()

        # Marcar producto como no disponible
        producto = Producto.objects.get(id_producto=producto_id)
        producto.disponible = False
        producto.save()

        return JsonResponse({"status": "ok", "mensaje": "Confirmación guardada con éxito"})
    return JsonResponse({"status": "error", "errores": form.errors})

@login_required
def mis_compras(request):
    usuario = request.user

    # Pendientes (entregas no confirmadas)
    pendientes = ConfirmacionEntrega.objects.filter(
        canal__usuarios=usuario,
        concretado=True,
        confirmado=False
    ).distinct()

    # Compras (productos comprados, confirmados y de tipo venta), excluyendo los que eres vendedor
    compras = ConfirmacionEntrega.objects.filter(
        canal__usuarios=usuario,
        confirmado=True,
        producto__tipo='Venta'
    ).exclude(producto__usuario=usuario).distinct()

    # Intercambios (productos intercambiados, confirmados), excluyendo los que eres vendedor
    intercambios = ConfirmacionEntrega.objects.filter(
        canal__usuarios=usuario,
        confirmado=True,
        producto__tipo='Intercambio'
    ).exclude(producto__usuario=usuario).distinct()

    # Mis productos vendidos o intercambiados (como vendedor)
    mis_productos = ConfirmacionEntrega.objects.filter(
        producto__usuario=usuario,
        confirmado=True
    ).distinct()

    reportados = ConfirmacionEntrega.objects.filter(
        canal__usuarios=usuario,
        concretado=False
    )

    return render(request, 'index/mis_compras.html', {
        'pendientes': pendientes,
        'compras': compras,
        'intercambios': intercambios,
        'mis_productos': mis_productos,
        'reportados': reportados
    })
@login_required
def calificar_cliente(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cliente_id = request.POST.get('cliente_id')
        puntaje = request.POST.get('puntaje')
        comentario = request.POST.get('comentario')

        if not producto_id or not cliente_id or not puntaje:
            messages.error(request, "Faltan datos para calificar al cliente.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        try:
            if cliente_id.isdigit():
                cliente = User.objects.get(id=cliente_id)
            producto = Producto.objects.get(id_producto=producto_id)
            cliente = User.objects.get(id=cliente_id)


            # Verificar que no se haya calificado ya
            if CalificacionCliente.objects.filter(producto=producto, vendedor=request.user).exists():
                messages.error(request, "Ya calificaste a este cliente para este producto.")
                return redirect(request.META.get('HTTP_REFERER', 'home'))

            # Guardar calificación
            calificacion = CalificacionCliente(
                cliente=cliente,
                producto=producto,
                vendedor=request.user,
                puntaje=puntaje,
                comentario=comentario
            )
            calificacion.save()
            messages.success(request, "Has calificado al cliente exitosamente.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

        except Producto.DoesNotExist:
            messages.error(request, "Producto no encontrado.")
        except User.DoesNotExist:
            messages.error(request, "Cliente no encontrado.")

    else:
        messages.error(request, "Método no permitido.")

    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
def calificar_vendedor(request):
    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        vendedor_id = request.POST.get('vendedor_id')
        puntaje = request.POST.get('puntaje')
        comentario = request.POST.get('comentario')

        # Verificar que se recibieron todos los datos necesarios
        if not producto_id or not vendedor_id or not puntaje:
            messages.error(request, "Faltan datos para procesar la calificación.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))  # Redirigir de vuelta para mostrar el mensaje

        try:
            # Obtener el producto y vendedor correspondientes
            producto = Producto.objects.get(id_producto=producto_id)
            vendedor = User.objects.get(id=vendedor_id)

            # Verificar que el comprador no esté calificando al vendedor más de una vez por el mismo producto
            if CalificacionVendedor.objects.filter(producto=producto, comprador=request.user).exists():
                messages.error(request, "Ya has calificado este vendedor para este producto.")
                return redirect(request.META.get('HTTP_REFERER', 'home'))

            # Guardar la calificación
            calificacion = CalificacionVendedor(
                vendedor=vendedor,
                producto=producto,
                comprador=request.user,  # El comprador (usuario logueado) deja la calificación
                puntaje=puntaje,
                comentario=comentario
            )
            calificacion.save()
            # Cambiar estado del producto a no disponible
            producto.disponible = False
            producto.save()
            # ✅ Marcar confirmación como confirmada
            confirmacion = ConfirmacionEntrega.objects.filter(producto=producto, canal__usuarios=request.user).first()
            if confirmacion:
                confirmacion.confirmado = True
                confirmacion.save()
                print("✔ Confirmación marcada como confirmada")
            else:
                print("⚠ No se encontró una confirmación para ese producto y usuario.")
            # Mostrar el mensaje de éxito
            messages.success(request, "Gracias por calificar al vendedor.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))  # Redirigir de vuelta para mostrar el mensaje

        except Producto.DoesNotExist:
            messages.error(request, "Producto no encontrado.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))
        except User.DoesNotExist:
            messages.error(request, "Vendedor no encontrado.")
            return redirect(request.META.get('HTTP_REFERER', 'home'))

    messages.error(request, "Método no permitido.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required
@require_POST
def reportar_vendedor(request):
    form = ReporteVendedorForm(request.POST)
    producto_id = request.POST.get('producto_id')
    vendedor_id = request.POST.get('vendedor_id')
    puntaje = request.POST.get('puntaje') 
    if form.is_valid() and producto_id and vendedor_id:
        reporte = form.save(commit=False)
        reporte.producto_id = producto_id
        reporte.vendedor_id = vendedor_id
        reporte.comprador = request.user
        reporte.puntaje = puntaje 
        reporte.save()
        ConfirmacionEntrega.objects.filter(producto_id=producto_id).update(concretado=False)
        messages.success(request, "Gracias por reportar al vendedor.")
        return redirect(request.META.get('HTTP_REFERER', 'home')) 
    else:
        return JsonResponse({'status': 'error', 'errors': form.errors})
    
@login_required
def perfil_publico(request, username):
    # Verificar si el usuario está viendo su propio perfil
    if request.user.username == username:
        return redirect('perfil_usuario')  # Redirigir a su propio perfil (privado)

    # Obtener el perfil del usuario público
    usuario = get_object_or_404(User, username=username)
    perfil = get_object_or_404(Perfil, user=usuario)

    # Obtener los productos del usuario público
    productos = Producto.objects.filter(usuario=usuario)

    opiniones = []

    # Calificaciones
    calificaciones = CalificacionVendedor.objects.filter(vendedor=usuario).select_related('comprador', 'producto')
    for calificacion in calificaciones:
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

    # Reportes
    reportes = ReporteVendedor.objects.filter(vendedor=usuario).select_related('comprador')
    for reporte in reportes:
        perfil_comprador = getattr(reporte.comprador, 'perfil', None)
        foto = perfil_comprador.get_foto_perfil_url() if perfil_comprador else None
        opiniones.append({
            'tipo': 'reporte',
            'usuario': reporte.comprador.username,
            'foto': foto,
            'motivo': reporte.motivo,
            'fecha': reporte.fecha_reporte,
        })

    # Ordenar por fecha descendente
    opiniones.sort(key=lambda x: x['fecha'], reverse=True)

    return render(request, 'index/perfil_publico.html', {
        'perfil': perfil,
        'opiniones': opiniones,
    })

@login_required
def agregar_favorito(request, producto_id):
    producto = get_object_or_404(Producto, id_producto=producto_id)
    perfil = request.user.perfil
    perfil.favoritos.add(producto)
    return redirect('perfil_publico', username=producto.usuario.username)

@login_required
def quitar_favorito(request, producto_id):
    producto = get_object_or_404(Producto, id_producto=producto_id)
    perfil = request.user.perfil
    perfil.favoritos.remove(producto)
    return redirect('perfil_usuario')
@login_required
def favoritos(request):
    favoritos = request.user.perfil.favoritos.all()
    return render(request, 'index/favoritos.html', {'favoritos': favoritos})
@login_required
def toggle_favorito(request, producto_id):
    producto = get_object_or_404(Producto, id_producto=producto_id)
    perfil = request.user.perfil

    if producto in perfil.favoritos.all():
        perfil.favoritos.remove(producto)
    else:
        perfil.favoritos.add(producto)

    # Redirige a la página anterior o a perfil público
    return redirect(request.META.get('HTTP_REFERER', 'perfil_usuario'))

def buscar_productos(request):
    query = request.GET.get('q', '')
    resultados = Producto.objects.filter(nombre__icontains=query, estado_revision='Aceptado')
    return render(request, 'index/resultados_busqueda.html', {'resultados': resultados, 'query': query})
def detalle_producto(request, id):
    producto = get_object_or_404(Producto, id=id)
    return render(request, 'index/detalle_producto.html', {'producto': producto})

@login_required
def editar_confirmacion(request, pk):
    confirmacion = get_object_or_404(ConfirmacionEntrega, pk=pk, creador=request.user)

    if not confirmacion.concretado or confirmacion.confirmado:
        return HttpResponseForbidden("No puedes editar esta confirmación.")

    if request.method == 'POST':
        form = ConfirmacionEntregaForm(request.POST, instance=confirmacion)
        if form.is_valid():
            form.save()
            return redirect('mis_compras')
    else:
        form = ConfirmacionEntregaForm(instance=confirmacion)

    return render(request, 'index/editar_confirmacion.html', {'form': form})

@login_required
@require_POST
def eliminar_confirmacion(request, pk):
    confirmacion = get_object_or_404(ConfirmacionEntrega, pk=pk, creador=request.user)

    producto = confirmacion.producto
    producto.disponible = True
    producto.save()

    if not confirmacion.concretado or confirmacion.confirmado:
        return HttpResponseForbidden("No puedes eliminar esta confirmación.")

    confirmacion.delete()
    return redirect('mis_compras')

@csrf_exempt
def mercadopago_webhook(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mp_service = MercadoPagoService()
            mp_service.procesar_webhook(data)
            return HttpResponse(status=200)
        except Exception as e:
            return HttpResponse(status=400)
    return HttpResponse(status=405)

#Webhook que recibe notificaciones de Mercado Pago
@csrf_exempt
def webhook_mercadopago(request):

    if request.method == "POST":
        try:
            payload = json.loads(request.body.decode('utf-8'))
            print("Webhook recibido:", payload)
            
            # Verificar el tipo de notificación
            if payload.get('type') == 'payment':
                payment_id = payload.get('data', {}).get('id')
                if not payment_id:
                    print("Error: No se recibió payment_id en el webhook")
                    return JsonResponse({"error": "payment_id no encontrado"}, status=400)
                
                # Procesar el pago
                mp_service = MercadoPagoService()
                try:
                    mp_service.procesar_webhook(payload)
                    return JsonResponse({"status": "procesado"}, status=200)
                except Exception as e:
                    print(f"Error al procesar webhook: {str(e)}")
                    return JsonResponse({"error": str(e)}, status=500)
            else:
                print(f"Tipo de webhook no manejado: {payload.get('type')}")
                return JsonResponse({"status": "ignorado"}, status=200)
                
        except json.JSONDecodeError:
            print("Error: JSON inválido en el webhook")
            return JsonResponse({"error": "payload inválido"}, status=400)
        except Exception as e:
            print(f"Error inesperado en webhook: {str(e)}")
            return JsonResponse({"error": str(e)}, status=500)
            
    return HttpResponse(status=405)

@csrf_exempt
def crear_suscripcion_api(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    try:
        data = json.loads(request.body)
        token_tarjeta = data.get('token_tarjeta')
        email = data.get('email')
        membresia_id = data.get('membresia_id')

        if not token_tarjeta:
            return JsonResponse({'error': 'El token de tarjeta es requerido'}, status=400)
        if not (email and membresia_id):
            return JsonResponse({'error': 'Faltan datos requeridos'}, status=400)

        perfil = Perfil.objects.get(user__email=email)
        membresia = Membresia.objects.get(id=membresia_id)

        mp_service = MercadoPagoService()
        respuesta = mp_service.crear_suscripcion(perfil, membresia, token_tarjeta)
        init_point = respuesta.get("sandbox_init_point") or respuesta.get("init_point")
        subscription_id = respuesta.get("id")

        return JsonResponse({
            'success': True,
            'init_point': init_point,
            'suscripcion_id': subscription_id
        })
    except Perfil.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=404)
    except Membresia.DoesNotExist:
        return JsonResponse({'error': 'Membresía no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
   
@csrf_exempt
@login_required
def cancelar_suscripcion_view(request):
    if request.method == "POST":
        try:
            perfil = request.user.perfil
            suscripciones = SuscripcionMercadoPago.objects.filter(perfil=perfil, estado="active")
            mp_service = MercadoPagoService()
            if suscripciones.count() == 0:
                return JsonResponse({"success": False, "error": "No tienes una suscripción activa."}, status=400)
            elif suscripciones.count() > 1:
             
                for suscripcion in suscripciones:
                    mp_service.cancelar_suscripcion(suscripcion)
                return JsonResponse({"success": True, "warning": "Había más de una suscripción activa, todas han sido canceladas."})
            else:
                mp_service.cancelar_suscripcion(suscripciones.first())
                return JsonResponse({"success": True})
        except SuscripcionMercadoPago.DoesNotExist:
            return JsonResponse({"success": False, "error": "No tienes una suscripción activa."}, status=400)
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)}, status=500)
    return JsonResponse({"success": False, "error": "Método no permitido."}, status=405)
   