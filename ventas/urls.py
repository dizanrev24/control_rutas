"""
URLs para el módulo de ventas.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.venta_listar, name='venta_listar'),
    path('<int:pk>/', views.venta_detalle, name='venta_detalle'),
    path('crear/<int:detalle_id>/', views.venta_crear, name='venta_crear'),
    path('pdf/<int:venta_id>/', views.venta_pdf, name='venta_pdf'),
]
