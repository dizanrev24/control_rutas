"""
Vistas para el módulo de pedidos.
Gestiona la creación de pedidos (sin descuento de stock) durante las visitas y la generación de PDFs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Sum, Count, Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from .models import Pedido, DetallePedido
from .forms import PedidoForm, DetallePedidoFormSet
from planificacion.models import DetallePlanificacion
from core.utils import generar_pdf_pedido
from productos.models import Producto
from decimal import Decimal
from django.contrib.auth import get_user_model
from clientes.models import Cliente
import logging

logger = logging.getLogger(__name__)


@login_required
def pedido_crear(request, detalle_id):
    """
    Crea un nuevo pedido durante una visita activa.
    
    Los pedidos NO descargan stock del camión (son para entrega futura).
    
    Valida que:
    - El usuario sea vendedor
    - La visita esté activa (hora_llegada existe, hora_salida no)
    
    Al confirmar:
    - Crea Pedido con estado 'pendiente'
    - Crea DetallePedido para cada producto
    - NO afecta el stock del camión
    
    Args:
        request: HttpRequest
        detalle_id: ID del DetallePlanificacion de la visita activa
    
    Returns:
        HttpResponse: Formulario o redirección
    """
    detalle_planificacion = get_object_or_404(
        DetallePlanificacion.objects.select_related(
            'planificacion__asignacion__vendedor',
            'planificacion__ruta_detalle__cliente'
        ),
        id=detalle_id
    )
    
    # Validar que el usuario sea el vendedor asignado
    if not request.user.es_vendedor:
        messages.error(request, 'Solo los vendedores pueden crear pedidos.')
        return redirect('home')
    
    if detalle_planificacion.planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para crear pedidos en esta visita.')
        return redirect('planificacion_vendedor_dia')
    
    # Validar que la visita esté activa
    if not detalle_planificacion.hora_llegada or detalle_planificacion.hora_salida:
        messages.error(request, 'La visita debe estar activa para crear pedidos.')
        return redirect('planificacion_vendedor_dia')
    
    cliente = detalle_planificacion.planificacion.ruta_detalle.cliente
    
    if request.method == 'POST':
        pedido_form = PedidoForm(request.POST)
        formset = DetallePedidoFormSet(request.POST, prefix='detalles')
        
        logger.debug("POST pedido_crear detalle_id=%s data_keys=%s", detalle_id, list(request.POST.keys()))
        if pedido_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear pedido
                    pedido = pedido_form.save(commit=False)
                    pedido.detalle_planificacion = detalle_planificacion
                    pedido.cliente = cliente
                    pedido.estado = 'pendiente'  # Estado inicial
                    # Inicializar total para cumplir con NOT NULL en BD
                    pedido.total = Decimal('0.00')
                    pedido.save()
                    
                    # Crear detalles (sin afectar stock)
                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                            detalle = form.save(commit=False)
                            detalle.pedido = pedido
                            detalle.save()

                    # Actualizar total del pedido
                    pedido.total = pedido.calcular_total()
                    pedido.save(update_fields=['total'])
                    
                    logger.info("Pedido creado id=%s total=%s detalles=%s", pedido.id, pedido.total, pedido.detalles.count())
                    messages.success(
                        request,
                        f'Pedido #{pedido.id} creado exitosamente. '
                        f'Total: Q{pedido.calcular_total():.2f}'
                    )
                    return redirect('dentro_visita', detalle_id=detalle_id)
            
            except Exception as e:
                logger.exception("Error creando pedido para detalle_planificacion=%s", detalle_id)
                messages.error(request, f'Error al crear el pedido: {str(e)}')
        else:
            logger.error("Errores en pedido_form: %s", pedido_form.errors.as_json())
            logger.error("Errores en formset (non_form): %s", formset.non_form_errors())
            for i, f in enumerate(formset.forms):
                if f.errors:
                    logger.error("Formset[%s] errors: %s", i, f.errors.as_json())
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    
    else:
        pedido_form = PedidoForm()
        formset = DetallePedidoFormSet(queryset=DetallePedido.objects.none(), prefix='detalles')
    
    context = {
        'pedido_form': pedido_form,
        'formset': formset,
        'detalle_planificacion': detalle_planificacion,
        'cliente': cliente,
        # Catálogo completo para UI de cotización/pedido
        'productos_catalogo': Producto.objects.filter(estado='activo').order_by('nombre'),
    }
    
    return render(request, 'pedidos/pedido_form.html', context)


@login_required
def pedido_pdf(request, pedido_id):
    """
    Genera PDF de un pedido.
    
    Accesible para:
    - El vendedor que creó el pedido
    - Admin y secretaría
    
    Args:
        request: HttpRequest
        pedido_id: ID del pedido
    
    Returns:
        HttpResponse: PDF como attachment o error
    """
    pedido = get_object_or_404(
        Pedido.objects.select_related(
            'detalle_planificacion__planificacion__asignacion__vendedor',
            'cliente'
        ).prefetch_related('detalles__producto'),
        id=pedido_id
    )
    
    # Validar permisos
    vendedor_pedido = pedido.detalle_planificacion.planificacion.asignacion.vendedor
    
    if request.user.es_vendedor and request.user != vendedor_pedido:
        messages.error(request, 'No tienes permiso para ver este pedido.')
        return redirect('planificacion_vendedor_dia')
    
    try:
        pdf_content = generar_pdf_pedido(pedido)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="pedido_{pedido.id}.pdf"'
        
        return response
    
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('planificacion_vendedor_dia')


@login_required
def pedido_listar(request):
    """
    Lista todos los pedidos con filtros.
    
    Accesible para: Admin y Secretaría
    
    Filtros:
    - Rango de fechas
    - Estado (pendiente, procesando, entregado, cancelado)
    - Vendedor
    - Cliente
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Template con lista de pedidos
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver todos los pedidos.')
        return redirect('home')
    
    # Obtener todos los pedidos
    pedidos = Pedido.objects.select_related(
        'cliente',
        'detalle_planificacion__planificacion__asignacion__vendedor'
    ).order_by('-fecha')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    estado = request.GET.get('estado')
    vendedor_id = request.GET.get('vendedor') or request.GET.get('vendedor_id')
    cliente_id = request.GET.get('cliente') or request.GET.get('cliente_id')
    
    # Aplicar filtros de fecha (default: últimos 30 días)
    if not fecha_inicio and not fecha_fin:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    if fecha_inicio:
        try:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            pedidos = pedidos.filter(fecha__gte=fecha_inicio)
        except:
            pass
    
    if fecha_fin:
        try:
            fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            pedidos = pedidos.filter(fecha__lte=fecha_fin)
        except:
            pass
    
    if estado:
        pedidos = pedidos.filter(estado=estado)
    
    if vendedor_id:
        pedidos = pedidos.filter(
            detalle_planificacion__planificacion__asignacion__vendedor_id=vendedor_id
        )
    
    if cliente_id:
        pedidos = pedidos.filter(cliente_id=cliente_id)
    
    # Calcular totales
    totales = pedidos.aggregate(
        total_pedidos_sum=Sum('total'),
        cantidad_pedidos=Count('id')
    )
    
    total_neto = totales['total_pedidos_sum'] or 0
    
    # Contar por estado
    # Construir resumen por estado con conteo y suma de totales
    por_estado_qs = pedidos.values('estado').annotate(
        count=Count('id'),
        total=Sum('total')
    )
    por_estado = {item['estado']: {'count': item['count'], 'total': item['total'] or 0} for item in por_estado_qs}
    
    # Paginación
    paginator = Paginator(pedidos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'pedidos': page_obj,  # iterable
        'total_pedidos': totales['cantidad_pedidos'] or 0,
        'total_neto': total_neto,
        'por_estado': por_estado,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'estado_seleccionado': estado,
        'vendedores': get_user_model().objects.filter(rol='vendedor', is_active=True).order_by('first_name', 'last_name'),
        'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
    }
    
    return render(request, 'pedidos/pedido_list.html', context)


