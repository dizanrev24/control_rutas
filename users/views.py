from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout
from django.views.decorators.http import require_POST
from .models import Usuario
from .forms import UsuarioCrearForm, UsuarioActualizarForm, LoginForm


# Vista de Login
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'¡Bienvenido {user.get_full_name() or user.username}!')
                return redirect('home')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})


@login_required
@require_POST
def logout_view(request):
    logout(request)
    messages.success(request, "Has cerrado sesión correctamente.")
    return redirect('login')  # redirige a la página de login

# Vista Home/Dashboard
@login_required
def home_view(request):
    """
    Dashboard diferenciado por rol:
    - Admin: métricas generales del sistema
    - Secretaria: métricas de ventas y pedidos
    - Vendedor: redirige a su planificación del día
    """
    user = request.user
    
    # Si es vendedor, redirige a su planificación
    if user.es_vendedor:
        return redirect('planificacion_vendedor_dia')
    
    # Dashboard para admin y secretaria
    context = {}
    
    if user.es_admin or user.puede_gestionar_rutas:
        from clientes.models import Cliente
        from rutas.models import Ruta
        from asignaciones.models import Asignacion
        from ventas.models import Venta
        from pedidos.models import Pedido
        from datetime import datetime, timedelta
        from django.db.models import Sum, Count
        
        # Métricas generales
        context['total_usuarios'] = Usuario.objects.filter(is_active=True).count()
        context['total_clientes'] = Cliente.objects.filter(activo=True).count()
        context['total_rutas'] = Ruta.objects.filter(activo=True).count()
        context['total_vendedores'] = Usuario.objects.filter(rol='vendedor', is_active=True).count()
        
        # Asignaciones activas
        asignaciones_activas = []
        for asig in Asignacion.objects.all():
            if asig.esta_activa:
                asignaciones_activas.append(asig)
        context['asignaciones_activas'] = len(asignaciones_activas)
        
        # Métricas de ventas (últimos 30 días)
        fecha_hace_30 = datetime.now().date() - timedelta(days=30)
        ventas_mes = Venta.objects.filter(fecha__gte=fecha_hace_30)
        context['ventas_mes_count'] = ventas_mes.count()
        context['ventas_mes_total'] = ventas_mes.aggregate(
            total=Sum('total')
        )['total'] or 0
        
        # Métricas de pedidos (últimos 30 días)
        pedidos_mes = Pedido.objects.filter(fecha__gte=fecha_hace_30)
        context['pedidos_mes_count'] = pedidos_mes.count()
        context['pedidos_por_estado'] = pedidos_mes.values('estado').annotate(
            count=Count('id')
        ).order_by('estado')
        
        # Si es solo secretaria, no mostrar gestión de usuarios
        if user.rol == 'secretaria':
            context['es_secretaria'] = True
    
    return render(request, 'home.html', context)


# Crear Usuario (Solo Admin)
class UsuarioCrearView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCrearForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_listar')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario creado exitosamente!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el usuario. Verifique los datos.')
        return super().form_invalid(form)


# Actualizar Usuario (Solo Admin)
class UsuarioActualizarView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioActualizarForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_listar')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario actualizado exitosamente!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el usuario. Verifique los datos.')
        return super().form_invalid(form)


# Listar Usuarios Activos (Solo Admin)
class UsuarioListarView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Usuario.objects.filter(is_active=True).order_by('-date_joined')


# Listar Usuarios Inactivos (Solo Admin)
class UsuarioInactivosView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/usuario_inactivos.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        if not request.user.es_admin:
            messages.error(request, 'No tienes permiso para acceder a esta sección.')
            return redirect('home')
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Usuario.objects.filter(is_active=False).order_by('-date_joined')


# Activar/Desactivar Usuario (Solo Admin)
@login_required
def usuario_toggle_estado(request, pk):
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('home')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    estado = "activado" if usuario.is_active else "desactivado"
    messages.success(request, f'Usuario {estado} exitosamente.')
    
    # Redirigir según el estado
    if usuario.is_active:
        return redirect('usuario_listar')
    else:
        return redirect('usuario_inactivos')


# Eliminar Usuario (Solo Admin - soft delete)
@login_required
def usuario_eliminar(request, pk):
    if not request.user.es_admin:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('home')
    
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = False
    usuario.save()
    messages.success(request, 'Usuario desactivado exitosamente.')
    return redirect('usuario_listar')
