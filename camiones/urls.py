"""
URLs para el módulo de camiones.
"""
from django.urls import path
from . import views

urlpatterns = [
    # CRUD Camiones
    path('', views.camion_listar, name='camion_listar'),
    path('crear/', views.camion_crear, name='camion_crear'),
    path('<int:pk>/', views.camion_detalle, name='camion_detalle'),
    path('<int:pk>/editar/', views.camion_editar, name='camion_editar'),
    path('<int:pk>/eliminar/', views.camion_eliminar, name='camion_eliminar'),
    path('<int:pk>/activar/', views.camion_activar, name='camion_activar'),
    
    # Cargas Diarias
    path('cargas/', views.carga_diaria_listar, name='carga_diaria_listar'),
    path('cargas/crear/', views.carga_diaria_crear, name='carga_diaria_crear'),
    path('cargas/<int:pk>/', views.carga_diaria_detalle, name='carga_diaria_detalle'),
    path('cargas/<int:pk>/agregar-producto/', views.carga_diaria_agregar_producto, name='carga_diaria_agregar_producto'),
    path('cargas/<int:carga_pk>/eliminar-producto/<int:detalle_pk>/', views.carga_diaria_eliminar_producto, name='carga_diaria_eliminar_producto'),
    path('cargas/<int:pk>/cerrar/', views.carga_diaria_cerrar, name='carga_diaria_cerrar'),
    
    # Cuadres Diarios
    path('cuadres/', views.cuadre_diario_listar, name='cuadre_diario_listar'),
    path('cuadres/crear/<int:carga_pk>/', views.cuadre_diario_crear, name='cuadre_diario_crear'),
    path('cuadres/<int:pk>/', views.cuadre_diario_detalle, name='cuadre_diario_detalle'),
    path('cuadres/<int:cuadre_pk>/actualizar-detalle/<int:detalle_pk>/', views.cuadre_diario_actualizar_detalle, name='cuadre_diario_actualizar_detalle'),
    path('cuadres/<int:pk>/finalizar/', views.cuadre_diario_finalizar, name='cuadre_diario_finalizar'),
]
