from django.db import models
from clientes.models import Cliente

class Ruta(models.Model):
    """
    Rutas que contienen las tiendas a visitar (RF-01)
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Ruta")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activa")
    fecha_creacion = models.DateTimeField(auto_now_add=True, 
                                         verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = 'Ruta'
        verbose_name_plural = 'Rutas'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class RutaDetalle(models.Model):
    """
    Detalle de clientes que pertenecen a una ruta específica (RF-01)
    """
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, 
                           related_name='detalles', verbose_name="Ruta")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, 
                               related_name='rutas_asignadas', verbose_name="Cliente")
    orden_visita = models.IntegerField(default=1, 
                                      verbose_name="Orden de Visita",
                                      help_text="Orden en que debe visitarse al cliente")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_asignacion = models.DateTimeField(auto_now_add=True, 
                                           verbose_name="Fecha de Asignación")

    class Meta:
        verbose_name = 'Detalle de Ruta'
        verbose_name_plural = 'Detalles de Rutas'
        unique_together = ['ruta', 'cliente']
        ordering = ['ruta', 'orden_visita']

    def __str__(self):
        return f"{self.ruta.nombre} - {self.cliente.nombre} (Orden: {self.orden_visita})"