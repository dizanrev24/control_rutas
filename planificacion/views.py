from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import date, datetime
from django.db.models import Q
from .models import Planificacion, DetallePlanificacion
from .forms import IniciarVisitaForm, FinalizarVisitaForm, ClienteNuevoVendedorForm, MarcarNoVisitadoForm
from asignaciones.models import Asignacion
from rutas.models import RutaDetalle
from clientes.models import Cliente
from core.utils import calcular_hash_md5, validar_ubicacion, verificar_foto_duplicada


@login_required
def planificacion_vendedor_dia(request):
    """
    Vista principal del vendedor: muestra su planificación del día actual
    Incluye clientes planificados y clientes nuevos creados en el día
    """
    # Verificar que el usuario sea vendedor
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('login')
    
    # Verificar que el usuario esté activo
    if not request.user.activo:
        context = {
            'error_tipo': 'inactivo',
            'mensaje': 'Tu cuenta de usuario está inactiva. Contacta con el administrador.'
        }
        return render(request, 'planificacion/vendedor_sin_acceso.html', context)
    
    hoy = date.today()
    
    # Obtener asignación activa del vendedor usando el usuario directamente
    asignaciones_activas = []
    for asig in Asignacion.objects.filter(vendedor=request.user):
        if asig.esta_activa:
            asignaciones_activas.append(asig)
    
    asignacion = asignaciones_activas[0] if asignaciones_activas else None
    
    if not asignacion:
        # Renderizar vista especial para vendedor sin asignación
        context = {
            'error_tipo': 'sin_asignacion',
            'mensaje': 'No tienes una ruta asignada actualmente. Contacta con el administrador.',
            'vendedor': request.user
        }
        return render(request, 'planificacion/vendedor_sin_acceso.html', context)
    
    # Obtener planificaciones del día (planificadas y no planificadas)
    planificaciones = Planificacion.objects.filter(
        asignacion=asignacion,
        fecha=hoy
    ).select_related('ruta_detalle__cliente').order_by('ruta_detalle__orden_visita', 'fecha_creacion')
    
    # Para cada planificación, obtener o crear el DetallePlanificacion
    planificaciones_detalle = []
    for plan in planificaciones:
        detalle, created = DetallePlanificacion.objects.get_or_create(
            planificacion=plan,
            defaults={'estado': 'pendiente'}
        )
        planificaciones_detalle.append({
            'planificacion': plan,
            'detalle': detalle,
            'cliente': plan.ruta_detalle.cliente,
            'es_nuevo': plan.tipo == 'no_planificado',
            'visita_activa': detalle.hora_llegada and not detalle.hora_salida,
        })
    
    context = {
        'planificaciones': planificaciones_detalle,
        'asignacion': asignacion,
        'fecha': hoy,
    }
    
    return render(request, 'planificacion/vendedor_dia.html', context)


