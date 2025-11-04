"""
Formularios para el módulo de productos.
Maneja la creación y edición de productos del catálogo.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Submit, HTML
from .models import Producto


class ProductoForm(forms.ModelForm):
    """
    Formulario para crear y editar productos.
    """
    class Meta:
        model = Producto
        fields = [
            'nombre',
            'descripcion',
            'categoria',
            'precio_compra',
            'precio_venta',
            'estado',
        ]
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
            'precio_compra': forms.NumberInput(attrs={'min': 0.01, 'step': 0.01}),
            'precio_venta': forms.NumberInput(attrs={'min': 0.01, 'step': 0.01}),
        }
        labels = {
            'nombre': 'Nombre del Producto',
            'descripcion': 'Descripción',
            'categoria': 'Categoría',
            'precio_compra': 'Precio de Compra',
            'precio_venta': 'Precio de Venta',
            'estado': 'Estado',
        }
        help_texts = {
            'precio_compra': 'Precio al que se compra el producto',
            'precio_venta': 'Precio al que se vende el producto',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('nombre', css_class='form-group col-md-12'),
            ),
            Row(
                Column('categoria', css_class='form-group col-md-12'),
            ),
            Row(
                Column('precio_compra', css_class='form-group col-md-6'),
                Column('precio_venta', css_class='form-group col-md-6'),
            ),
            Field('descripcion'),
            Field('estado'),
            HTML('<hr>'),
            Row(
                Column(
                    Submit('submit', 'Guardar Producto', css_class='btn btn-primary btn-lg w-100'),
                    css_class='col-md-12'
                ),
            ),
        )


class ProductoFiltroForm(forms.Form):
    """
    Formulario para filtrar productos en la lista.
    """
    buscar = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre o categoría...',
            'class': 'form-control'
        })
    )
    
    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[
            ('', 'Todos'),
            ('activo', 'Activos'),
            ('inactivo', 'Inactivos'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Row(
                Column('buscar', css_class='col-md-9'),
                Column('estado', css_class='col-md-3'),
            ),
        )
