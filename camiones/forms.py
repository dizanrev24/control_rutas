"""
Formularios para el módulo de camiones.
"""
from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Field, HTML
from .models import Camion, AsignacionCamionRuta, CargaCamion, CargaCamionDetalle, CuadreDiario, CuadreDiarioDetalle
from productos.models import Producto
from rutas.models import Ruta


class CamionForm(forms.ModelForm):
    """
    Formulario para crear y editar camiones.
    """
    class Meta:
        model = Camion
        fields = ['placa', 'marca', 'modelo', 'año', 'capacidad_carga', 'activo']
        widgets = {
            'placa': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: P-123ABC',
                'style': 'text-transform: uppercase;'
            }),
            'marca': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Toyota'
            }),
            'modelo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Hilux'
            }),
            'año': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '2024',
                'min': 1990,
                'max': 2030
            }),
            'capacidad_carga': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '1000.00',
                'step': '0.01'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('placa', css_class='form-group col-md-6 mb-3'),
                Column('marca', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('modelo', css_class='form-group col-md-6 mb-3'),
                Column('año', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('capacidad_carga', css_class='form-group col-md-6 mb-3'),
                Column('activo', css_class='form-group col-md-6 mb-3'),
            ),
        )
    
    def clean_placa(self):
        placa = self.cleaned_data.get('placa')
        if placa:
            placa = placa.strip().upper()
        return placa


class CamionFiltroForm(forms.Form):
    """
    Formulario para filtrar camiones.
    """
    buscar = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por placa, marca o modelo...'
        })
    )
    activo = forms.ChoiceField(
        required=False,
        choices=[('', 'Todos'), ('true', 'Activos'), ('false', 'Inactivos')],
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class AsignacionCamionRutaForm(forms.ModelForm):
    """
    Formulario para asignar camión a ruta.
    """
    class Meta:
        model = AsignacionCamionRuta
        fields = ['camion', 'ruta', 'fecha_inicio', 'fecha_fin', 'observaciones']
        widgets = {
            'camion': forms.Select(attrs={'class': 'form-control'}),
            'ruta': forms.Select(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'fecha_fin': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones adicionales...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo camiones activos
        self.fields['camion'].queryset = Camion.objects.filter(activo=True)
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('camion', css_class='form-group col-md-6 mb-3'),
                Column('ruta', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('fecha_inicio', css_class='form-group col-md-6 mb-3'),
                Column('fecha_fin', css_class='form-group col-md-6 mb-3'),
            ),
            'observaciones',
        )
    
    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError(
                    'La fecha de fin no puede ser anterior a la fecha de inicio.'
                )
        
        return cleaned_data


class CargaCamionForm(forms.ModelForm):
    """
    Formulario para crear carga de camión.
    """
    # Agregar campo para seleccionar la ruta
    ruta = forms.ModelChoiceField(
        queryset=Ruta.objects.filter(activo=True),
        required=True,
        label="Ruta",
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text="Selecciona la ruta para esta carga"
    )
    
    class Meta:
        model = CargaCamion
        fields = ['camion', 'ruta', 'fecha', 'observaciones']
        widgets = {
            'camion': forms.Select(attrs={'class': 'form-control'}),
            'fecha': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Observaciones sobre la carga...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo camiones activos
        self.fields['camion'].queryset = Camion.objects.filter(activo=True)
        
        # Configurar fecha por defecto si es nueva carga
        if not self.instance.pk:
            from django.utils import timezone
            self.fields['fecha'].initial = timezone.now().date()
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('camion', css_class='form-group col-md-6 mb-3'),
                Column('fecha', css_class='form-group col-md-6 mb-3'),
            ),
            'ruta',
            'observaciones',
            HTML('''
                <div class="alert alert-info mt-3">
                    <i class="bi bi-info-circle"></i>
                    <strong>Nota:</strong> Después de crear la carga, podrás agregar los productos.
                </div>
            ''')
        )
    
    def save(self, commit=True):
        """
        Sobrescribe el método save para crear o buscar la asignación automáticamente.
        """
        instance = super().save(commit=False)
        
        # Obtener la ruta seleccionada
        ruta = self.cleaned_data.get('ruta')
        camion = self.cleaned_data.get('camion')
        
        if ruta and camion:
            from camiones.models import AsignacionCamionRuta
            
            # Buscar o crear asignación activa para este camión y ruta
            asignacion, created = AsignacionCamionRuta.objects.get_or_create(
                camion=camion,
                ruta=ruta,
                activo=True,
                fecha_fin__isnull=True,
                defaults={
                    'fecha_inicio': self.cleaned_data.get('fecha'),
                }
            )
            
            instance.asignacion_camion_ruta = asignacion
        
        if commit:
            instance.save()
        
        return instance

class CargaCamionDetalleForm(forms.ModelForm):
    """
    Formulario para agregar productos a la carga.
    """
    class Meta:
        model = CargaCamionDetalle
        fields = ['producto', 'cantidad_cargada']
        widgets = {
            'producto': forms.Select(attrs={'class': 'form-control'}),
            'cantidad_cargada': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        carga_camion = kwargs.pop('carga_camion', None)
        super().__init__(*args, **kwargs)
        
        # Filtrar solo productos activos
        self.fields['producto'].queryset = Producto.objects.filter(estado='activo')
        
        # Si hay carga, excluir productos ya cargados
        if carga_camion:
            productos_ya_cargados = carga_camion.detalles.values_list('producto_id', flat=True)
            self.fields['producto'].queryset = self.fields['producto'].queryset.exclude(
                id__in=productos_ya_cargados
            )
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Row(
                Column('producto', css_class='form-group col-md-6 mb-3'),
                Column('cantidad_cargada', css_class='form-group col-md-6 mb-3'),
            ),
        )


class CuadreDiarioDetalleForm(forms.ModelForm):
    """
    Formulario para registrar el cuadre de cada producto.
    """
    class Meta:
        model = CuadreDiarioDetalle
        fields = ['cantidad_real_retorno', 'observaciones']
        widgets = {
            'cantidad_real_retorno': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'observaciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Explica la diferencia si existe...'
            }),
        }
