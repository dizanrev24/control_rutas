from django.urls import path
from django.contrib.auth.views import LogoutView
from django.urls import reverse_lazy
from . import views

urlpatterns = [
    # Login y Logout
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Home
    path('', views.home_view, name='home'),
    
    # Usuarios
    path('usuarios/', views.UsuarioListarView.as_view(), name='usuario_listar'),
    path('usuarios/inactivos/', views.UsuarioInactivosView.as_view(), name='usuario_inactivos'),
    path('usuarios/crear/', views.UsuarioCrearView.as_view(), name='usuario_crear'),
    path('usuarios/<int:pk>/editar/', views.UsuarioActualizarView.as_view(), name='usuario_editar'),
    path('usuarios/<int:pk>/toggle/', views.usuario_toggle_estado, name='usuario_toggle'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
]