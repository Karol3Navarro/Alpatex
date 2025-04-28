from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Producto,Perfil
from .Forms import CustomUserCreationForm, PerfilForm, ProductoForm
from django.contrib import messages
import json
from django.core.serializers.json import DjangoJSONEncoder

def map(request):
    productos = Producto.objects.select_related('usuario').all()
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
            return render(request, 'index/index.html', {'error_message': error_message})

    return render(request, 'index/index.html')  

def home(request):
    usuarios = User.objects.all()
    productos = Producto.objects.all()  # Obtener todos los productos
    context = {"usuarios": usuarios, "productos": productos}  # Pasar la variable 'productos'
    return render(request, 'index/home.html', context)



def ver_producto(request, id_producto):
    producto = get_object_or_404(Producto, id_producto=id_producto)
    return render(request, 'index/ver_producto.html', {'producto': producto})

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
    return render(request, 'index/productos_perf.html', {'productos': productos, 'mensaje': mensaje})


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
            return redirect('productos_perf')  # O puedes redirigir a producto_add_perf si prefieres
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