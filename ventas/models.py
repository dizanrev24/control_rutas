from django.db import models
from clientes.models import Cliente
from productos.models import Producto
from planificacion.models import DetallePlanificacion
from camiones.models import CargaCamion

class Venta(models.Model):
    """
    Registro de ventas realizadas durante las visitas (RF-03)
    Las ventas descuentan del inventario del camión (stock móvil)
    """
    ESTADO_CHOICES = [
        ('completada', 'Completada'),
        ('pendiente', 'Pendiente'),
        ('cancelada', 'Cancelada'),
    ]

    detalle_planificacion = models.ForeignKey(
        DetallePlanificacion,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name="Detalle de Planificación"
    )
    carga_camion = models.ForeignKey(
        CargaCamion,
        on_delete=models.PROTECT,
        related_name='ventas',
        verbose_name="Carga de Camión",
        help_text="Inventario móvil del cual se descuentan los productos"
    )
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT,
                               related_name='ventas', verbose_name="Cliente")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Venta")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='completada',
                            verbose_name="Estado")
    observaciones = models.TextField(blank=True, verbose_name="Observaciones")

    class Meta:
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente.nombre} - Q{self.total}"

    def calcular_total(self):
        """Calcula el total de la venta sumando los detalles"""
        return sum(detalle.subtotal for detalle in self.detalles.all())


class DetalleVenta(models.Model):
    """
    Detalle de productos vendidos en cada venta
    """
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE,
                            related_name='detalles', verbose_name="Venta")
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT,
                                verbose_name="Producto")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2,
                                         verbose_name="Precio Unitario")
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")

    class Meta:
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

    def save(self, *args, **kwargs):
        # Calcular subtotal automáticamente
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)