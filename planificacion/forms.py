from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from .models import Planificacion, DetallePlanificacion
from clientes.models import Cliente
from rutas.models import RutaDetalle


class IniciarVisitaForm(forms.ModelForm):
    """
    Formulario para iniciar una visita (captura ubicación y foto)
    """
    class Meta:
        model = DetallePlanificacion
        fields = ['latitud', 'longitud', 'fotografia_referencia', 'observaciones']
        widgets = {
            'observaciones': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones opcionales...'}),
            'latitud': forms.HiddenInput(),
            'longitud': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            'latitud',
            'longitud',
            Row(
                Column('fotografia_referencia', css_class='col-md-12 mb-3'),
            ),
            Row(
                Column('observaciones', css_class='col-md-12 mb-3'),
            ),
            Div(
                Submit('submit', 'Iniciar Visita', css_class='btn btn-success'),
                css_class='text-end'
            )
        )


class FinalizarVisitaForm(forms.Form):
    """
    Formulario simple para finalizar visita
    """
    observaciones_cierre = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Observaciones al finalizar visita...'}),
        label='Observaciones de Cierre'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'observaciones_cierre',
            Div(
                Submit('submit', 'Finalizar Visita', css_class='btn btn-danger'),
                css_class='text-end'
            )
        )


class ClienteNuevoVendedorForm(forms.ModelForm):
    """
    Formulario simplificado para que vendedor cree cliente nuevo en el día
    """
    class Meta:
        model = Cliente
        fields = ['nit', 'nombre', 'nombre_contacto', 'telefono', 'direccion', 'referencia_ubicacion', 'latitud', 'longitud']
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 2}),
            'referencia_ubicacion': forms.Textarea(attrs={'rows': 2}),
            'latitud': forms.HiddenInput(),
            'longitud': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('nit', css_class='col-md-6 mb-3'),
                Column('nombre', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('nombre_contacto', css_class='col-md-6 mb-3'),
                Column('telefono', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('direccion', css_class='col-md-12 mb-3'),
            ),
            Row(
                Column('referencia_ubicacion', css_class='col-md-12 mb-3'),
            ),
            'latitud',
            'longitud',
            Div(
                Submit('submit', 'Registrar Cliente Nuevo', css_class='btn btn-success'),
                css_class='text-end'
            )
        )


class MarcarNoVisitadoForm(forms.Form):
    """
    Formulario para marcar un cliente como no visitado o cerrado
    """
    MOTIVO_CHOICES = [
        ('no_visitado', 'No Visitado'),
        ('cerrado', 'Negocio Cerrado'),
    ]
    
    motivo = forms.ChoiceField(
        choices=MOTIVO_CHOICES,
        label='Motivo',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    observaciones = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Explique el motivo...'}),
        label='Observaciones'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'motivo',
            'observaciones',
            Div(
                Submit('submit', 'Guardar', css_class='btn btn-warning'),
                css_class='text-end'
            )
        )
