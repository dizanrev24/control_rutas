"""
Vistas para el módulo de asignaciones.

Gestiona la asignación de rutas a vendedores y la generación de planificaciones diarias.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Asignacion
from .forms import AsignacionForm, AsignacionFiltroForm
from planificacion.models import Planificacion, DetallePlanificacion
from rutas.models import RutaDetalle


@login_required
def asignacion_listar(request):
    """
    Lista todas las asignaciones con filtros y paginación.
    
    Accesible para: Admin y Secretaría
    
    Filtros:
    - vendedor: Vendedor específico
    - ruta: Ruta específica
    - estado: Activas/Finalizadas/Todas
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Template con lista de asignaciones
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para gestionar asignaciones.')
        return redirect('home')
    
    # Obtener todas las asignaciones
    asignaciones = Asignacion.objects.select_related(
        'ruta',
        'vendedor'
    ).order_by('-fecha_inicio')
    
    # Aplicar filtros
    filtro_form = AsignacionFiltroForm(request.GET)
    
    if filtro_form.is_valid():
        vendedor = filtro_form.cleaned_data.get('vendedor')
        if vendedor:
            asignaciones = asignaciones.filter(vendedor=vendedor)
        
        ruta = filtro_form.cleaned_data.get('ruta')
        if ruta:
            asignaciones = asignaciones.filter(ruta=ruta)
        
        estado = filtro_form.cleaned_data.get('estado')
        if estado == 'activas':
            hoy = timezone.now().date()
            asignaciones = asignaciones.filter(
                Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=hoy)
            ).filter(fecha_inicio__lte=hoy)
        elif estado == 'finalizadas':
            hoy = timezone.now().date()
            asignaciones = asignaciones.filter(fecha_fin__lt=hoy)
    
    # Paginación
    paginator = Paginator(asignaciones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'total_asignaciones': asignaciones.count(),
    }
    
    return render(request, 'asignaciones/asignacion_list.html', context)


@login_required
def asignacion_crear(request):
    """
    Crea una nueva asignación de ruta a vendedor.
    
    Genera automáticamente las planificaciones diarias para cada cliente de la ruta.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Formulario o redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para crear asignaciones.')
        return redirect('home')
    
    if request.method == 'POST':
        form = AsignacionForm(request.POST)
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    asignacion = form.save()
                    
                    # Generar planificaciones diarias
                    clientes_generados = generar_planificaciones(asignacion)
                    
                    messages.success(
                        request,
                        f'Asignación creada exitosamente. '
                        f'Se generaron planificaciones para {clientes_generados} visitas de clientes.'
                    )
                    return redirect('asignacion_listar')
            
            except Exception as e:
                messages.error(request, f'Error al crear la asignación: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = AsignacionForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Asignación',
    }
    
    return render(request, 'asignaciones/asignacion_form.html', context)


@login_required
def asignacion_detalle(request, pk):
    """
    Muestra el detalle de una asignación con sus planificaciones.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la asignación
    
    Returns:
        HttpResponse: Template con detalle de asignación
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver asignaciones.')
        return redirect('home')
    
    asignacion = get_object_or_404(
        Asignacion.objects.select_related('ruta', 'vendedor'),
        pk=pk
    )
    
    # Obtener planificaciones de esta asignación
    planificaciones = Planificacion.objects.filter(
        asignacion=asignacion
    ).select_related('ruta_detalle__cliente').prefetch_related('detalles_visita').order_by('-fecha')[:30]
    
    # Estadísticas
    total_planificaciones = Planificacion.objects.filter(asignacion=asignacion).count()
    
    context = {
        'asignacion': asignacion,
        'planificaciones': planificaciones,
        'total_planificaciones': total_planificaciones,
    }
    
    return render(request, 'asignaciones/asignacion_detalle.html', context)