@login_required
def vendedor_crear_cliente_nuevo(request):
    """
    Permite al vendedor crear un cliente nuevo que aparecerá en su planificación del día
    Se asigna automáticamente a su ruta y se crea una planificación tipo 'no_planificado'
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('login')
    
    # Verificar que el usuario tenga un perfil de vendedor
    try:
        vendedor = request.user.vendedor
    except:
        messages.error(request, 'No tienes un perfil de vendedor asignado. Contacta con el administrador.')
        return redirect('planificacion_vendedor_dia')
    
    # Verificar que tenga asignación activa
    asignaciones_activas = []
    for asig in Asignacion.objects.filter(vendedor=vendedor):
        if asig.esta_activa:
            asignaciones_activas.append(asig)
    
    asignacion = asignaciones_activas[0] if asignaciones_activas else None
    
    if not asignacion:
        messages.warning(request, 'No tienes una ruta asignada. Contacta con el administrador.')
        return redirect('planificacion_vendedor_dia')
    
    if request.method == 'POST':
        form = ClienteNuevoVendedorForm(request.POST)
        if form.is_valid():
            # Crear cliente
            cliente = form.save()
            
            # Asignar a la ruta del vendedor (crear RutaDetalle)
            # Obtener el máximo orden_visita de la ruta
            max_orden = RutaDetalle.objects.filter(
                ruta=asignacion.ruta
            ).count() + 1
            
            ruta_detalle = RutaDetalle.objects.create(
                ruta=asignacion.ruta,
                cliente=cliente,
                orden_visita=max_orden,
                activo=True
            )
            
            # Crear planificación para hoy con tipo 'no_planificado'
            hoy = date.today()
            planificacion = Planificacion.objects.create(
                asignacion=asignacion,
                ruta_detalle=ruta_detalle,
                fecha=hoy,
                tipo='no_planificado'
            )
            
            messages.success(request, f'¡Cliente "{cliente.nombre}" registrado y agregado a tu planificación del día!')
            return redirect('planificacion_vendedor_dia')
        else:
            messages.error(request, 'Error al crear el cliente. Verifique los datos.')
    else:
        form = ClienteNuevoVendedorForm()
    
    context = {'form': form}
    return render(request, 'planificacion/crear_cliente_nuevo.html', context)


@login_required
def iniciar_visita(request, planificacion_id):
    """
    Inicia una visita: captura ubicación, foto, calcula hash MD5 y valida ubicación
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('home')
    
    planificacion = get_object_or_404(Planificacion, pk=planificacion_id)
    
    # Verificar que la planificación pertenezca al vendedor
    if planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta planificación.')
        return redirect('planificacion_vendedor_dia')
    
    # Obtener o crear detalle
    detalle, created = DetallePlanificacion.objects.get_or_create(
        planificacion=planificacion,
        defaults={'estado': 'pendiente'}
    )
    
    # Verificar que no haya una visita activa
    if detalle.hora_llegada and not detalle.hora_salida:
        messages.info(request, 'Ya tienes una visita activa con este cliente.')
        return redirect('dentro_visita', detalle_id=detalle.pk)
    
    # Verificar que no esté ya visitado
    if detalle.estado == 'visitado' and detalle.hora_salida:
        messages.warning(request, 'Este cliente ya fue visitado hoy.')
        return redirect('planificacion_vendedor_dia')
    
    if request.method == 'POST':
        form = IniciarVisitaForm(request.POST, request.FILES, instance=detalle)
        if form.is_valid():
            detalle = form.save(commit=False)
            detalle.hora_llegada = timezone.now()
            detalle.estado = 'visitado'
            
            # Calcular hash MD5 si hay foto
            if detalle.fotografia_referencia:
                hash_foto = calcular_hash_md5(detalle.fotografia_referencia)
                detalle.hash_foto = hash_foto
                
                # Verificar si es duplicada (solo para admin, vendedor no lo ve)
                es_duplicada, detalle_anterior = verificar_foto_duplicada(hash_foto)
                if es_duplicada:
                    detalle.foto_duplicada = True
            
            # Validar ubicación (100m de margen)
            cliente = planificacion.ruta_detalle.cliente
            if cliente.latitud and cliente.longitud and detalle.latitud and detalle.longitud:
                es_valida, distancia = validar_ubicacion(
                    cliente.latitud, cliente.longitud,
                    detalle.latitud, detalle.longitud,
                    margen=100
                )
                detalle.ubicacion_valida = es_valida
            
            detalle.save()
            
            messages.success(request, '¡Visita iniciada correctamente!')
            return redirect('dentro_visita', detalle_id=detalle.pk)
        else:
            messages.error(request, 'Error al iniciar la visita. Verifique los datos.')
    else:
        form = IniciarVisitaForm(instance=detalle)
    
    context = {
        'form': form,
        'planificacion': planificacion,
        'cliente': planificacion.ruta_detalle.cliente,
    }
    return render(request, 'planificacion/iniciar_visita.html', context)


@login_required
def continuar_visita(request, detalle_id):
    """
    Continúa una visita que ya fue iniciada (tiene hora_llegada pero no hora_salida)
    Redirige directamente a dentro_visita
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('home')
    
    detalle = get_object_or_404(DetallePlanificacion, pk=detalle_id)
    
    # Verificar permisos
    if detalle.planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta visita.')
        return redirect('planificacion_vendedor_dia')
    
    # Verificar que la visita esté activa
    if not detalle.hora_llegada or detalle.hora_salida:
        messages.warning(request, 'Esta visita no está activa.')
        return redirect('planificacion_vendedor_dia')
    
    return redirect('dentro_visita', detalle_id=detalle.pk)


@login_required
def dentro_visita(request, detalle_id):
    """
    Vista dentro de la visita: muestra opciones para crear ventas, pedidos o finalizar
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('home')
    
    detalle = get_object_or_404(DetallePlanificacion, pk=detalle_id)
    
    # Verificar permisos
    if detalle.planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para acceder a esta visita.')
        return redirect('planificacion_vendedor_dia')
    
    # Verificar que la visita esté activa
    if not detalle.hora_llegada or detalle.hora_salida:
        messages.warning(request, 'Esta visita no está activa.')
        return redirect('planificacion_vendedor_dia')
    
    # Obtener ventas y pedidos de esta visita
    ventas = detalle.ventas.all()
    pedidos = detalle.pedidos.all()
    
    context = {
        'detalle': detalle,
        'cliente': detalle.planificacion.ruta_detalle.cliente,
        'planificacion': detalle.planificacion,
        'ventas': ventas,
        'pedidos': pedidos,
    }
    
    return render(request, 'planificacion/dentro_visita.html', context)


@login_required
def finalizar_visita(request, detalle_id):
    """
    Finaliza una visita: registra hora_salida
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('home')
    
    detalle = get_object_or_404(DetallePlanificacion, pk=detalle_id)
    
    # Verificar permisos
    if detalle.planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para finalizar esta visita.')
        return redirect('planificacion_vendedor_dia')
    
    # Verificar que la visita esté activa
    if not detalle.hora_llegada or detalle.hora_salida:
        messages.warning(request, 'Esta visita no está activa o ya fue finalizada.')
        return redirect('planificacion_vendedor_dia')
    
    if request.method == 'POST':
        form = FinalizarVisitaForm(request.POST)
        if form.is_valid():
            observaciones_cierre = form.cleaned_data.get('observaciones_cierre')
            
            detalle.hora_salida = timezone.now()
            if observaciones_cierre:
                detalle.observaciones += f"\n[Cierre] {observaciones_cierre}"
            detalle.save()
            
            messages.success(request, '¡Visita finalizada correctamente!')
            return redirect('planificacion_vendedor_dia')
    else:
        form = FinalizarVisitaForm()
    
    context = {
        'form': form,
        'detalle': detalle,
        'cliente': detalle.planificacion.ruta_detalle.cliente,
    }
    
    return render(request, 'planificacion/finalizar_visita.html', context)


@login_required
def marcar_no_visitado(request, planificacion_id):
    """
    Marca un cliente como no visitado o cerrado sin iniciar visita
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('home')
    
    planificacion = get_object_or_404(Planificacion, pk=planificacion_id)
    
    # Verificar permisos
    if planificacion.asignacion.vendedor != request.user:
        messages.error(request, 'No tienes permiso para modificar esta planificación.')
        return redirect('planificacion_vendedor_dia')
    
    # Obtener o crear detalle
    detalle, created = DetallePlanificacion.objects.get_or_create(
        planificacion=planificacion,
        defaults={'estado': 'pendiente'}
    )
    
    if request.method == 'POST':
        form = MarcarNoVisitadoForm(request.POST)
        if form.is_valid():
            motivo = form.cleaned_data.get('motivo')
            observaciones = form.cleaned_data.get('observaciones')
            
            detalle.estado = motivo
            detalle.observaciones = observaciones
            detalle.save()
            
            messages.success(request, f'Cliente marcado como "{dict(form.fields["motivo"].choices)[motivo]}"')
            return redirect('planificacion_vendedor_dia')
    else:
        form = MarcarNoVisitadoForm()
    
    context = {
        'form': form,
        'planificacion': planificacion,
        'cliente': planificacion.ruta_detalle.cliente,
    }
    
    return render(request, 'planificacion/marcar_no_visitado.html', context)
