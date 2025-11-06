"""
Vistas para el módulo de camiones.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from .models import Camion, AsignacionCamionRuta, CargaCamion, CargaCamionDetalle, CuadreDiario, CuadreDiarioDetalle
from ventas.models import Venta
from pedidos.models import Pedido
from .forms import CamionForm, CamionFiltroForm, AsignacionCamionRutaForm, CargaCamionForm, CargaCamionDetalleForm, CuadreDiarioDetalleForm


# ==================== CRUD CAMIONES ====================

@login_required
def camion_listar(request):
    """Lista todos los camiones con filtros."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para gestionar camiones.')
        return redirect('home')
    
    camiones = Camion.objects.all().order_by('placa')
    
    # Aplicar filtros
    filtro_form = CamionFiltroForm(request.GET)
    
    if filtro_form.is_valid():
        buscar = filtro_form.cleaned_data.get('buscar')
        if buscar:
            camiones = camiones.filter(
                Q(placa__icontains=buscar) |
                Q(marca__icontains=buscar) |
                Q(modelo__icontains=buscar)
            )
        
        activo = filtro_form.cleaned_data.get('activo')
        if activo == 'true':
            camiones = camiones.filter(activo=True)
        elif activo == 'false':
            camiones = camiones.filter(activo=False)
    
    # Paginación
    paginator = Paginator(camiones, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filtro_form': filtro_form,
        'total_camiones': camiones.count(),
    }
    
    return render(request, 'camiones/camion_list.html', context)


@login_required
def camion_crear(request):
    """Crea un nuevo camión."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para crear camiones.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CamionForm(request.POST)
        if form.is_valid():
            camion = form.save()
            messages.success(request, f'Camión {camion.placa} creado exitosamente.')
            return redirect('camion_listar')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CamionForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Camión',
    }
    
    return render(request, 'camiones/camion_form.html', context)


@login_required
def camion_editar(request, pk):
    """Edita un camión existente."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para editar camiones.')
        return redirect('home')
    
    camion = get_object_or_404(Camion, pk=pk)
    
    if request.method == 'POST':
        form = CamionForm(request.POST, instance=camion)
        if form.is_valid():
            camion = form.save()
            messages.success(request, f'Camión {camion.placa} actualizado exitosamente.')
            return redirect('camion_listar')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CamionForm(instance=camion)
    
    context = {
        'form': form,
        'titulo': f'Editar Camión {camion.placa}',
        'camion': camion,
    }
    
    return render(request, 'camiones/camion_form.html', context)


@login_required
def camion_detalle(request, pk):
    """Muestra el detalle de un camión con sus asignaciones."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver detalles de camiones.')
        return redirect('home')
    
    camion = get_object_or_404(Camion, pk=pk)
    asignaciones = camion.asignaciones_rutas.select_related('ruta').order_by('-fecha_inicio')[:10]
    cargas = camion.cargas.select_related('asignacion_camion_ruta__ruta').order_by('-fecha')[:10]
    
    context = {
        'camion': camion,
        'asignaciones': asignaciones,
        'cargas': cargas,
    }
    
    return render(request, 'camiones/camion_detalle.html', context)


@login_required
def camion_eliminar(request, pk):
    """Desactiva un camión (soft delete)."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para eliminar camiones.')
        return redirect('home')
    
    camion = get_object_or_404(Camion, pk=pk)
    camion.activo = False
    camion.save()
    
    messages.success(request, f'Camión {camion.placa} desactivado correctamente.')
    return redirect('camion_listar')


@login_required
def camion_activar(request, pk):
    """Activa un camión."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para activar camiones.')
        return redirect('home')
    
    camion = get_object_or_404(Camion, pk=pk)
    camion.activo = True
    camion.save()
    
    messages.success(request, f'Camión {camion.placa} activado correctamente.')
    return redirect('camion_listar')


# ==================== CARGAS DIARIAS ====================

@login_required
def carga_diaria_listar(request):
    """Lista todas las cargas diarias."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver cargas diarias.')
        return redirect('home')
    
    cargas = CargaCamion.objects.select_related(
        'camion',
        'asignacion_camion_ruta__ruta'
    ).order_by('-fecha', '-hora_carga')
    
    # Paginación
    paginator = Paginator(cargas, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_cargas': cargas.count(),
    }
    
    return render(request, 'camiones/carga_list.html', context)


