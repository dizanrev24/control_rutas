"""
Formularios para el módulo de pedidos.
Maneja la creación de pedidos (sin descuento de stock) desde el vendedor durante la visita.
"""
from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Field
from .models import Pedido, DetallePedido
from productos.models import Producto


class PedidoForm(forms.ModelForm):
    """
    Formulario para crear un pedido durante la visita.
    Los pedidos NO descargan stock del camión.
    """
    class Meta:
        model = Pedido
        fields = ['observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'observaciones': 'Observaciones del pedido',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('observaciones', placeholder='Observaciones adicionales sobre el pedido (opcional)'),
        )


class DetallePedidoForm(forms.ModelForm):
    """
    Formulario para cada línea de detalle del pedido.
    Permite seleccionar cualquier producto activo del catálogo.
    """
    class Meta:
        model = DetallePedido
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'cantidad': forms.NumberInput(attrs={'min': 1, 'step': 1}),
            'precio_unitario': forms.NumberInput(attrs={'min': 0.01, 'step': 0.01}),
        }
        labels = {
            'producto': 'Producto',
            'cantidad': 'Cantidad',
            'precio_unitario': 'Precio Unitario',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Mostrar todos los productos activos (sin restricción de stock)
        self.fields['producto'].queryset = Producto.objects.filter(activo=True)


# Formset para manejar múltiples líneas de detalle
DetallePedidoFormSet = inlineformset_factory(
    Pedido,
    DetallePedido,
    form=DetallePedidoForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
