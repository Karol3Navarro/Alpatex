from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes
from django.conf import settings
from django.core.mail import EmailMessage
from email.mime.image import MIMEImage
import os


def cambiar_clave(request):
    error_email = False
    if request.method == 'POST':
        # Utiliza PasswordResetForm para manejar la validación del correo electrónico
        # y la generación del token de restablecimiento de contraseña
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            # Obtiene el correo electrónico del formulario
            # y busca usuarios con ese correo en la base de datos
            correo = form.cleaned_data['email']
            usuarios = User.objects.filter(email=correo)
            # Si existen usuarios con ese correo, genera el enlace de restablecimiento
            if usuarios.exists():
                for user in usuarios:
                    # Genera el UID y el token para el usuario
                    # Utiliza urlsafe_base64_encode para codificar el ID del usuario
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    token = default_token_generator.make_token(user)
                    reset_link = request.build_absolute_uri(f"/autenticacion/reset-clave/{uid}/{token}/")

                    context = {
                        'reset_link': reset_link,
                    }

                    html_content = render_to_string("autenticacion/email_recuperar_clave.html", context)

                    email = EmailMessage(
                        subject="Recuperación de clave",
                        body=html_content,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        to=[correo],
                    )
                    email.content_subtype = "html"

                    logo_path = os.path.join(settings.BASE_DIR, 'index', 'static', 'img', 'alpatex-v2-tipografía.png')
                    with open(logo_path, 'rb') as img:
                        mime_image = MIMEImage(img.read())
                        mime_image.add_header('Content-ID', '<logo_alpatex>')
                        mime_image.add_header('Content-Disposition', 'inline', filename='alpatex-v2-tipografía.png')
                        email.attach(mime_image)

                    email.send()

                return redirect('autenticacion:correo_modal')
            else:
                error_email = True  # Activa el flag

    else:
        form = PasswordResetForm()

    return render(request, 'autenticacion/cambiar_clave.html', {'form': form, 'error_email': error_email})


def reset_clave(request, uidb64, token):
    try:
        # Decodifica el UID usando urlsafe_base64_decode
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
        # Verifica el token usando default_token_generator
        if default_token_generator.check_token(user, token):
            clave_cambiada_exito = False
            # Si el token es válido, muestra el formulario para cambiar la contraseña
            # Utiliza SetPasswordForm para manejar el cambio de contraseña
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    clave_cambiada_exito = True
                else:
                    # Si el formulario no es válido, filtra los errores personalizados
                    # para evitar mostrar errores de longitud o comunes
                    errores_personalizados = []
                    for error in form.errors.get('new_password1', []):                        
                        if "too short" in error or "too common" in error:
                            continue
                        else:
                            errores_personalizados.append(error)
                    form.errors['new_password1'] = errores_personalizados
            # Si el método no es POST, muestra el formulario vacío
            else:
                form = SetPasswordForm(user)
            return render(request, 'autenticacion/reset_clave.html', {'form': form, 'clave_cambiada_exito': clave_cambiada_exito})
        # Si el token no es válido, redirige a una página de error
        else:
            return redirect('autenticacion:error_token')
    # Maneja errores de decodificación, tipo, valor y si el usuario no existe
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return redirect('autenticacion:error_token')

#vistas que muestran paginas especificas de autenticación o recuperación de contraseña
def clave_cambiada(request):
    return render(request, 'autenticacion/clave_cambiada.html')
def clave_enviada(request):
    return render(request, 'autenticacion/clave_enviada.html') 
def correo_modal(request):
    return render(request, 'autenticacion/correo_modal.html')
