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
    total_usuarios = Usuario.objects.count()
    usuarios_activos = Usuario.objects.filter(is_active=True).count()
    usuarios_inactivos = Usuario.objects.filter(is_active=False).count()
    
    context = {
        'total_usuarios': total_usuarios,
        'usuarios_activos': usuarios_activos,
        'usuarios_inactivos': usuarios_inactivos,
    }
    return render(request, 'home.html', context)


# Crear Usuario
class UsuarioCrearView(LoginRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCrearForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_listar')

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario creado exitosamente!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al crear el usuario. Verifique los datos.')
        return super().form_invalid(form)


# Actualizar Usuario
class UsuarioActualizarView(LoginRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioActualizarForm
    template_name = 'usuarios/usuario_form.html'
    success_url = reverse_lazy('usuario_listar')

    def form_valid(self, form):
        messages.success(self.request, '¡Usuario actualizado exitosamente!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error al actualizar el usuario. Verifique los datos.')
        return super().form_invalid(form)


# Listar Usuarios Activos
class UsuarioListarView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/usuario_list.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return Usuario.objects.filter(is_active=True).order_by('-date_joined')


# Listar Usuarios Inactivos
class UsuarioInactivosView(LoginRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/usuario_inactivos.html'
    context_object_name = 'usuarios'
    paginate_by = 10

    def get_queryset(self):
        return Usuario.objects.filter(is_active=False).order_by('-date_joined')


# Activar/Desactivar Usuario (AJAX)
@login_required
def usuario_toggle_estado(request, pk):
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


# Eliminar Usuario (soft delete - desactivar)
@login_required
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    usuario.is_active = False
    usuario.save()
    messages.success(request, 'Usuario desactivado exitosamente.')
    return redirect('usuario_listar')
