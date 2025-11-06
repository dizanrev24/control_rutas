"""
Formularios para el módulo de ventas.
Maneja la creación de ventas y sus detalles desde el vendedor durante la visita.
"""
from django import forms
from django.forms import inlineformset_factory
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, HTML, Submit
from .models import Venta, DetalleVenta
from productos.models import Producto


class VentaForm(forms.ModelForm):
    """
    Formulario para crear una venta durante la visita.
    """
    class Meta:
        model = Venta
        fields = ['observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'observaciones': 'Observaciones de la venta',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Field('observaciones', placeholder='Observaciones adicionales sobre la venta (opcional)'),
        )


class DetalleVentaForm(forms.ModelForm):
    """
    Formulario para cada línea de detalle de la venta.
    Valida que haya stock disponible en el camión.
    """
    # Forzar cantidades enteras en el formulario aunque el modelo use Decimal
    cantidad = forms.IntegerField(min_value=1, label='Cantidad', widget=forms.NumberInput(attrs={'min': 1, 'step': 1}))
    class Meta:
        model = DetalleVenta
        fields = ['producto', 'cantidad', 'precio_unitario']
        widgets = {
            'precio_unitario': forms.NumberInput(attrs={'min': 0.01, 'step': 0.01}),
        }
        labels = {
            'producto': 'Producto',
            'cantidad': 'Cantidad',
            'precio_unitario': 'Precio Unitario',
        }
    
    def __init__(self, *args, **kwargs):
        self.carga_camion = kwargs.pop('carga_camion', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar productos disponibles en el camión con stock
        if self.carga_camion:
            productos_disponibles = self.carga_camion.detalles.filter(
                cantidad_actual__gt=0
            ).values_list('producto_id', flat=True)
            self.fields['producto'].queryset = Producto.objects.filter(
                id__in=productos_disponibles,
                estado='activo'
            )
        else:
            self.fields['producto'].queryset = Producto.objects.none()
    
    def clean(self):
        cleaned_data = super().clean()
        producto = cleaned_data.get('producto')
        cantidad = cleaned_data.get('cantidad')
        
        if producto and cantidad and self.carga_camion:
            # Validar que la cantidad sea entera positiva
            try:
                if int(cantidad) != cantidad or cantidad < 1:
                    raise forms.ValidationError('La cantidad debe ser un número entero positivo.')
            except Exception:
                raise forms.ValidationError('La cantidad debe ser un número entero positivo.')

            # Verificar stock disponible en el camión
            try:
                detalle_carga = self.carga_camion.detalles.get(producto=producto)
                if cantidad > detalle_carga.cantidad_actual:
                    raise forms.ValidationError(
                        f'Stock insuficiente para {producto.nombre}. '
                        f'Disponible: {int(detalle_carga.cantidad_actual)}'
                    )
            except:
                raise forms.ValidationError(
                    f'El producto {producto.nombre} no está en el camión.'
                )
        
        return cleaned_data


# Formset para manejar múltiples líneas de detalle
DetalleVentaFormSet = inlineformset_factory(
    Venta,
    DetalleVenta,
    form=DetalleVentaForm,
    extra=0,
    can_delete=True,
    min_num=1,
    validate_min=True,
)
