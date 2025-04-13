from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
# Create your views here.


def logout(request):
    context={}
    return render(request, 'index/index.html', context)

@login_required
def menu(request):
    request.session["usuario"]="cgarcia"
    usuario=request.session["usuario"]
    context={'usuario':usuario}
    return render(request, 'index/inicio.html', context)


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
    context = {}
    return render(request, 'index/home.html', context)