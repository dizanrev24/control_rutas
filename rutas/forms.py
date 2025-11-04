"""
Formularios para el módulo de rutas.
Maneja la creación de rutas y asignación de clientes con orden de visita.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Submit, HTML
from .models import Ruta, RutaDetalle
from clientes.models import Cliente


class RutaForm(forms.ModelForm):
    """
    Formulario para crear y editar rutas.
    """
    class Meta:
        model = Ruta
        fields = ['nombre', 'descripcion', 'activo']
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 3}),
        }
        labels = {
            'nombre': 'Nombre de la Ruta',
            'descripcion': 'Descripción',
            'activo': 'Activo',
        }
        help_texts = {
            'nombre': 'Nombre identificativo de la ruta (ej: Zona Norte)',
            'activo': 'Desmarcar para desactivar la ruta sin eliminarla',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field('nombre'),
            Field('descripcion'),
            Field('activo'),
            HTML('<hr>'),
            Row(
                Column(
                    Submit('submit', 'Guardar Ruta', css_class='btn btn-primary btn-lg w-100'),
                    css_class='col-md-12'
                ),
            ),
        )


class RutaDetalleForm(forms.ModelForm):
    """
    Formulario para agregar clientes a una ruta con orden de visita.
    """
    class Meta:
        model = RutaDetalle
        fields = ['cliente', 'orden_visita']
        widgets = {
            'orden_visita': forms.NumberInput(attrs={'min': 1, 'step': 1}),
        }
        labels = {
            'cliente': 'Cliente',
            'orden_visita': 'Orden de Visita',
        }
        help_texts = {
            'orden_visita': 'Número que indica el orden en que se visitará este cliente',
        }
    
    def __init__(self, *args, **kwargs):
        self.ruta = kwargs.pop('ruta', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo clientes activos que NO estén ya en esta ruta
        if self.ruta:
            clientes_en_ruta = RutaDetalle.objects.filter(ruta=self.ruta).values_list('cliente_id', flat=True)
            self.fields['cliente'].queryset = Cliente.objects.filter(
                activo=True
            ).exclude(id__in=clientes_en_ruta)
        else:
            self.fields['cliente'].queryset = Cliente.objects.filter(activo=True)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('cliente', css_class='col-md-8'),
                Column('orden_visita', css_class='col-md-4'),
            ),
            HTML('<hr>'),
            Row(
                Column(
                    Submit('submit', 'Agregar Cliente', css_class='btn btn-success w-100'),
                    css_class='col-md-12'
                ),
            ),
        )
    
    def clean(self):
        cleaned_data = super().clean()
        cliente = cleaned_data.get('cliente')
        orden_visita = cleaned_data.get('orden_visita')
        
        if self.ruta and cliente and orden_visita:
            # Verificar que el orden no esté duplicado en esta ruta
            existe_orden = RutaDetalle.objects.filter(
                ruta=self.ruta,
                orden_visita=orden_visita
            ).exclude(pk=self.instance.pk if self.instance.pk else None).exists()
            
            if existe_orden:
                raise forms.ValidationError(
                    f'Ya existe un cliente con el orden {orden_visita} en esta ruta.'
                )
        
        return cleaned_data


class RutaFiltroForm(forms.Form):
    """
    Formulario para filtrar rutas en la lista.
    """
    buscar = forms.CharField(
        required=False,
        label='Buscar',
        widget=forms.TextInput(attrs={
            'placeholder': 'Buscar por nombre o descripción...',
            'class': 'form-control'
        })
    )
    
    activo = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[
            ('', 'Todas'),
            ('true', 'Activas'),
            ('false', 'Inactivas'),
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
                Column('activo', css_class='col-md-3'),
            ),
        )
