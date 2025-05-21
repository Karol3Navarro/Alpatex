from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Perfil, Producto, CalificacionProducto, ReporteVendedor

#Calificacion de Producto
class CalificacionProductoForm(forms.ModelForm):
    class Meta:
        model = CalificacionProducto
        fields = ['puntaje', 'comentario']
        widgets = {
            'puntaje': forms.HiddenInput(),
            'comentario': forms.Textarea(attrs={'rows': 3}),
        }

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
        self.fields['password1'].help_text = "La clave debe tener al menos 8 caracteres, no puede ser completamente numérica ni común."
        self.fields['password2'].help_text = "Confirma la misma clave que antes."

        self.fields['username'].label = "Nombre de usuario"
        self.fields['password1'].label = "Clave"
        self.fields['password2'].label = "Confirmar clave"

        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control'
            })

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Este correo electrónico ya está registrado. Por favor, utiliza otro.")
        return email

    def clean_rut(self):
        rut = self.cleaned_data.get('rut')
        if Perfil.objects.filter(rut=rut).exists():  
            raise ValidationError("El RUT ingresado ya está registrado.")
        return rut

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['nombre_completo']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            perfil, creado = Perfil.objects.get_or_create(user=user)
            perfil.rut = self.cleaned_data['rut']
            perfil.direccion = self.cleaned_data['direccion']
            perfil.save()
        return user

class PerfilForm(forms.ModelForm):
    email = forms.EmailField(label="Correo electrónico")
    direccion = forms.CharField(label="Dirección")
    genero = forms.ChoiceField(label="Género", choices=Perfil.GENERO_CHOICES)
    foto_perfil = forms.ImageField(label="Foto de perfil", required=False)

    class Meta:
        model = Perfil
        fields = ['direccion', 'genero', 'foto_perfil']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)  
        super().__init__(*args, **kwargs)

        if user:
            self.fields['email'].initial = user.email

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(id=self.instance.user.id).exists():
            raise ValidationError("Este correo electrónico ya está registrado con otro usuario.")
        return email

    def save(self, user, commit=True):
        perfil = super().save(commit=False)
        user.email = self.cleaned_data['email']
        
        # Si no se subió una nueva imagen y no hay una imagen existente, usar la imagen por defecto
        if not self.cleaned_data.get('foto_perfil') and not perfil.foto_perfil:
            perfil.foto_perfil = 'perfil_images/user_defecto.PNG'
            
        if commit:
            user.save() 
            perfil.save()  
        return perfil
    
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields =  ['nombre', 'estado',  'tipo', 'direccion', 'categoria', 'imagen']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if 'direccion' in self.initial:
            self.fields['direccion'].initial = self.initial['direccion']

class ReporteVendedorForm(forms.ModelForm):
    class Meta:
        model = ReporteVendedor
        fields = ['motivo']