@login_required
def carga_diaria_crear(request):
    """Crea una nueva carga diaria."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para crear cargas diarias.')
        return redirect('home')
    
    if request.method == 'POST':
        form = CargaCamionForm(request.POST)
        if form.is_valid():
            try:
                carga = form.save()
                messages.success(
                    request,
                    f'Carga creada exitosamente. Ahora agrega los productos.'
                )
                return redirect('carga_diaria_agregar_producto', pk=carga.pk)
            except Exception as e:
                messages.error(request, f'Error al crear la carga: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CargaCamionForm()
    
    context = {
        'form': form,
        'titulo': 'Registrar Carga Diaria',
    }
    
    return render(request, 'camiones/carga_form.html', context)


@login_required
def carga_diaria_detalle(request, pk):
    """Muestra el detalle de una carga con sus productos."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver detalles de cargas.')
        return redirect('home')
    
    carga = get_object_or_404(
        CargaCamion.objects.select_related(
            'camion',
            'asignacion_camion_ruta__ruta'
        ),
        pk=pk
    )
    detalles = carga.detalles.select_related('producto').order_by('producto__nombre')
    
    context = {
        'carga': carga,
        'detalles': detalles,
    }
    
    return render(request, 'camiones/carga_detalle.html', context)


@login_required
def carga_diaria_agregar_producto(request, pk):
    """Agrega un producto a la carga."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para agregar productos a cargas.')
        return redirect('home')
    
    carga = get_object_or_404(CargaCamion, pk=pk)
    
    if carga.cerrado:
        messages.warning(request, 'Esta carga ya está cerrada. No se pueden agregar más productos.')
        return redirect('carga_diaria_detalle', pk=pk)
    
    if request.method == 'POST':
        form = CargaCamionDetalleForm(request.POST, carga_camion=carga)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.carga_camion = carga
            detalle.save()
            messages.success(
                request,
                f'Producto {detalle.producto.nombre} agregado exitosamente.'
            )
            return redirect('carga_diaria_agregar_producto', pk=pk)
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = CargaCamionDetalleForm(carga_camion=carga)
    
    detalles = carga.detalles.select_related('producto').order_by('producto__nombre')
    
    context = {
        'form': form,
        'carga': carga,
        'detalles': detalles,
        'titulo': f'Agregar Productos - {carga.camion.placa}',
    }
    
    return render(request, 'camiones/carga_agregar_producto.html', context)


@login_required
def carga_diaria_eliminar_producto(request, carga_pk, detalle_pk):
    """Elimina un producto de la carga."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para eliminar productos de cargas.')
        return redirect('home')
    
    carga = get_object_or_404(CargaCamion, pk=carga_pk)
    
    if carga.cerrado:
        messages.warning(request, 'Esta carga ya está cerrada. No se pueden eliminar productos.')
        return redirect('carga_diaria_detalle', pk=carga_pk)
    
    detalle = get_object_or_404(CargaCamionDetalle, pk=detalle_pk, carga_camion=carga)
    producto_nombre = detalle.producto.nombre
    detalle.delete()
    
    messages.success(request, f'Producto {producto_nombre} eliminado de la carga.')
    return redirect('carga_diaria_agregar_producto', pk=carga_pk)


@login_required
def carga_diaria_cerrar(request, pk):
    """Cierra la carga para que no se puedan agregar más productos."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para cerrar cargas.')
        return redirect('home')
    
    carga = get_object_or_404(CargaCamion, pk=pk)
    
    if not carga.detalles.exists():
        messages.error(request, 'No se puede cerrar una carga sin productos.')
        return redirect('carga_diaria_agregar_producto', pk=pk)
    
    carga.cerrado = True
    carga.save()
    
    messages.success(
        request,
        f'Carga cerrada exitosamente. Total productos: {carga.total_productos_cargados}'
    )
    return redirect('carga_diaria_detalle', pk=pk)


# ==================== CUADRES DIARIOS ====================

@login_required
def cuadre_diario_listar(request):
    """Lista todos los cuadres diarios."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver cuadres diarios.')
        return redirect('home')
    
    cuadres = CuadreDiario.objects.select_related(
        'carga_camion__camion',
        'carga_camion__asignacion_camion_ruta__ruta'
    ).order_by('-fecha_cuadre')
    
    # Paginación
    paginator = Paginator(cuadres, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_cuadres': cuadres.count(),
    }
    
    return render(request, 'camiones/cuadre_list.html', context)


