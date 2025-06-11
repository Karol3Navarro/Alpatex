from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Perfil, Producto, ReporteVendedor, ReporteUsuario


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
        fields =  ['nombre', 'estado',  'tipo', 'precio', 'direccion', 'categoria', 'imagen']  

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['imagen'].widget.attrs.update({'id': 'id_imagen'})
        self.fields['precio'].widget.attrs.update({'id': 'id_precio'})
        
        if 'direccion' in self.initial:
            self.fields['direccion'].initial = self.initial['direccion']

class ReporteVendedorForm(forms.ModelForm):
    class Meta:
        model = ReporteVendedor
        fields = ['motivo']
class ReporteusuarioForm(forms.ModelForm):
    class Meta:
        model = ReporteUsuario
        fields = ['motivo']