from django import forms
from .models import Membresia

class MembresiaForm(forms.ModelForm):
    class Meta:
        model = Membresia
        fields = '__all__'
