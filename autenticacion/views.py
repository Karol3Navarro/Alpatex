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
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            correo = form.cleaned_data['email']
            usuarios = User.objects.filter(email=correo)
            if usuarios.exists():
                for user in usuarios:
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
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            clave_cambiada_exito = False
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    clave_cambiada_exito = True
                else:
                    # Aquí puedes reemplazar o limpiar errores de validación
                    # Por ejemplo, sobreescribir errores de new_password1:
                    errores_personalizados = []
                    for error in form.errors.get('new_password1', []):
                        # Por ejemplo, ignorar mensajes de "too short" y "too common"
                        if "too short" in error or "too common" in error:
                            continue
                        else:
                            errores_personalizados.append(error)
                    form.errors['new_password1'] = errores_personalizados
            else:
                form = SetPasswordForm(user)
            return render(request, 'autenticacion/reset_clave.html', {'form': form, 'clave_cambiada_exito': clave_cambiada_exito})
        else:
            return redirect('autenticacion:error_token')
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return redirect('autenticacion:error_token')



def clave_cambiada(request):
    return render(request, 'autenticacion/clave_cambiada.html')
def clave_enviada(request):
    return render(request, 'autenticacion/clave_enviada.html') 
def correo_modal(request):
    return render(request, 'autenticacion/correo_modal.html')