@login_required
def pedido_detalle(request, pk):
    """
    Muestra el detalle de un pedido específico.
    
    Args:
        request: HttpRequest
        pk: ID del pedido
    
    Returns:
        HttpResponse: Template con detalle de pedido
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver detalles de pedidos.')
        return redirect('home')
    
    pedido = get_object_or_404(
        Pedido.objects.select_related(
            'cliente',
            'detalle_planificacion__planificacion__asignacion__vendedor',
            'detalle_planificacion__planificacion__ruta_detalle__cliente'
        ).prefetch_related('detalles__producto__categoria'),
        pk=pk
    )
    
    detalles = pedido.detalles.all()
    
    context = {
        'pedido': pedido,
        'detalles': detalles,
    }
    
    return render(request, 'pedidos/pedido_detalle.html', context)


@login_required
def pedido_cambiar_estado(request, pk):
    """
    Cambia el estado de un pedido.
    
    Args:
        request: HttpRequest
        pk: ID del pedido
    
    Returns:
        HttpResponse: Redirección
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para cambiar estados de pedidos.')
        return redirect('home')
    
    pedido = get_object_or_404(Pedido, pk=pk)
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        if nuevo_estado in dict(Pedido.ESTADO_CHOICES):
            pedido.estado = nuevo_estado
            pedido.save()
            messages.success(
                request,
                f'Estado del pedido #{pedido.id} actualizado a {pedido.get_estado_display()}.'
            )
        else:
            messages.error(request, 'Estado inválido.')
    
    return redirect('pedido_detalle', pk=pk)
