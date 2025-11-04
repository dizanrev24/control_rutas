from django.contrib import admin
from .models import (
    Camion, AsignacionCamionRuta, CargaCamion, 
    CargaCamionDetalle, CuadreDiario, CuadreDiarioDetalle
)


@admin.register(Camion)
class CamionAdmin(admin.ModelAdmin):
    list_display = ['placa', 'marca', 'modelo', 'activo']
    list_filter = ['activo', 'marca']
    search_fields = ['placa', 'marca', 'modelo']


@admin.register(AsignacionCamionRuta)
class AsignacionCamionRutaAdmin(admin.ModelAdmin):
    list_display = ['camion', 'ruta', 'fecha_inicio', 'fecha_fin', 'activo']
    list_filter = ['activo', 'ruta']
    search_fields = ['camion__placa', 'ruta__nombre']


class CargaCamionDetalleInline(admin.TabularInline):
    model = CargaCamionDetalle
    extra = 1


@admin.register(CargaCamion)
class CargaCamionAdmin(admin.ModelAdmin):
    list_display = ['camion', 'fecha', 'cerrado']
    list_filter = ['cerrado', 'fecha']
    search_fields = ['camion__placa']
    inlines = [CargaCamionDetalleInline]


class CuadreDiarioDetalleInline(admin.TabularInline):
    model = CuadreDiarioDetalle
    extra = 0


@admin.register(CuadreDiario)
class CuadreDiarioAdmin(admin.ModelAdmin):
    list_display = ['carga_camion', 'fecha_cuadre', 'estado']
    list_filter = ['estado', 'fecha_cuadre']
    inlines = [CuadreDiarioDetalleInline]
