"""
URLs para el módulo de asignaciones.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.asignacion_listar, name='asignacion_listar'),
    path('crear/', views.asignacion_crear, name='asignacion_crear'),
    path('<int:pk>/', views.asignacion_detalle, name='asignacion_detalle'),
    path('<int:pk>/finalizar/', views.asignacion_finalizar, name='asignacion_finalizar'),
    path('<int:pk>/regenerar/', views.asignacion_regenerar_planificaciones, name='asignacion_regenerar'),
]
