from django.urls import path
from . import views

urlpatterns = [
    path('', views.cliente_listar, name='cliente_listar'),
    path('crear/', views.cliente_crear, name='cliente_crear'),
    path('vendedor/crear/', views.vendedor_crear_cliente, name='vendedor_crear_cliente'),
    path('<int:pk>/editar/', views.cliente_editar, name='cliente_editar'),
    path('<int:pk>/eliminar/', views.cliente_eliminar, name='cliente_eliminar'),
    path('<int:pk>/activar/', views.cliente_activar, name='cliente_activar'),
]
