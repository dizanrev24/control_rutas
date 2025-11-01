from django.db import models

class Categoria(models.Model):
    """
    Categorías de productos
    """
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    """
    Productos disponibles para la venta
    """
    ESTADO_CHOICES = [
        ('activo', 'Activo'),
        ('inactivo', 'Inactivo'),
    ]

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, verbose_name="Descripción")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, 
                                 related_name='productos', verbose_name="Categoría")
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, 
                                       verbose_name="Precio de Compra")
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, 
                                      verbose_name="Precio de Venta")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='activo',
                            verbose_name="Estado")
    fecha_creacion = models.DateTimeField(auto_now_add=True, 
                                         verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

    @property
    def margen_ganancia(self):
        """Calcula el margen de ganancia"""
        if self.precio_compra > 0:
            return ((self.precio_venta - self.precio_compra) / self.precio_compra) * 100
        return 0