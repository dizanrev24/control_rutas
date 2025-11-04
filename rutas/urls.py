"""
URLs para el módulo de rutas.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.ruta_listar, name='ruta_listar'),
    path('crear/', views.ruta_crear, name='ruta_crear'),
    path('<int:pk>/', views.ruta_detalle, name='ruta_detalle'),
    path('<int:pk>/editar/', views.ruta_editar, name='ruta_editar'),
    path('<int:pk>/agregar-cliente/', views.ruta_agregar_cliente, name='ruta_agregar_cliente'),
    path('<int:pk>/eliminar-cliente/<int:detalle_id>/', views.ruta_eliminar_cliente, name='ruta_eliminar_cliente'),
    path('<int:pk>/reordenar/', views.ruta_reordenar, name='ruta_reordenar'),
    path('<int:pk>/eliminar/', views.ruta_eliminar, name='ruta_eliminar'),
    path('<int:pk>/activar/', views.ruta_activar, name='ruta_activar'),
]
