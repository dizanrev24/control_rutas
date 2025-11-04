"""from django.shortcuts import render

Vistas para el módulo de rutas.

Gestiona el CRUD de rutas y la asignación de clientes con orden de visita.# Create your views here.

"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from django.db import transaction
from .models import Ruta, RutaDetalle
from .forms import RutaForm, RutaDetalleForm, RutaFiltroForm


@login_required
def ruta_listar(request):
    """
    Lista todas las rutas con filtros y paginación.
    
    Accesible para: Admin y Secretaría
    
    Filtros:
    - buscar: Nombre o descripción
    - activo: Activas/Inactivas/Todas
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Template con lista de rutas
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para gestionar rutas.')
        return redirect('home')
    
    # Obtener todas las rutas con conteo de clientes
    rutas = Ruta.objects.annotate(
        num_clientes=Count('detalles')
    ).order_by('-activo', 'nombre')
    
    # Aplicar filtros
    filtro_form = RutaFiltroForm(request.GET)
    
    if filtro_form.is_valid():
        buscar = filtro_form.cleaned_data.get('buscar')
        if buscar:
            rutas = rutas.filter(
                Q(nombre__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        activo = filtro_form.cleaned_data.get('activo')
        if activo:
            rutas = rutas.filter(activo=(activo == 'true'))
    
    # Paginación
    paginator = Paginator(rutas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'total_rutas': rutas.count(),
    }
    
    return render(request, 'rutas/ruta_list.html', context)


@login_required
def ruta_crear(request):
    """
    Crea una nueva ruta.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Formulario o redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para crear rutas.')
        return redirect('home')
    
    if request.method == 'POST':
        form = RutaForm(request.POST)
        
        if form.is_valid():
            ruta = form.save()
            messages.success(
                request,
                f'Ruta "{ruta.nombre}" creada exitosamente. '
                f'Ahora puedes agregar clientes a esta ruta.'
            )
            return redirect('ruta_detalle', pk=ruta.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RutaForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Ruta',
        'accion': 'Crear',
    }
    
    return render(request, 'rutas/ruta_form.html', context)


@login_required
def ruta_editar(request, pk):
    """
    Edita una ruta existente.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
    
    Returns:
        HttpResponse: Formulario o redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para editar rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    if request.method == 'POST':
        form = RutaForm(request.POST, instance=ruta)
        
        if form.is_valid():
            ruta = form.save()
            messages.success(
                request,
                f'Ruta "{ruta.nombre}" actualizada exitosamente.'
            )
            return redirect('ruta_detalle', pk=ruta.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = RutaForm(instance=ruta)
    
    context = {
        'form': form,
        'ruta': ruta,
        'titulo': f'Editar Ruta: {ruta.nombre}',
        'accion': 'Actualizar',
    }
    
    return render(request, 'rutas/ruta_form.html', context)


@login_required
def ruta_detalle(request, pk):
    """
    Muestra el detalle de una ruta con sus clientes ordenados.
    
    Permite agregar/eliminar clientes y reordenar.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
    
    Returns:
        HttpResponse: Template con detalle de ruta
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    # Obtener clientes de la ruta ordenados
    clientes_ruta = RutaDetalle.objects.filter(ruta=ruta).select_related(
        'cliente'
    ).order_by('orden_visita')
    
    context = {
        'ruta': ruta,
        'clientes_ruta': clientes_ruta,
        'total_clientes': clientes_ruta.count(),
    }
    
    return render(request, 'rutas/ruta_detalle.html', context)


@login_required
def ruta_agregar_cliente(request, pk):
    """
    Agrega un cliente a una ruta con su orden de visita.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
    
    Returns:
        HttpResponse: Formulario o redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para modificar rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    if request.method == 'POST':
        form = RutaDetalleForm(request.POST, ruta=ruta)
        
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.ruta = ruta
            detalle.save()
            
            messages.success(
                request,
                f'Cliente "{detalle.cliente.nombre}" agregado a la ruta en orden {detalle.orden_visita}.'
            )
            return redirect('ruta_detalle', pk=ruta.pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        # Sugerir el siguiente orden disponible
        ultimo_orden = RutaDetalle.objects.filter(ruta=ruta).order_by('-orden_visita').first()
        orden_sugerido = (ultimo_orden.orden_visita + 1) if ultimo_orden else 1
        
        form = RutaDetalleForm(
            ruta=ruta,
            initial={'orden_visita': orden_sugerido}
        )
    
    context = {
        'form': form,
        'ruta': ruta,
        'titulo': f'Agregar Cliente a: {ruta.nombre}',
    }
    
    return render(request, 'rutas/ruta_agregar_cliente.html', context)


@login_required
def ruta_eliminar_cliente(request, pk, detalle_id):
    """
    Elimina un cliente de una ruta.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
        detalle_id: ID del RutaDetalle
    
    Returns:
        HttpResponse: Redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para modificar rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    detalle = get_object_or_404(RutaDetalle, pk=detalle_id, ruta=ruta)
    
    cliente_nombre = detalle.cliente.nombre
    detalle.delete()
    
    messages.success(
        request,
        f'Cliente "{cliente_nombre}" eliminado de la ruta.'
    )
    
    return redirect('ruta_detalle', pk=ruta.pk)


@login_required
def ruta_reordenar(request, pk):
    """
    Reordena los clientes de una ruta.
    
    Recibe un JSON con los IDs en el nuevo orden.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest (POST con JSON)
        pk: ID de la ruta
    
    Returns:
        JsonResponse: Resultado de la operación
    """
    from django.http import JsonResponse
    import json
    
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        return JsonResponse({'success': False, 'error': 'Sin permisos'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    try:
        data = json.loads(request.body)
        orden_ids = data.get('orden', [])
        
        with transaction.atomic():
            for idx, detalle_id in enumerate(orden_ids, start=1):
                RutaDetalle.objects.filter(
                    id=detalle_id,
                    ruta=ruta
                ).update(orden_visita=idx)
        
        return JsonResponse({'success': True})
    
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def ruta_eliminar(request, pk):
    """
    Desactiva una ruta (soft delete).
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
    
    Returns:
        HttpResponse: Redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para eliminar rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    if ruta.activo:
        ruta.activo = False
        ruta.save()
        messages.success(
            request,
            f'Ruta "{ruta.nombre}" desactivada correctamente.'
        )
    else:
        messages.info(request, 'La ruta ya estaba desactivada.')
    
    return redirect('ruta_listar')


@login_required
def ruta_activar(request, pk):
    """
    Activa una ruta previamente desactivada.
    
    Accesible para: Admin y Secretaría
    
    Args:
        request: HttpRequest
        pk: ID de la ruta
    
    Returns:
        HttpResponse: Redirección
    """
    # Validar permisos
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para activar rutas.')
        return redirect('home')
    
    ruta = get_object_or_404(Ruta, pk=pk)
    
    if not ruta.activo:
        ruta.activo = True
        ruta.save()
        messages.success(
            request,
            f'Ruta "{ruta.nombre}" activada correctamente.'
        )
    else:
        messages.info(request, 'La ruta ya estaba activa.')
    
    return redirect('ruta_listar')
