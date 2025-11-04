from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.exceptions import ValidationError
from rutas.models import Ruta
from users.models import Usuario


class Asignacion(models.Model):
    """
    Asignación de rutas a vendedores con periodo definido (RF-04)
    
    Permite asignar una ruta a un vendedor específico por un periodo de tiempo.
    Genera automáticamente las planificaciones diarias para cada cliente de la ruta.
    """
    ruta = models.ForeignKey(
        Ruta, 
        on_delete=models.CASCADE, 
        related_name='asignaciones', 
        verbose_name="Ruta"
    )
    vendedor = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='asignaciones_rutas',
        verbose_name="Vendedor",
        limit_choices_to={'rol': 'vendedor', 'is_active': True}
    )
    fecha_inicio = models.DateField(
        verbose_name="Fecha de Inicio",
        help_text="Fecha desde la cual comienza la asignación"
    )
    fecha_fin = models.DateField(
        verbose_name="Fecha de Fin",
        null=True,
        blank=True,
        help_text="Fecha de finalización. Dejar vacío para asignación indefinida."
    )
    fecha_asignacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de Creación"
    )

    class Meta:
        verbose_name = 'Asignación'
        verbose_name_plural = 'Asignaciones'
        ordering = ['-fecha_inicio', 'ruta__nombre']
        indexes = [
            models.Index(fields=['vendedor', 'fecha_inicio']),
            models.Index(fields=['ruta', 'fecha_inicio']),
            models.Index(fields=['fecha_inicio', 'fecha_fin']),
        ]
        # Constraint para evitar solapamientos (opcional pero recomendado)
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_fin__isnull=True) | models.Q(fecha_fin__gte=models.F('fecha_inicio')),
                name='fecha_fin_mayor_que_inicio'
            )
        ]

    def __str__(self):
        """
        Representación en string de la asignación.
        
        Returns:
            str: Descripción de la asignación
        """
        vendedor_nombre = self.vendedor.get_full_name() or self.vendedor.username
        if self.fecha_fin:
            return f"{self.ruta.nombre} → {vendedor_nombre} ({self.fecha_inicio} al {self.fecha_fin})"
        return f"{self.ruta.nombre} → {vendedor_nombre} (desde {self.fecha_inicio})"

    def clean(self):
        """
        Validaciones personalizadas del modelo.
        """
        # Validar que el vendedor tenga rol de vendedor
        if self.vendedor and self.vendedor.rol != 'vendedor':
            raise ValidationError({
                'vendedor': 'El usuario seleccionado debe tener rol de vendedor.'
            })
        
        # Validar que fecha_fin sea posterior a fecha_inicio
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin < self.fecha_inicio:
                raise ValidationError({
                    'fecha_fin': 'La fecha de fin debe ser posterior a la fecha de inicio.'
                })
        
        # Validar que no haya solapamientos con otras asignaciones
        if self.vendedor and self.ruta and self.fecha_inicio:
            asignaciones_existentes = Asignacion.objects.filter(
                vendedor=self.vendedor,
                ruta=self.ruta
            ).exclude(pk=self.pk)
            
            for asignacion in asignaciones_existentes:
                # Si la existente no tiene fecha_fin, está activa indefinidamente
                if not asignacion.fecha_fin:
                    if not self.fecha_fin or self.fecha_fin >= asignacion.fecha_inicio:
                        raise ValidationError(
                            f'Ya existe una asignación activa de esta ruta para este vendedor '
                            f'desde el {asignacion.fecha_inicio.strftime("%d/%m/%Y")}.'
                        )
                else:
                    # Verificar solapamiento de periodos
                    if self.fecha_inicio <= asignacion.fecha_fin:
                        if not self.fecha_fin or self.fecha_fin >= asignacion.fecha_inicio:
                            raise ValidationError(
                                f'Ya existe una asignación de esta ruta para este vendedor '
                                f'del {asignacion.fecha_inicio.strftime("%d/%m/%Y")} '
                                f'al {asignacion.fecha_fin.strftime("%d/%m/%Y")}.'
                            )

    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para ejecutar validaciones.
        """
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def esta_activa(self):
        """
        Verifica si la asignación está activa en la fecha actual.
        
        Returns:
            bool: True si está activa, False si ya finalizó
        """
        hoy = timezone.now().date()
        
        # No ha comenzado aún
        if hoy < self.fecha_inicio:
            return False
        
        # Ya finalizó
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        
        return True

    @property
    def dias_asignados(self):
        """
        Calcula el número de días de la asignación.
        
        Returns:
            int: Número de días o None si es indefinida
        """
        if not self.fecha_fin:
            return None
        
        return (self.fecha_fin - self.fecha_inicio).days + 1

    @property
    def dias_restantes(self):
        """
        Calcula cuántos días faltan para que termine la asignación.
        
        Returns:
            int: Número de días restantes, 0 si ya finalizó, None si es indefinida
        """
        if not self.fecha_fin:
            return None
        
        hoy = timezone.now().date()
        
        if hoy > self.fecha_fin:
            return 0
        
        return (self.fecha_fin - hoy).days + 1

    @property
    def dias_transcurridos(self):
        """
        Calcula cuántos días han transcurrido desde el inicio.
        
        Returns:
            int: Número de días transcurridos (puede ser negativo si aún no inicia)
        """
        hoy = timezone.now().date()
        return (hoy - self.fecha_inicio).days

    @property
    def porcentaje_completado(self):
        """
        Calcula el porcentaje de avance de la asignación.
        
        Returns:
            float: Porcentaje de 0 a 100, o None si es indefinida
        """
        if not self.fecha_fin:
            return None
        
        dias_totales = self.dias_asignados
        if dias_totales <= 0:
            return 0
        
        dias_pasados = max(0, self.dias_transcurridos)
        porcentaje = (dias_pasados / dias_totales) * 100
        
        return min(100, max(0, porcentaje))

    @property
    def estado_label(self):
        """
        Devuelve una etiqueta descriptiva del estado actual.
        
        Returns:
            str: 'Pendiente', 'Activa' o 'Finalizada'
        """
        hoy = timezone.now().date()
        
        if hoy < self.fecha_inicio:
            return 'Pendiente'
        elif self.esta_activa:
            return 'Activa'
        else:
            return 'Finalizada'

    def tiene_planificaciones(self):
        """
        Verifica si la asignación tiene planificaciones generadas.
        
        Returns:
            bool: True si tiene planificaciones
        """
        return self.planificaciones.exists()

    def total_clientes(self):
        """
        Devuelve el número total de clientes en la ruta asignada.
        
        Returns:
            int: Cantidad de clientes
        """
        return self.ruta.detalles.count()

    def finalizar(self):
        """
        Finaliza la asignación estableciendo la fecha_fin a hoy.
        """
        if not self.fecha_fin:
            self.fecha_fin = timezone.now().date()
            self.save()