from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
# Create your views here.

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