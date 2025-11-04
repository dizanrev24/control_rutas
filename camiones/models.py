from django.db import models
from django.core.validators import MinLengthValidator
from rutas.models import Ruta
from productos.models import Producto


class Camion(models.Model):
	"""
	Vehículos utilizados para distribución
	"""
	placa = models.CharField(
		max_length=15,
		unique=True,
		validators=[MinLengthValidator(1)],
		verbose_name="Placa"
	)
	marca = models.CharField(max_length=50, verbose_name="Marca")
	modelo = models.CharField(max_length=50, blank=True, verbose_name="Modelo")
	año = models.IntegerField(null=True, blank=True, verbose_name="Año")
	capacidad_carga = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		help_text="Capacidad en kilogramos",
		null=True,
		blank=True,
		verbose_name="Capacidad de Carga (kg)"
	)
	activo = models.BooleanField(default=True, verbose_name="Activo")
	fecha_registro = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha de Registro"
	)

	class Meta:
		verbose_name = 'Camión'
		verbose_name_plural = 'Camiones'
		ordering = ['placa']

	def __str__(self):
		return f"{self.placa} - {self.marca}"


class AsignacionCamionRuta(models.Model):
	"""
	Historial de asignación de camiones a rutas
	Para trazabilidad: saber qué camión estuvo en qué ruta y cuándo
	"""
	camion = models.ForeignKey(
		Camion,
		on_delete=models.CASCADE,
		related_name='asignaciones_rutas',
		verbose_name="Camión"
	)
	ruta = models.ForeignKey(
		Ruta,
		on_delete=models.CASCADE,
		related_name='asignaciones_camiones',
		verbose_name="Ruta"
	)
	fecha_inicio = models.DateField(verbose_name="Fecha de Inicio")
	fecha_fin = models.DateField(
		null=True,
		blank=True,
		verbose_name="Fecha de Fin",
		help_text="Si está vacío, la asignación está activa"
	)
	activo = models.BooleanField(default=True, verbose_name="Activo")
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")
	fecha_creacion = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha de Creación"
	)

	class Meta:
		verbose_name = 'Asignación de Camión a Ruta'
		verbose_name_plural = 'Asignaciones de Camiones a Rutas'
		ordering = ['-fecha_inicio']

	def __str__(self):
		estado = "Activa" if self.activo and not self.fecha_fin else "Inactiva"
		return f"{self.camion.placa} → {self.ruta.nombre} ({estado})"


class CargaCamion(models.Model):
	"""
	Registro de productos cargados en el camión al inicio del día
	Funciona como inventario móvil
	"""
	camion = models.ForeignKey(
		Camion,
		on_delete=models.PROTECT,
		related_name='cargas',
		verbose_name="Camión"
	)
	asignacion_camion_ruta = models.ForeignKey(
		AsignacionCamionRuta,
		on_delete=models.PROTECT,
		related_name='cargas',
		verbose_name="Asignación Camión-Ruta",
		help_text="Ruta asociada a esta carga"
	)
	fecha = models.DateField(verbose_name="Fecha de Carga")
	hora_carga = models.TimeField(
		auto_now_add=True,
		verbose_name="Hora de Carga"
	)
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")
	cerrado = models.BooleanField(
		default=False,
		verbose_name="Cerrado",
		help_text="Si está cerrado, no se pueden agregar más productos"
	)
	fecha_creacion = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha de Creación"
	)

	class Meta:
		verbose_name = 'Carga de Camión'
		verbose_name_plural = 'Cargas de Camiones'
		unique_together = ['camion', 'fecha']
		ordering = ['-fecha', '-hora_carga']

	def __str__(self):
		return f"Carga {self.camion.placa} - {self.fecha}"

	@property
	def total_productos_cargados(self):
		"""Retorna el total de productos cargados"""
		return sum(
			detalle.cantidad_cargada
			for detalle in self.detalles.all()
		)

	@property
	def valor_total_carga(self):
		"""Retorna el valor total de la carga"""
		return sum(
			detalle.cantidad_cargada * detalle.producto.precio_venta
			for detalle in self.detalles.all()
		)


