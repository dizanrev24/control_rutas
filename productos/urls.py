"""
URLs para el módulo de productos.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.producto_listar, name='producto_listar'),
    path('crear/', views.producto_crear, name='producto_crear'),
    path('editar/<int:pk>/', views.producto_editar, name='producto_editar'),
    path('eliminar/<int:pk>/', views.producto_eliminar, name='producto_eliminar'),
    path('activar/<int:pk>/', views.producto_activar, name='producto_activar'),
    path('categorias/', views.categoria_lista, name='categoria_lista'),
    path('categorias/crear/', views.categoria_crear, name='categoria_crear'),
    path('categorias/<int:pk>/editar/', views.categoria_editar, name='categoria_editar'),
    path('categorias/<int:pk>/eliminar/', views.categoria_eliminar, name='categoria_eliminar')
]

