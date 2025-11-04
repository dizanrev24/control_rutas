from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div
from .models import Cliente


class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar clientes
    """
    class Meta:
        model = Cliente
        fields = [
            'nit', 'nombre', 'nombre_contacto', 'correo', 'telefono',
            'direccion', 'referencia_ubicacion', 'latitud', 'longitud',
            'fotografia_referencia', 'activo'
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'referencia_ubicacion': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
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
                Column('correo', css_class='col-md-12 mb-3'),
            ),
            Row(
                Column('direccion', css_class='col-md-12 mb-3'),
            ),
            Row(
                Column('referencia_ubicacion', css_class='col-md-12 mb-3'),
            ),
            Row(
                Column('latitud', css_class='col-md-6 mb-3'),
                Column('longitud', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('fotografia_referencia', css_class='col-md-6 mb-3'),
                Column('activo', css_class='col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Guardar Cliente', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )


class ClienteVendedorForm(forms.ModelForm):
    """
    Formulario simplificado para que vendedores creen clientes nuevos
    """
    class Meta:
        model = Cliente
        fields = [
            'nit', 'nombre', 'nombre_contacto', 'telefono',
            'direccion', 'referencia_ubicacion', 'latitud', 'longitud'
        ]
        widgets = {
            'direccion': forms.Textarea(attrs={'rows': 3}),
            'referencia_ubicacion': forms.Textarea(attrs={'rows': 2}),
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
            Row(
                Column('latitud', css_class='col-md-6 mb-3'),
                Column('longitud', css_class='col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Registrar Cliente', css_class='btn btn-success'),
                css_class='text-end'
            )
        )


class ClienteFiltroForm(forms.Form):
    """
    Formulario para filtrar clientes
    """
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Buscar por nombre o NIT...'})
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('1', 'Activos'), ('0', 'Inactivos')]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Row(
                Column('buscar', css_class='col-md-8'),
                Column('activo', css_class='col-md-4'),
            )
        )
