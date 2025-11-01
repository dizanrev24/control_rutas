from django.db import models
from django.conf import settings
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

class Vendedor(models.Model):
    """
    Modelo para vendedores (RF-09, RF-08)
    Tabla vendedores: dpi, nombre, correo, teléfono, código empleado
    """
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vendedor',
        limit_choices_to={'rol': 'vendedor'},
        verbose_name="Usuario"
    )
    dpi = models.CharField(
        max_length=13, 
        unique=True, 
        validators=[MinLengthValidator(13)],
        verbose_name="DPI",
        help_text="Documento Personal de Identificación (13 dígitos)"
    )
    codigo_empleado = models.CharField(
        max_length=20, 
        unique=True,
        verbose_name="Código de Empleado"
    )
    nombre_completo = models.CharField(
        max_length=100,
        verbose_name="Nombre Completo"
    )
    correo = models.EmailField(
        unique=True,
        verbose_name="Correo Electrónico"
    )
    telefono = models.CharField(
        max_length=15,
        verbose_name="Teléfono"
    )
    direccion = models.TextField(
        blank=True,
        verbose_name="Dirección"
    )
    fecha_contratacion = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Contratación"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    fotografia = models.ImageField(
        upload_to='vendedores/',
        null=True,
        blank=True,
        verbose_name="Fotografía"
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )

    class Meta:
        verbose_name = 'Vendedor'
        verbose_name_plural = 'Vendedores'
        ordering = ['codigo_empleado']

    def __str__(self):
        return f"{self.codigo_empleado} - {self.nombre_completo}"

    def clean(self):
        """
        Validaciones personalizadas (RF-08, RF-09)
        """
        # Validar DPI único
        if self.dpi:
            if len(self.dpi) != 13:
                raise ValidationError({'dpi': 'El DPI debe tener exactamente 13 dígitos.'})
            
            if Vendedor.objects.filter(dpi=self.dpi).exclude(pk=self.pk).exists():
                raise ValidationError({'dpi': 'Ya existe un vendedor con este DPI.'})
        
        # Validar código de empleado único
        if self.codigo_empleado:
            if Vendedor.objects.filter(codigo_empleado=self.codigo_empleado).exclude(pk=self.pk).exists():
                raise ValidationError({'codigo_empleado': 'Ya existe un vendedor con este código de empleado.'})
        
        # Validar correo único
        if self.correo:
            if Vendedor.objects.filter(correo=self.correo).exclude(pk=self.pk).exists():
                raise ValidationError({'correo': 'Ya existe un vendedor con este correo electrónico.'})
        
        # Validar nombre (sin espacios iniciales/finales)
        if self.nombre_completo:
            self.nombre_completo = self.nombre_completo.strip()
            if not self.nombre_completo:
                raise ValidationError({'nombre_completo': 'El nombre no puede estar vacío.'})

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def total_ventas_mes(self):
        """
        Calcula el total de ventas del mes actual
        """
        from datetime import datetime
        from ventas.models import Venta
        
        mes_actual = datetime.now().month
        año_actual = datetime.now().year
        
        ventas = Venta.objects.filter(
            detalle_planificacion__planificacion__asignacion__vendedor__vendedor=self,
            fecha__month=mes_actual,
            fecha__year=año_actual,
            estado='completada'
        )
        
        total = sum(venta.total for venta in ventas)
        return total

    @property
    def rutas_asignadas(self):
        """
        Retorna las rutas asignadas al vendedor
        """
        from asignaciones.models import Asignacion
        return Asignacion.objects.filter(vendedor__vendedor=self, activo=True)