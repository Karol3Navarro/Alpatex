from django import forms
from .models import ConfirmacionEntrega

# Formulario para enviar mensajes en un canal
# Utiliza CharField con un widget Textarea para permitir la entrada de texto en varias líneas
class FormMensajes(forms.Form):
    mensaje = forms.CharField(widget=forms.Textarea(attrs={
        "class": "formulario_ms",
        "placeholder": "Escribe tu mensaje"
    }))

# Formulario para confirmar la entrega de un pedido
# Utiliza ModelForm para generar automáticamente los campos basados en el modelo ConfirmacionEntrega
class ConfirmacionEntregaForm(forms.ModelForm):
    class Meta:
        model = ConfirmacionEntrega
        fields = ['lugar', 'fecha', 'hora']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }