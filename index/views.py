from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Producto, Perfil, CalificacionProducto, CalificacionVendedor
from .Forms import CustomUserCreationForm, PerfilForm, ProductoForm, CalificacionProductoForm
from django.contrib import messages
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Avg
from admin_alpatex.models import Membresia
from django.db.models import F
from django.contrib.messages import get_messages
from Dm.models import ConfirmacionEntrega
from Dm.forms import ConfirmacionEntregaForm
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse

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


    for producto in productos:
        calificaciones = CalificacionProducto.objects.filter(producto=producto)
        if calificaciones.exists():
            promedio = calificaciones.aggregate(Avg('puntaje'))['puntaje__avg']
            producto.calificacion_promedio = round(promedio, 1)
        else:
            producto.calificacion_promedio = "Sin calificaciones"

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

    if request.method == 'POST':
        form = CalificacionProductoForm(request.POST)
        if form.is_valid():
            calificacion = form.save(commit=False)
            calificacion.producto = producto
            calificacion.usuario = request.user
            calificacion.save()
            return redirect('ver_producto', id_producto=producto.id_producto)
    else:
        form = CalificacionProductoForm()

    # Obtener calificaciones con información de perfil segura
    calificaciones = []
    for calificacion in CalificacionProducto.objects.filter(producto=producto):
        try:
            perfil = calificacion.usuario.perfil
            foto_perfil = perfil.foto_perfil.url if perfil.foto_perfil else None
        except (Perfil.DoesNotExist, AttributeError):
            foto_perfil = None
        
        calificaciones.append({
            'calificacion': calificacion,
            'foto_perfil': foto_perfil
        })

    context = {
        'producto': producto,
        'form': form,
        'calificaciones': calificaciones,
    }
    return render(request, 'index/ver_producto.html', context)

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('index')  # Redirige a la página principal
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'index/registro.html', {'form': form})

def registro(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        
        if form.is_valid():
            user = form.save(commit=False)
            user.first_name = form.cleaned_data['nombre_completo']
            user.email = form.cleaned_data['email']
            user.save()
            rut = form.cleaned_data['rut']
            direccion = form.cleaned_data['direccion']
            Perfil.objects.create(user=user, rut=rut, direccion=direccion)

            messages.success(request, '¡Cuenta creada exitosamente!')
            return redirect('index')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CustomUserCreationForm()

    return render(request, 'index/registro.html', {'form': form})



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
    perfil = Perfil.objects.get(user=request.user)
    membresias = Membresia.objects.all()

    if request.method == 'POST':
        nueva_id = request.POST.get('membresia_id')
        if nueva_id:
            nueva_membresia = Membresia.objects.get(id=nueva_id)
            perfil.membresia = nueva_membresia
            perfil.save()
            return redirect('ver_membresia_usuario')

    return render(request, 'index/ver_membresia.html', {
        'perfil': perfil,
        'membresias': membresias,
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

    return render(request, 'index/mis_compras.html', {
        'pendientes': pendientes,
        'compras': compras,
        'intercambios': intercambios,
        'mis_productos': mis_productos,
    })

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