@login_required
def asignacion_finalizar(request, pk):
    """
    Finaliza una asignación estableciendo fecha_fin a hoy.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la asignación
    
    Returns:
        HttpResponse: Redirección con mensaje
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para finalizar asignaciones.')
        return redirect('home')
    
    asignacion = get_object_or_404(Asignacion, pk=pk)
    
    if request.method == 'POST':
        if asignacion.fecha_fin:
            messages.warning(request, 'Esta asignación ya está finalizada.')
        else:
            # Finalizar asignación
            asignacion.fecha_fin = timezone.now().date()
            asignacion.save()
            
            # Desactivar vendedor
            vendedor = asignacion.vendedor
            vendedor.activo = False
            vendedor.is_active = False  # También Django's built-in flag
            vendedor.save()
            
            messages.success(
                request,
                f'Asignación finalizada y vendedor {vendedor.get_full_name() or vendedor.username} desactivado correctamente.'
            )
        
        return redirect('asignacion_listar')
    
    # Si no es POST, redirigir
    messages.warning(request, 'Método no permitido.')
    return redirect('asignacion_listar')

@login_required
def asignacion_regenerar_planificaciones(request, pk):
    """
    Regenera las planificaciones para una asignación.
    
    Útil cuando se modifican los clientes de la ruta.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la asignación
    
    Returns:
        HttpResponse: Redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para regenerar planificaciones.')
        return redirect('home')
    
    asignacion = get_object_or_404(Asignacion, pk=pk)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # Eliminar planificaciones futuras no visitadas
                hoy = timezone.now().date()
                
                # Obtener planificaciones futuras
                planificaciones_futuras = Planificacion.objects.filter(
                    asignacion=asignacion,
                    fecha__gte=hoy
                )
                
                # Filtrar solo las que no han sido visitadas
                planificaciones_a_eliminar = []
                for planificacion in planificaciones_futuras:
                    # Verificar si tiene detalles con visita registrada
                    tiene_visita = planificacion.detalles.filter(
                        hora_llegada__isnull=False
                    ).exists()
                    
                    if not tiene_visita:
                        planificaciones_a_eliminar.append(planificacion.pk)
                
                # Eliminar planificaciones
                planificaciones_eliminadas = Planificacion.objects.filter(
                    pk__in=planificaciones_a_eliminar
                ).delete()[0]
                
                # Regenerar planificaciones
                clientes_generados = generar_planificaciones(asignacion, desde_fecha=hoy)
                
                messages.success(
                    request,
                    f'Planificaciones regeneradas exitosamente. '
                    f'Eliminadas: {planificaciones_eliminadas}, '
                    f'Generadas: {clientes_generados} nuevas visitas.'
                )
        
        except Exception as e:
            messages.error(request, f'Error al regenerar planificaciones: {str(e)}')
        
        return redirect('asignacion_detalle', pk=pk)
    
    # Si no es POST, mostrar confirmación
    context = {
        'asignacion': asignacion,
    }
    return render(request, 'asignaciones/asignacion_confirmar_regenerar.html', context)


def generar_planificaciones(asignacion, desde_fecha=None):
    """
    Función auxiliar que genera planificaciones diarias para una asignación.
    
    Crea registros de Planificacion para cada día desde fecha_inicio
    hasta fecha_fin (o 30 días si es indefinida).
    
    Args:
        asignacion: Instancia de Asignacion
        desde_fecha: Fecha desde donde generar (default: fecha_inicio de asignación)
    
    Returns:
        int: Número de visitas de clientes generadas
    """
    if not desde_fecha:
        desde_fecha = asignacion.fecha_inicio
    
    # Determinar hasta qué fecha generar
    if asignacion.fecha_fin:
        hasta_fecha = asignacion.fecha_fin
    else:
        # Generar 30 días hacia adelante para asignaciones indefinidas
        hasta_fecha = desde_fecha + timedelta(days=30)
    
    # Obtener clientes de la ruta ordenados
    clientes_ruta = RutaDetalle.objects.filter(
        ruta=asignacion.ruta
    ).select_related('cliente').order_by('orden_visita')
    
    if not clientes_ruta.exists():
        raise Exception('La ruta no tiene clientes asignados.')
    
    # Generar planificaciones para cada día
    fecha_actual = desde_fecha
    clientes_generados = 0
    
    while fecha_actual <= hasta_fecha:
        # Verificar si ya existe planificación para esta asignación y fecha
        for ruta_detalle in clientes_ruta:
            planificacion, created = Planificacion.objects.get_or_create(
                asignacion=asignacion,
                ruta_detalle=ruta_detalle,
                fecha=fecha_actual,
                defaults={
                    'tipo': 'planificado'
                }
            )
            
            if created:
                # Crear DetallePlanificacion (inicialmente sin visita)
                DetallePlanificacion.objects.get_or_create(
                    planificacion=planificacion
                )
                clientes_generados += 1
        
        # Avanzar al siguiente día
        fecha_actual += timedelta(days=1)
    
    return clientes_generados