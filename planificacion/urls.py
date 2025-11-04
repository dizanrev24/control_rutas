from django.urls import path
from . import views

urlpatterns = [
    # Planificación del vendedor
    path('mi-dia/', views.planificacion_vendedor_dia, name='planificacion_vendedor_dia'),
    path('crear-cliente-nuevo/', views.vendedor_crear_cliente_nuevo, name='vendedor_crear_cliente_nuevo'),
    
    # Flujo de visitas
    path('<int:planificacion_id>/iniciar-visita/', views.iniciar_visita, name='iniciar_visita'),
    path('detalle/<int:detalle_id>/continuar/', views.continuar_visita, name='continuar_visita'),
    path('detalle/<int:detalle_id>/dentro/', views.dentro_visita, name='dentro_visita'),
    path('detalle/<int:detalle_id>/finalizar/', views.finalizar_visita, name='finalizar_visita'),
    path('<int:planificacion_id>/marcar-no-visitado/', views.marcar_no_visitado, name='marcar_no_visitado'),
]
