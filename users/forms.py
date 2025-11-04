from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, Div
from .models import Usuario


class UsuarioCrearForm(UserCreationForm):
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese el nombre'})
    )
    last_name = forms.CharField(
        label='Apellido',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese el apellido'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'dpi', 'codigo_empleado', 'telefono', 'rol', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
            'dpi': forms.TextInput(attrs={'placeholder': '1234567890123'}),
            'codigo_empleado': forms.TextInput(attrs={'placeholder': 'Código de empleado'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+502 1234-5678'}),
        }
        labels = {
            'username': 'Usuario',
            'dpi': 'DPI',
            'codigo_empleado': 'Código de Empleado',
            'telefono': 'Teléfono',
            'rol': 'Rol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='col-md-6 mb-3'),
                Column('email', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('first_name', css_class='col-md-6 mb-3'),
                Column('last_name', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('dpi', css_class='col-md-6 mb-3'),
                Column('codigo_empleado', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('telefono', css_class='col-md-6 mb-3'),
                Column('rol', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('password1', css_class='col-md-6 mb-3'),
                Column('password2', css_class='col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Guardar Usuario', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )

    def clean_dpi(self):
        dpi = self.cleaned_data.get('dpi')
        if dpi and not dpi.isdigit():
            raise forms.ValidationError('El DPI debe contener solo números.')
        if dpi and len(dpi) != 13:
            raise forms.ValidationError('El DPI debe tener exactamente 13 dígitos.')
        return dpi

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        dpi = cleaned_data.get('dpi')
        codigo_empleado = cleaned_data.get('codigo_empleado')

        # Validar que vendedores tengan DPI y código
        if rol == 'vendedor':
            if not dpi:
                self.add_error('dpi', 'Los vendedores deben tener un DPI registrado.')
            if not codigo_empleado:
                self.add_error('codigo_empleado', 'Los vendedores deben tener un código de empleado.')

        return cleaned_data


class UsuarioActualizarForm(forms.ModelForm):
    first_name = forms.CharField(
        label='Nombre',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese el nombre'})
    )
    last_name = forms.CharField(
        label='Apellido',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Ingrese el apellido'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'})
    )

    class Meta:
        model = Usuario
        fields = ['username', 'first_name', 'last_name', 'email', 'dpi', 'codigo_empleado', 'telefono', 'rol', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Nombre de usuario'}),
            'dpi': forms.TextInput(attrs={'placeholder': '1234567890123'}),
            'codigo_empleado': forms.TextInput(attrs={'placeholder': 'Código de empleado'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+502 1234-5678'}),
        }
        labels = {
            'username': 'Usuario',
            'dpi': 'DPI',
            'codigo_empleado': 'Código de Empleado',
            'telefono': 'Teléfono',
            'rol': 'Rol',
            'is_active': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('username', css_class='col-md-6 mb-3'),
                Column('email', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('first_name', css_class='col-md-6 mb-3'),
                Column('last_name', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('dpi', css_class='col-md-6 mb-3'),
                Column('codigo_empleado', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('telefono', css_class='col-md-6 mb-3'),
                Column('rol', css_class='col-md-6 mb-3'),
            ),
            Row(
                Column('is_active', css_class='col-md-6 mb-3'),
            ),
            Div(
                Submit('submit', 'Actualizar Usuario', css_class='btn btn-primary'),
                css_class='text-end'
            )
        )

    def clean_dpi(self):
        dpi = self.cleaned_data.get('dpi')
        if dpi and not dpi.isdigit():
            raise forms.ValidationError('El DPI debe contener solo números.')
        if dpi and len(dpi) != 13:
            raise forms.ValidationError('El DPI debe tener exactamente 13 dígitos.')
        return dpi

    def clean(self):
        cleaned_data = super().clean()
        rol = cleaned_data.get('rol')
        dpi = cleaned_data.get('dpi')
        codigo_empleado = cleaned_data.get('codigo_empleado')

        # Validar que vendedores tengan DPI y código
        if rol == 'vendedor':
            if not dpi:
                self.add_error('dpi', 'Los vendedores deben tener un DPI registrado.')
            if not codigo_empleado:
                self.add_error('codigo_empleado', 'Los vendedores deben tener un código de empleado.')

        return cleaned_data


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Usuario',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre de usuario',
            'autofocus': True
        })
    )
    password = forms.CharField(
        label='Contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Contraseña'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_show_labels = True