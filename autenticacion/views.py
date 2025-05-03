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

import os
def cambiar_clave(request):
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
                    html_message = render_to_string("autenticacion/email_recuperar_clave.html", {
                        'reset_link': reset_link,
                    })
                    email = EmailMessage(
                        subject="Recuperación de clave",
                        body=html_message,
                        from_email=None,
                        to=[correo],
                    )
                    email.content_subtype = "html"
                    email.send()
            # Redirigimos a una vista temporal que muestra el modal
            return redirect('autenticacion:correo_modal')
    else:
        form = PasswordResetForm()
    return render(request, 'autenticacion/cambiar_clave.html', {'form': form})


def reset_clave(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64)
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            if request.method == 'POST':
                form = SetPasswordForm(user, request.POST)
                if form.is_valid():
                    form.save()
                    return redirect('autenticacion:clave_cambiada')  # Redirect to confirmation page
            else:
                form = SetPasswordForm(user)
            return render(request, 'autenticacion/reset_clave.html', {'form': form})
        else:
            return redirect('autenticacion:error_token')  # Token error handling
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        return redirect('autenticacion:error_token')  # Token error handling

def clave_cambiada(request):
    return render(request, 'autenticacion/clave_cambiada.html')
def clave_enviada(request):
    return render(request, 'autenticacion/clave_enviada.html') 
def correo_modal(request):
    return render(request, 'autenticacion/correo_modal.html')
