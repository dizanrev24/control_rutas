"""
URLs para el módulo de reportes.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.reporte_dashboard, name='reporte_dashboard'),
    path('fotos-duplicadas/', views.reporte_fotos_duplicadas, name='reporte_fotos_duplicadas'),
    path('ubicaciones-invalidas/', views.reporte_ubicaciones_invalidas, name='reporte_ubicaciones_invalidas'),
    path('ventas-por-vendedor/', views.reporte_ventas_por_vendedor, name='reporte_ventas_por_vendedor'),
]