class CargaCamionDetalle(models.Model):
	"""
	Detalle de productos cargados en el camión
	"""
	carga_camion = models.ForeignKey(
		CargaCamion,
		on_delete=models.CASCADE,
		related_name='detalles',
		verbose_name="Carga de Camión"
	)
	producto = models.ForeignKey(
		Producto,
		on_delete=models.PROTECT,
		verbose_name="Producto"
	)
	cantidad_cargada = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Cargada"
	)
	cantidad_actual = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Actual",
		help_text="Se actualiza con cada venta"
	)
	fecha_creacion = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha de Creación"
	)

	class Meta:
		verbose_name = 'Detalle de Carga'
		verbose_name_plural = 'Detalles de Carga'
		unique_together = ['carga_camion', 'producto']
		ordering = ['producto__nombre']

	def __str__(self):
		return f"{self.producto.nombre} - {self.cantidad_actual}/{self.cantidad_cargada}"

	@property
	def cantidad_vendida(self):
		"""Calcula cuánto se ha vendido de este producto"""
		return self.cantidad_cargada - self.cantidad_actual

	def save(self, *args, **kwargs):
		# Al crear, cantidad_actual = cantidad_cargada
		if not self.pk:
			self.cantidad_actual = self.cantidad_cargada
		super().save(*args, **kwargs)


class CuadreDiario(models.Model):
	"""
	Cuadre de fin de día para verificar inventario del camión
	"""
	ESTADO_CHOICES = [
		('pendiente', 'Pendiente'),
		('cuadrado', 'Cuadrado'),
		('con_diferencia', 'Con Diferencia'),
	]

	carga_camion = models.OneToOneField(
		CargaCamion,
		on_delete=models.CASCADE,
		related_name='cuadre',
		verbose_name="Carga de Camión"
	)
	fecha_cuadre = models.DateTimeField(
		auto_now_add=True,
		verbose_name="Fecha de Cuadre"
	)
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")
	estado = models.CharField(
		max_length=20,
		choices=ESTADO_CHOICES,
		default='pendiente',
		verbose_name="Estado"
	)

	class Meta:
		verbose_name = 'Cuadre Diario'
		verbose_name_plural = 'Cuadres Diarios'
		ordering = ['-fecha_cuadre']

	def __str__(self):
		return f"Cuadre {self.carga_camion.camion.placa} - {self.carga_camion.fecha}"

	def calcular_cuadre(self):
		"""
		Calcula el cuadre comparando lo cargado vs vendido vs retornado
		"""
		detalles = []

		for detalle_carga in self.carga_camion.detalles.all():
			esperado = detalle_carga.cantidad_actual
            
			detalle_info = {
				'producto': detalle_carga.producto,
				'cargado': detalle_carga.cantidad_cargada,
				'vendido': detalle_carga.cantidad_vendida,
				'esperado': esperado,
				'actual': detalle_carga.cantidad_actual,
				'diferencia': 0
			}
			detalles.append(detalle_info)

		return detalles


class CuadreDiarioDetalle(models.Model):
	"""
	Detalle del cuadre por producto
	Registra lo que realmente regresó vs lo esperado
	"""
	cuadre = models.ForeignKey(
		CuadreDiario,
		on_delete=models.CASCADE,
		related_name='detalles',
		verbose_name="Cuadre"
	)
	producto = models.ForeignKey(
		Producto,
		on_delete=models.PROTECT,
		verbose_name="Producto"
	)
	cantidad_cargada = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Cargada"
	)
	cantidad_vendida = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Vendida"
	)
	cantidad_esperada = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Esperada de Retorno"
	)
	cantidad_real_retorno = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Cantidad Real de Retorno",
		help_text="Registrada por secretaria/admin al final del día"
	)
	diferencia = models.DecimalField(
		max_digits=10,
		decimal_places=2,
		verbose_name="Diferencia",
		help_text="Positivo = sobrante, Negativo = faltante"
	)
	observaciones = models.TextField(blank=True, verbose_name="Observaciones")

	class Meta:
		verbose_name = 'Detalle de Cuadre'
		verbose_name_plural = 'Detalles de Cuadre'
		unique_together = ['cuadre', 'producto']
		ordering = ['producto__nombre']

	def __str__(self):
		return f"{self.producto.nombre} - Dif: {self.diferencia}"

	def save(self, *args, **kwargs):
		# Calcular diferencia automáticamente
		self.diferencia = self.cantidad_real_retorno - self.cantidad_esperada
		super().save(*args, **kwargs)
