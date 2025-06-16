from django import forms
from .models import Membresia

# Formulario para crear o editar una membresía
# Utiliza ModelForm para generar automáticamente los campos basados en el modelo Membresia
class MembresiaForm(forms.ModelForm):
    class Meta:
        model = Membresia
        fields = '__all__'
