from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    nombre_completo = forms.CharField(max_length=100, label="Nombre completo")
    email = forms.EmailField(label="Correo electrónico")
    rut = forms.CharField(max_length=12, label="RUT")
    direccion = forms.CharField(max_length=255, label="Dirección")

    class Meta:
        model = User
        fields = ['username', 'nombre_completo', 'rut', 'direccion', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        
        self.fields['username'].help_text = "Requerido. Máximo 150 caracteres. Solo letras, dígitos y @/./+/-/_."
        self.fields['nombre_completo'].help_text = "Escribe tu nombre completo."
        self.fields['email'].help_text = "Introduce una dirección de correo electrónico válida."
        self.fields['password1'].help_text = "La contraseña debe tener al menos 8 caracteres, no puede ser completamente numérica, ni común."
        self.fields['password2'].help_text = "Confirma la misma contraseña que antes."

    
        self.fields['username'].label = "Nombre de usuario"
        self.fields['password1'].label = "Contraseña"
        self.fields['password2'].label = "Confirmar contraseña"

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado. Por favor, utiliza otro.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre_completo']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
