from django.db import models
from django.core.validators import MinLengthValidator
from django.core.exceptions import ValidationError

class Cliente(models.Model):
    """
    Modelo para tiendas/negocios visitados por los vendedores (RF-02, RF-05)
    """
    nit = models.CharField(max_length=15, unique=True, verbose_name="NIT")
    nombre = models.CharField(max_length=200, validators=[MinLengthValidator(1)], 
                             verbose_name="Nombre del Negocio")
    nombre_contacto = models.CharField(max_length=100, blank=True, 
                                      verbose_name="Nombre del Contacto")
    correo = models.EmailField(blank=True, null=True, verbose_name="Correo Electrónico")
    telefono = models.CharField(max_length=15, verbose_name="Teléfono")
    direccion = models.TextField(verbose_name="Dirección")
    referencia_ubicacion = models.TextField(blank=True, 
                                           verbose_name="Referencia de Ubicación")
    
    # Geolocalización
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                 verbose_name="Latitud")
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                  verbose_name="Longitud")
    
    # Fotografía de referencia del negocio
    fotografia_referencia = models.ImageField(upload_to='clientes/', null=True, blank=True,
                                             verbose_name="Fotografía de Referencia")
    
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Registro")
    fecha_actualizacion = models.DateTimeField(auto_now=True, 
                                              verbose_name="Fecha de Actualización")

    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nit} - {self.nombre}"

    def clean(self):
        # Validar nombre (RF-05)
        if self.nombre:
            self.nombre = self.nombre.strip()
            if len(self.nombre) > 200:
                raise ValidationError({'nombre': 'El nombre no puede exceder 200 caracteres.'})
            if not self.nombre:
                raise ValidationError({'nombre': 'El nombre no puede estar vacío.'})
        
        # Validar NIT único (RF-02)
        if self.nit and Cliente.objects.filter(nit=self.nit).exclude(pk=self.pk).exists():
            raise ValidationError({'nit': 'Ya existe un cliente con este NIT.'})