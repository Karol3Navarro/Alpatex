from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Producto,Perfil
from .Forms import CustomUserCreationForm, PerfilForm
from django.contrib import messages


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

        # Intentamos autenticar al usuario con el username y password
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Si el usuario es válido, lo logueamos
            login(request, user)
            return redirect('home')  # Redirige a la página inicio después del login
        else:
            # Si el login falla, podemos mostrar un mensaje de error
            error_message = "Credenciales incorrectas, por favor intenta nuevamente."
            return render(request, 'index/index.html', {'error_message': error_message})

    return render(request, 'index/index.html')  # Muestra el formulario de login

def home(request):
    usuarios = User.objects.all()
    productos = Producto.objects.all()  # Obtener todos los productos
    context = {"usuarios": usuarios, "productos": productos}  # Pasar la variable 'productos'
    return render(request, 'index/home.html', context)

def producto_add(request):
    if request.method != "POST":
        # Si no es un POST, mostramos el formulario vacío
        productos = Producto.objects.all()
        context = {"productos": productos}
        return render(request, 'index/producto_add.html', context)
    else:
        # Si es un POST, verificamos que el nombre no esté vacío
        nombre = request.POST.get("producto")  # Usamos .get() para obtener el valor
        
        if not nombre:  # Verificamos que el campo 'producto' no esté vacío
            context = {'mensaje': "El nombre del producto es obligatorio."}
            return render(request, 'index/producto_add.html', context)
        
        # Crear el producto y asignar el usuario autenticado
        producto = Producto.objects.create(
            nombre=nombre,
            usuario=request.user  # Asignamos el usuario autenticado
        )

        # Guardamos el producto
        producto.save()

        # Enviamos un mensaje de éxito
        context = {'mensaje': "Producto creado con éxito!"}
        return render(request, 'index/producto_add.html', context)

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