@login_required
def cuadre_diario_crear(request, carga_pk):
    """Crea un cuadre para una carga específica."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para crear cuadres.')
        return redirect('home')
    
    carga = get_object_or_404(CargaCamion, pk=carga_pk)
    
    if not carga.cerrado:
        messages.error(request, 'La carga debe estar cerrada antes de crear un cuadre.')
        return redirect('carga_diaria_detalle', pk=carga_pk)
    
    if hasattr(carga, 'cuadre'):
        messages.warning(request, 'Ya existe un cuadre para esta carga.')
        return redirect('cuadre_diario_detalle', pk=carga.cuadre.pk)
    
    try:
        with transaction.atomic():
            # Crear cuadre
            cuadre = CuadreDiario.objects.create(
                carga_camion=carga,
                estado='pendiente'
            )
            
            # Crear detalles basados en la carga
            for detalle_carga in carga.detalles.all():
                CuadreDiarioDetalle.objects.create(
                    cuadre=cuadre,
                    producto=detalle_carga.producto,
                    cantidad_cargada=detalle_carga.cantidad_cargada,
                    cantidad_vendida=detalle_carga.cantidad_vendida,
                    cantidad_esperada=detalle_carga.cantidad_actual,
                    cantidad_real_retorno=detalle_carga.cantidad_actual,  # Inicialmente igual
                )
            
            messages.success(request, 'Cuadre creado exitosamente. Registra las cantidades reales.')
            return redirect('cuadre_diario_detalle', pk=cuadre.pk)
    
    except Exception as e:
        messages.error(request, f'Error al crear el cuadre: {str(e)}')
        return redirect('carga_diaria_detalle', pk=carga_pk)


@login_required
def cuadre_diario_detalle(request, pk):
    """Muestra y permite editar el cuadre diario."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver cuadres.')
        return redirect('home')
    
    cuadre = get_object_or_404(
        CuadreDiario.objects.select_related(
            'carga_camion__camion',
            'carga_camion__asignacion_camion_ruta__ruta'
        ),
        pk=pk
    )
    detalles = cuadre.detalles.select_related('producto').order_by('producto__nombre')
    
    # Calcular totales
    total_diferencias = sum(d.diferencia for d in detalles)
    tiene_diferencias = any(d.diferencia != 0 for d in detalles)

    # Resumen de ventas y pedidos del día para la ruta/camión
    carga = cuadre.carga_camion
    ruta = carga.asignacion_camion_ruta.ruta if carga.asignacion_camion_ruta else None
    fecha = carga.fecha

    ventas_qs = Venta.objects.filter(carga_camion=carga, fecha__date=fecha)
    ventas_total = ventas_qs.aggregate(total=Sum('total'))['total'] or 0
    ventas_count = ventas_qs.count()

    pedidos_qs = Pedido.objects.filter(
        detalle_planificacion__planificacion__fecha=fecha
    )
    if ruta:
        pedidos_qs = pedidos_qs.filter(
            detalle_planificacion__planificacion__asignacion__ruta=ruta
        )
    pedidos_total = pedidos_qs.aggregate(total=Sum('total'))['total'] or 0
    pedidos_count = pedidos_qs.count()
    
    context = {
        'cuadre': cuadre,
        'detalles': detalles,
        'total_diferencias': total_diferencias,
        'tiene_diferencias': tiene_diferencias,
        'ventas_total': ventas_total,
        'ventas_count': ventas_count,
        'pedidos_total': pedidos_total,
        'pedidos_count': pedidos_count,
    }
    
    return render(request, 'camiones/cuadre_detalle.html', context)


@login_required
def cuadre_diario_actualizar_detalle(request, cuadre_pk, detalle_pk):
    """Actualiza la cantidad real de retorno de un producto en el cuadre."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para actualizar cuadres.')
        return redirect('home')
    
    cuadre = get_object_or_404(CuadreDiario, pk=cuadre_pk)
    detalle = get_object_or_404(CuadreDiarioDetalle, pk=detalle_pk, cuadre=cuadre)
    
    if request.method == 'POST':
        form = CuadreDiarioDetalleForm(request.POST, instance=detalle)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'Cantidad real de {detalle.producto.nombre} actualizada.'
            )
            return redirect('cuadre_diario_detalle', pk=cuadre_pk)
    else:
        form = CuadreDiarioDetalleForm(instance=detalle)
    
    context = {
        'form': form,
        'cuadre': cuadre,
        'detalle': detalle,
        'titulo': f'Actualizar {detalle.producto.nombre}',
    }
    
    return render(request, 'camiones/cuadre_actualizar_detalle.html', context)


@login_required
def cuadre_diario_finalizar(request, pk):
    """Finaliza el cuadre y actualiza el estado según las diferencias."""
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para finalizar cuadres.')
        return redirect('home')
    
    cuadre = get_object_or_404(CuadreDiario, pk=pk)
    
    # Verificar si hay diferencias
    detalles = cuadre.detalles.all()
    tiene_diferencias = any(d.diferencia != 0 for d in detalles)
    
    if tiene_diferencias:
        cuadre.estado = 'con_diferencia'
    else:
        cuadre.estado = 'cuadrado'
    
    cuadre.save()
    
    messages.success(
        request,
        f'Cuadre finalizado. Estado: {cuadre.get_estado_display()}'
    )
    return redirect('cuadre_diario_detalle', pk=pk)
