"""
Vistas para el módulo de ventas.

Gestiona la creación de ventas durante las visitas y la generación de PDFs.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Sum, F, Q, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

from asignaciones import models
from .models import Venta, DetalleVenta
from .forms import VentaForm, DetalleVentaFormSet
from planificacion.models import DetallePlanificacion
from camiones.models import AsignacionCamionRuta, CargaCamion
from core.utils import generar_pdf_venta
from clientes.models import Cliente
from django.db.models import Q
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

@login_required
def venta_crear(request, detalle_id):
    """
    Crea una nueva venta durante una visita activa.
    
    Valida que:
    - El usuario sea vendedor
    - La visita esté activa (hora_llegada existe, hora_salida no)
    - Exista carga de camión para la fecha en la ruta
    - Haya stock suficiente en el camión
    
    Al confirmar:
    - Crea Venta con FK a carga_camion
    - Crea DetalleVenta para cada producto
    - Decrementa cantidad_actual en CargaCamionDetalle
    """
    detalle_planificacion = get_object_or_404(
        DetallePlanificacion.objects.select_related(
            'planificacion__asignacion__vendedor',
            'planificacion__asignacion__ruta',
            'planificacion__ruta_detalle__cliente'
        ),
        id=detalle_id
    )
    
    # Validar que el usuario sea el vendedor asignado
    if not request.user.es_vendedor:
        messages.error(request, 'Solo los vendedores pueden crear ventas.')
        return redirect('home')
    
    if detalle_planificacion.planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para crear ventas en esta visita.')
        return redirect('planificacion_vendedor_dia')
    
    # Validar que la visita esté activa
    if not detalle_planificacion.hora_llegada or detalle_planificacion.hora_salida:
        messages.error(request, 'La visita debe estar activa para crear ventas.')
        return redirect('planificacion_vendedor_dia')
    
    # Obtener la ruta y fecha de la visita
    fecha_visita = detalle_planificacion.planificacion.fecha
    ruta = detalle_planificacion.planificacion.asignacion.ruta
    
    try:
        # Buscar asignación de camión activa para la ruta en la fecha
        asignacion_camion = AsignacionCamionRuta.objects.filter(
            ruta=ruta,
            fecha_inicio__lte=fecha_visita,
            activo=True
        ).filter(
            Q(fecha_fin__isnull=True) | Q(fecha_fin__gte=fecha_visita)  # ← Usar Q directamente
        ).first()
        
        if not asignacion_camion:
            messages.error(
                request,
                f'No hay un camión asignado a la ruta {ruta.nombre} para esta fecha.'
            )
            return redirect('dentro_visita', detalle_id=detalle_id)
        
        # Buscar la carga del camión para esa fecha
        carga_camion = CargaCamion.objects.get(
            camion=asignacion_camion.camion,
            fecha=fecha_visita
        )
        
    except CargaCamion.DoesNotExist:
        messages.error(
            request,
            f'No existe carga registrada en el camión {asignacion_camion.camion.placa} '
            f'para la fecha {fecha_visita.strftime("%d/%m/%Y")}. Contacta a la secretaría.'
        )
        return redirect('dentro_visita', detalle_id=detalle_id)
    
    cliente = detalle_planificacion.planificacion.ruta_detalle.cliente
    
    if request.method == 'POST':
        venta_form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(
            request.POST,
            form_kwargs={'carga_camion': carga_camion},
            prefix='detalles'
        )
        
        logger.debug("POST venta_crear detalle_id=%s data_keys=%s", detalle_id, list(request.POST.keys()))
        if venta_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # Crear venta
                    venta = venta_form.save(commit=False)
                    venta.detalle_planificacion = detalle_planificacion
                    venta.cliente = cliente
                    venta.carga_camion = carga_camion
                    # Inicializar total para cumplir con NOT NULL en BD
                    venta.total = Decimal('0.00')
                    venta.save()
                    
                    # Crear detalles y decrementar stock
                    for form in formset:
                        if form.cleaned_data and not form.cleaned_data.get('DELETE'):
                            detalle = form.save(commit=False)
                            detalle.venta = venta
                            detalle.save()
                            
                            # Decrementar stock del camión
                            detalle_carga = carga_camion.detalles.get(
                                producto=detalle.producto
                            )
                            detalle_carga.cantidad_actual -= detalle.cantidad
                            detalle_carga.save()

                    # Actualizar total de la venta
                    venta.total = venta.calcular_total()
                    venta.save(update_fields=['total'])

                    logger.info("Venta creada id=%s total=%s detalles=%s", venta.id, venta.total, venta.detalles.count())
                    messages.success(
                        request,
                        f'Venta #{venta.id} creada exitosamente. '
                        f'Total: Q{venta.calcular_total():.2f}'
                    )
                    return redirect('dentro_visita', detalle_id=detalle_id)
            
            except Exception as e:
                logger.exception("Error creando venta para detalle_planificacion=%s", detalle_id)
                messages.error(request, f'Error al crear la venta: {str(e)}')
        else:
            logger.error("Errores en venta_form: %s", venta_form.errors.as_json())
            logger.error("Errores en formset (non_form): %s", formset.non_form_errors())
            for i, f in enumerate(formset.forms):
                if f.errors:
                    logger.error("Formset[%s] errors: %s", i, f.errors.as_json())
            messages.error(request, 'Por favor corrige los errores en el formulario.')
    
    else:
        venta_form = VentaForm()
        formset = DetalleVentaFormSet(
            queryset=DetalleVenta.objects.none(),
            form_kwargs={'carga_camion': carga_camion},
            prefix='detalles'
        )
    
    context = {
        'venta_form': venta_form,
        'formset': formset,
        'detalle_planificacion': detalle_planificacion,
        'cliente': cliente,
        'carga_camion': carga_camion,
        # Lista de productos cargados en el camión (para UI tipo POS)
        'productos_cargados': carga_camion.detalles.select_related('producto').order_by('producto__nombre'),
    }
    
    return render(request, 'ventas/venta_form.html', context)


@login_required
def venta_pdf(request, venta_id):
    """
    Genera PDF de una venta.
    
    Accesible para:
    - El vendedor que creó la venta
    - Admin y secretaría
    
    Args:
        request: HttpRequest
        venta_id: ID de la venta
    
    Returns:
        HttpResponse: PDF como attachment o error
    """
    venta = get_object_or_404(
        Venta.objects.select_related(
            'detalle_planificacion__planificacion__asignacion__vendedor',
            'cliente',
            'carga_camion__camion'
        ).prefetch_related('detalles__producto'),
        id=venta_id
    )
    
    # Validar permisos
    vendedor_venta = venta.detalle_planificacion.planificacion.asignacion.vendedor
    
    if request.user.es_vendedor and request.user != vendedor_venta:
        messages.error(request, 'No tienes permiso para ver esta venta.')
        return redirect('planificacion_vendedor_dia')
    
    try:
        pdf_content = generar_pdf_venta(venta)
        
        response = HttpResponse(pdf_content, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="venta_{venta.id}.pdf"'
        
        return response
    
    except Exception as e:
        messages.error(request, f'Error al generar PDF: {str(e)}')
        return redirect('planificacion_vendedor_dia')


@login_required
def venta_listar(request):
    """
    Lista todas las ventas con filtros.
    
    Accesible para: Admin y Secretaría
    
    Filtros:
    - Rango de fechas
    - Vendedor
    - Cliente
    
    Args:
        request: HttpRequest
    
    Returns:
        HttpResponse: Template con lista de ventas
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver todas las ventas.')
        return redirect('home')
    
    # Obtener todas las ventas
    ventas = Venta.objects.select_related(
        'cliente',
        'detalle_planificacion__planificacion__asignacion__vendedor',
        'carga_camion__camion'
    ).order_by('-fecha')
    
    # Filtros
    fecha_inicio = request.GET.get('fecha_inicio')
    fecha_fin = request.GET.get('fecha_fin')
    vendedor_id = request.GET.get('vendedor') or request.GET.get('vendedor_id')
    cliente_id = request.GET.get('cliente') or request.GET.get('cliente_id')
    
    # Aplicar filtros de fecha (default: últimos 30 días)
    if not fecha_inicio and not fecha_fin:
        fecha_fin = timezone.now().date()
        fecha_inicio = fecha_fin - timedelta(days=30)
    
    if fecha_inicio:
        try:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__gte=fecha_inicio)
        except:
            pass
    
    if fecha_fin:
        try:
            fecha_fin = timezone.datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            ventas = ventas.filter(fecha__lte=fecha_fin)
        except:
            pass
    
    if vendedor_id:
        ventas = ventas.filter(
            detalle_planificacion__planificacion__asignacion__vendedor_id=vendedor_id
        )
    
    if cliente_id:
        ventas = ventas.filter(cliente_id=cliente_id)
    
    # Calcular totales
    totales = ventas.aggregate(
        total_ventas=Sum('total'),
        cantidad_ventas=Count('id')
    )
    
    total_neto = totales['total_ventas'] or 0
    
    # Paginación
    paginator = Paginator(ventas, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'ventas': page_obj,  # iterable en template
        'total_ventas': totales['cantidad_ventas'] or 0,
        'total_neto': total_neto,
        'total_bruto': total_neto,  # No manejamos descuentos; mapeo útil para template
        'total_descuento': 0,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'vendedores': get_user_model().objects.filter(rol='vendedor', is_active=True).order_by('first_name', 'last_name'),
        'clientes': Cliente.objects.filter(activo=True).order_by('nombre'),
    }
    
    return render(request, 'ventas/venta_list.html', context)


@login_required
def venta_detalle(request, pk):
    """
    Muestra el detalle de una venta específica.
    
    Args:
        request: HttpRequest
        pk: ID de la venta
    
    Returns:
        HttpResponse: Template con detalle de venta
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permiso para ver detalles de ventas.')
        return redirect('home')
    
    venta = get_object_or_404(
        Venta.objects.select_related(
            'cliente',
            'detalle_planificacion__planificacion__asignacion__vendedor',
            'detalle_planificacion__planificacion__ruta_detalle__cliente',
            'carga_camion__camion'
        ).prefetch_related('detalles__producto__categoria'),
        pk=pk
    )
    
    detalles = venta.detalles.all()
    
    context = {
        'venta': venta,
        'detalles': detalles,
    }
    
    return render(request, 'ventas/venta_detalle.html', context)
