"""
URLs para el módulo de pedidos.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.pedido_listar, name='pedido_listar'),
    path('<int:pk>/', views.pedido_detalle, name='pedido_detalle'),
    path('<int:pk>/cambiar-estado/', views.pedido_cambiar_estado, name='pedido_cambiar_estado'),
    path('crear/<int:detalle_id>/', views.pedido_crear, name='pedido_crear'),
    path('pdf/<int:pedido_id>/', views.pedido_pdf, name='pedido_pdf'),
]
