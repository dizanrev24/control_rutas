from django.contrib import admin
from .models import Vendedor

@admin.register(Vendedor)
class VendedorAdmin(admin.ModelAdmin):
    list_display = ['codigo_empleado', 'nombre_completo', 'dpi', 'telefono', 'correo', 'activo']
    list_filter = ['activo', 'fecha_contratacion']
    search_fields = ['codigo_empleado', 'nombre_completo', 'dpi', 'correo']
    readonly_fields = ['fecha_registro', 'fecha_actualizacion']
    
    fieldsets = (
        ('Información Personal', {
            'fields': ('usuario', 'codigo_empleado', 'dpi', 'nombre_completo', 'fotografia')
        }),
        ('Contacto', {
            'fields': ('correo', 'telefono', 'direccion')
        }),
        ('Información Laboral', {
            'fields': ('fecha_contratacion', 'activo')
        }),
        ('Fechas', {
            'fields': ('fecha_registro', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )