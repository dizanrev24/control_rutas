"""
Formularios para el módulo de asignaciones.
Maneja la asignación de rutas a vendedores con generación automática de planificaciones.
"""
from django import forms
from django.utils import timezone
from datetime import date
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Submit, HTML
from .models import Asignacion
from rutas.models import Ruta
from users.models import Usuario


class AsignacionForm(forms.ModelForm):
    """
    Formulario para crear asignaciones de ruta a vendedor.
    """
    class Meta:
        model = Asignacion
        fields = ['ruta', 'vendedor', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'fecha_fin': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
        labels = {
            'ruta': 'Ruta',
            'vendedor': 'Vendedor',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Fin (opcional)',
        }
        help_texts = {
            'ruta': 'Selecciona la ruta que será asignada',
            'vendedor': 'Selecciona el vendedor que recorrerá la ruta',
            'fecha_inicio': 'Fecha desde cuando el vendedor atenderá esta ruta',
            'fecha_fin': 'Dejar vacío para asignación indefinida',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo rutas activas
        self.fields['ruta'].queryset = Ruta.objects.filter(activo=True)
        self.fields['ruta'].widget.attrs.update({'class': 'form-select'})
        
        # Filtrar solo usuarios con rol de vendedor y activos
        self.fields['vendedor'].queryset = Usuario.objects.filter(
            rol='vendedor',
            is_active=True,
            activo=True
        ).order_by('first_name', 'last_name', 'username')
        self.fields['vendedor'].widget.attrs.update({'class': 'form-select'})
        
        # Personalizar la forma en que se muestran los vendedores
        self.fields['vendedor'].label_from_instance = self.vendedor_label_from_instance
        
        # Establecer fecha de inicio por defecto a hoy (usar date.today() en lugar de timezone.now())
        if not self.instance.pk:
            self.fields['fecha_inicio'].initial = date.today()
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(
                Column('ruta', css_class='col-md-6'),
                Column('vendedor', css_class='col-md-6'),
            ),
            Row(
                Column('fecha_inicio', css_class='col-md-6'),
                Column('fecha_fin', css_class='col-md-6'),
            ),
            HTML('<hr>'),
            HTML('''
                <div class="alert alert-info">
                    <i class="bi bi-info-circle me-2"></i>
                    <strong>Importante:</strong> Al crear la asignación, se generarán automáticamente 
                    las planificaciones diarias para el vendedor según los clientes de la ruta.
                </div>
            '''),
        )
    
    def vendedor_label_from_instance(self, obj):
        """
        Personaliza cómo se muestra cada vendedor en el select.
        """
        nombre_completo = obj.get_full_name() or obj.username
        if obj.codigo_empleado:
            return f"{nombre_completo} ({obj.codigo_empleado})"
        return nombre_completo
    
    def clean_fecha_inicio(self):
        """Validar que la fecha de inicio no sea anterior a hoy."""
        fecha_inicio = self.cleaned_data.get('fecha_inicio')
        
        # Solo validar para nuevas asignaciones
        if not self.instance.pk and fecha_inicio:
            # Usar date.today() en lugar de timezone.now().date()
            hoy = date.today()
            if fecha_inicio < hoy:
                raise forms.ValidationError(
                    'La fecha de inicio no puede ser anterior a hoy.'
                )
        
        return fecha_inicio
    
    def clean(self):
        cleaned_data = super().clean()
        ruta = cleaned_data.get('ruta')
        vendedor = cleaned_data.get('vendedor')
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')
        
        # Validar que el vendedor tenga rol de vendedor
        if vendedor and vendedor.rol != 'vendedor':
            raise forms.ValidationError({
                'vendedor': 'El usuario seleccionado no es un vendedor.'
            })
        
        # Validar que fecha_fin sea posterior a fecha_inicio
        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise forms.ValidationError(
                    'La fecha de fin debe ser posterior a la fecha de inicio.'
                )
            
            # Validar que la diferencia no sea muy grande (opcional, máximo 1 año)
            diferencia_dias = (fecha_fin - fecha_inicio).days
            if diferencia_dias > 365:
                raise forms.ValidationError(
                    'La asignación no puede durar más de 1 año. '
                    'Para asignaciones más largas, déjela indefinida.'
                )
        
        # Validar que no haya solapamiento con otras asignaciones activas
        if ruta and vendedor and fecha_inicio:
            # Construir query para detectar solapamientos
            asignaciones_existentes = Asignacion.objects.filter(
                ruta=ruta,
                vendedor=vendedor
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            # Filtrar asignaciones que se solapen
            for asignacion in asignaciones_existentes:
                # Si la asignación existente no tiene fecha_fin, está activa indefinidamente
                if not asignacion.fecha_fin:
                    if not fecha_fin or fecha_fin >= asignacion.fecha_inicio:
                        raise forms.ValidationError(
                            f'Ya existe una asignación activa de esta ruta a este vendedor '
                            f'desde el {asignacion.fecha_inicio.strftime("%d/%m/%Y")} (indefinida).'
                        )
                else:
                    # Hay solapamiento si:
                    # - Nueva inicia antes de que termine la existente Y
                    # - Nueva termina (o es indefinida) después de que inicie la existente
                    if fecha_inicio <= asignacion.fecha_fin:
                        if not fecha_fin or fecha_fin >= asignacion.fecha_inicio:
                            raise forms.ValidationError(
                                f'Ya existe una asignación de esta ruta a este vendedor '
                                f'del {asignacion.fecha_inicio.strftime("%d/%m/%Y")} '
                                f'al {asignacion.fecha_fin.strftime("%d/%m/%Y")}.'
                            )
        
        # Validar que la ruta tenga clientes
        if ruta and not ruta.detalles.exists():
            raise forms.ValidationError({
                'ruta': 'La ruta seleccionada no tiene clientes asignados. '
                        'Por favor, agregue clientes a la ruta antes de crear una asignación.'
            })
        
        return cleaned_data


class AsignacionFiltroForm(forms.Form):
    """
    Formulario para filtrar asignaciones en la lista.
    """
    vendedor = forms.ModelChoiceField(
        required=False,
        label='Vendedor',
        queryset=Usuario.objects.filter(
            rol='vendedor',
            is_active=True,
            activo=True
        ).order_by('first_name', 'last_name', 'username'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Todos los vendedores'
    )
    
    ruta = forms.ModelChoiceField(
        required=False,
        label='Ruta',
        queryset=Ruta.objects.filter(activo=True).order_by('nombre'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        empty_label='Todas las rutas'
    )
    
    estado = forms.ChoiceField(
        required=False,
        label='Estado',
        choices=[
            ('', 'Todas'),
            ('activas', 'Activas'),
            ('finalizadas', 'Finalizadas'),
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial=''
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar la forma en que se muestran los vendedores
        self.fields['vendedor'].label_from_instance = self.vendedor_label_from_instance
        
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_class = 'form-inline'
        self.helper.layout = Layout(
            Row(
                Column('vendedor', css_class='col-md-4'),
                Column('ruta', css_class='col-md-4'),
                Column('estado', css_class='col-md-4'),
            ),
        )
    
    def vendedor_label_from_instance(self, obj):
        """
        Personaliza cómo se muestra cada vendedor en el select.
        """
        nombre_completo = obj.get_full_name() or obj.username
        if obj.codigo_empleado:
            return f"{nombre_completo} ({obj.codigo_empleado})"
        return nombre_completo