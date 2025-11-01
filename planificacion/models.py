from django.db import models
from asignaciones.models import Asignacion
from rutas.models import RutaDetalle

class Planificacion(models.Model):
    """
    Planificación de visitas para una fecha específica (RF-04)
    """
    asignacion = models.ForeignKey(Asignacion, on_delete=models.CASCADE,
                                  related_name='planificaciones',
                                  verbose_name="Asignación")
    ruta_detalle = models.ForeignKey(RutaDetalle, on_delete=models.CASCADE,
                                    related_name='planificaciones',
                                    verbose_name="Detalle de Ruta")
    fecha = models.DateField(verbose_name="Fecha Planificada")
    fecha_creacion = models.DateTimeField(auto_now_add=True,
                                         verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = 'Planificación'
        verbose_name_plural = 'Planificaciones'
        ordering = ['fecha', 'ruta_detalle__orden_visita']

    def __str__(self):
        return f"{self.asignacion.ruta.nombre} - {self.fecha}"


class DetallePlanificacion(models.Model):
    """
    Registro de la visita real al cliente (check-in/check-out) (RF-04)
    """
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('visitado', 'Visitado'),
        ('no_visitado', 'No Visitado'),
        ('cerrado', 'Negocio Cerrado'),
    ]

    planificacion = models.ForeignKey(Planificacion, on_delete=models.CASCADE,
                                     related_name='detalles_visita',
                                     verbose_name="Planificación")
    
    # Geolocalización de la visita real
    latitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                 verbose_name="Latitud de Visita")
    longitud = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True,
                                  verbose_name="Longitud de Visita")
    
    # Fotografía de la visita
    fotografia_referencia = models.ImageField(upload_to='visitas/', null=True, blank=True,
                                             verbose_name="Fotografía de la Visita")
    
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente',
                            verbose_name="Estado")
    
    hora_llegada = models.DateTimeField(null=True, blank=True, verbose_name="Hora de Llegada")
    hora_salida = models.DateTimeField(null=True, blank=True, verbose_name="Hora de Salida")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")
    fecha_creacion = models.DateTimeField(auto_now_add=True,
                                         verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = 'Detalle de Planificación'
        verbose_name_plural = 'Detalles de Planificación'
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Visita {self.planificacion.ruta_detalle.cliente.nombre} - {self.estado}"

    @property
    def duracion_visita(self):
        """Calcula la duración de la visita"""
        if self.hora_llegada and self.hora_salida:
            return self.hora_salida - self.hora_llegada
        return None