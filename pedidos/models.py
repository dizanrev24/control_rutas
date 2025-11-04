from django.db import models
from clientes.models import Cliente
from productos.models import Producto
from planificacion.models import DetallePlanificacion


class Pedido(models.Model):
	"""
	Registro de pedidos realizados durante las visitas
	Los pedidos NO descuentan del stock del camión, solo registran
	qué productos y cantidades el cliente quiere para futuras entregas
	"""
	ESTADO_CHOICES = [
		('pendiente', 'Pendiente'),
		('procesado', 'Procesado'),
		('entregado', 'Entregado'),
		('cancelado', 'Cancelado'),
	]

	detalle_planificacion = models.ForeignKey(
		DetallePlanificacion,
		on_delete=models.PROTECT,
		related_name='pedidos',
		verbose_name="Detalle de Planificación"
	)
	cliente = models.ForeignKey(
		Cliente,
		on_delete=models.PROTECT,
		related_name='pedidos',
		verbose_name="Cliente"
	)
	fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Pedido")
	fecha_entrega_estimada = models.DateField(
		null=True,
		blank=True,
		verbose_name="Fecha de Entrega Estimada"
	)
	total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='pendiente',
		verbose_name="Estado"
	)
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")

	class Meta:
		verbose_name = 'Pedido'
		verbose_name_plural = 'Pedidos'
		ordering = ['-fecha']

	def __str__(self):
		return f"Pedido #{self.id} - {self.cliente.nombre} - Q{self.total}"

	def calcular_total(self):
		"""Calcula el total del pedido sumando los detalles"""
		return sum(detalle.subtotal for detalle in self.detalles.all())


class DetallePedido(models.Model):
	"""
	Detalle de productos en cada pedido
	"""
	pedido = models.ForeignKey(
		Pedido,
		on_delete=models.CASCADE,
		related_name='detalles',
		verbose_name="Pedido"
	)
	producto = models.ForeignKey(
		Producto,
		on_delete=models.PROTECT,
		verbose_name="Producto"
	)
	cantidad = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cantidad")
	precio_unitario = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Precio Unitario"
	)
	subtotal = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Subtotal")

	class Meta:
		verbose_name = 'Detalle de Pedido'
		verbose_name_plural = 'Detalles de Pedido'
		ordering = ['producto__nombre']

	def __str__(self):
		return f"{self.producto.nombre} x {self.cantidad}"

	def save(self, *args, **kwargs):
		# Calcular subtotal automáticamente
		self.subtotal = self.cantidad * self.precio_unitario
		super().save(*args, **kwargs)
