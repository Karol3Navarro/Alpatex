from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Producto
# Create your views here.


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