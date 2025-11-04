from django.contrib import admin
from .models import Pedido, DetallePedido


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 1


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'fecha', 'total', 'estado']
    list_filter = ['estado', 'fecha']
    search_fields = ['cliente__nombre', 'cliente__nit']
    inlines = [DetallePedidoInline]
