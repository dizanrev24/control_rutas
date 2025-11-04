from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

class Usuario(AbstractUser):
    """
    Modelo extendido de usuario para vendedores, secretarias y administradores
    """
    dpi = models.CharField(
        max_length=13, 
        unique=True, 
        null=True, 
        blank=True, 
        verbose_name="DPI",
        help_text="Documento Personal de Identificación (13 dígitos)"
    )
    codigo_empleado = models.CharField(
        max_length=20, 
        unique=True, 
        null=True, 
        blank=True,
        verbose_name="Código de Empleado"
    )
    telefono = models.CharField(
        max_length=15, 
        blank=True, 
        verbose_name="Teléfono"
    )
    rol = models.CharField(
        max_length=50, 
        choices=[
            ('admin', 'Administrador'),
            ('secretaria', 'Secretaria'),
            ('vendedor', 'Vendedor'),
        ], 
        verbose_name="Rol"
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo"
    )
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['username']

    def __str__(self):
        nombre = self.get_full_name() or self.username
        codigo = self.codigo_empleado or "Sin código"
        return f"{nombre} ({codigo})"

    def clean(self):
        """
        Validaciones personalizadas (RF-08)
        """
        # Validar DPI único
        if self.dpi:
            # Eliminar espacios
            self.dpi = self.dpi.strip()
            
            # Validar longitud
            if len(self.dpi) != 13:
                raise ValidationError({
                    'dpi': 'El DPI debe tener exactamente 13 dígitos.'
                })
            
            # Validar que sea numérico
            if not self.dpi.isdigit():
                raise ValidationError({
                    'dpi': 'El DPI solo debe contener números.'
                })
            
            # Validar unicidad
            if Usuario.objects.filter(dpi=self.dpi).exclude(pk=self.pk).exists():
                raise ValidationError({
                    'dpi': 'Ya existe un usuario con este DPI.'
                })
        
        # Validar código de empleado único
        if self.codigo_empleado:
            self.codigo_empleado = self.codigo_empleado.strip()
            if Usuario.objects.filter(codigo_empleado=self.codigo_empleado).exclude(pk=self.pk).exists():
                raise ValidationError({
                    'codigo_empleado': 'Ya existe un usuario con este código de empleado.'
                })
        
        # Validar que el vendedor tenga DPI y código
        if self.rol == 'vendedor':
            if not self.dpi:
                raise ValidationError({
                    'dpi': 'Los vendedores deben tener un DPI registrado.'
                })
            if not self.codigo_empleado:
                raise ValidationError({
                    'codigo_empleado': 'Los vendedores deben tener un código de empleado.'
                })
        
        # Validar teléfono si está presente
        if self.telefono:
            self.telefono = self.telefono.strip()
            # Remover caracteres especiales comunes
            telefono_limpio = self.telefono.replace('-', '').replace(' ', '').replace('+', '')
            if not telefono_limpio.isdigit():
                raise ValidationError({
                    'telefono': 'El teléfono solo debe contener números, espacios, guiones o el símbolo +.'
                })
    
    REQUIRED_FIELDS = ['rol', 'email']

    def save(self, *args, **kwargs):
        """
        Sobrescribir save para ejecutar validaciones
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def es_vendedor(self):
        """Verifica si el usuario es vendedor"""
        return self.rol == 'vendedor'
    
    @property
    def es_admin(self):
        """Verifica si el usuario es administrador"""
        return self.rol == 'admin'
    
    @property
    def es_secretaria(self):
        """Verifica si el usuario es secretaria"""
        return self.rol == 'secretaria'
    
    @property
    def puede_generar_reportes(self):
        """Verifica si el usuario puede generar reportes (RF-03)"""
        return self.rol in ['admin', 'secretaria']
    
    @property
    def puede_gestionar_rutas(self):
        """Verifica si el usuario puede gestionar rutas (RF-01)"""
        return self.rol in ['admin', 'secretaria']