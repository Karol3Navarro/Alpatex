from django import forms
from .models import ConfirmacionEntrega

class FormMensajes(forms.Form):
    mensaje = forms.CharField(widget=forms.Textarea(attrs={
        "class": "formulario_ms",
        "placeholder": "Escribe tu mensaje"
    }))

class ConfirmacionEntregaForm(forms.ModelForm):
    class Meta:
        model = ConfirmacionEntrega
        fields = ['lugar', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }