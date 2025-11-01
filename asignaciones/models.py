from django.db import models
from django.conf import settings
from rutas.models import Ruta

class Asignacion(models.Model):
    """
    Asignación de rutas a vendedores (RF-04)
    """
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE, 
                           related_name='asignaciones', verbose_name="Ruta")
    vendedor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='asignaciones_rutas',
        limit_choices_to={'rol': 'vendedor'},
        verbose_name="Vendedor"
    )
    activo = models.BooleanField(default=True, verbose_name="Activa")
    fecha_asignacion = models.DateTimeField(auto_now_add=True, 
                                           verbose_name="Fecha de Asignación")

    class Meta:
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        unique_together = ['ruta', 'vendedor']
        ordering = ['-fecha_asignacion']

    def __str__(self):
        return f"{self.ruta.nombre} -> {self.vendedor.get_full_name()}"