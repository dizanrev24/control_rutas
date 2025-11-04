from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Cliente
from .forms import ClienteForm, ClienteFiltroForm


@login_required
def cliente_listar(request):
    """
    Lista todos los clientes con filtros y paginación
    Acceso: admin y secretaria
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    # Obtener parámetros de filtro
    form_filtro = ClienteFiltroForm(request.GET)
    clientes = Cliente.objects.all()
    
    if form_filtro.is_valid():
        buscar = form_filtro.cleaned_data.get('buscar')
        activo = form_filtro.cleaned_data.get('activo')
        
        if buscar:
            clientes = clientes.filter(
                Q(nombre__icontains=buscar) | 
                Q(nit__icontains=buscar) |
                Q(nombre_contacto__icontains=buscar)
            )
        
        if activo == '1':
            clientes = clientes.filter(activo=True)
        elif activo == '0':
            clientes = clientes.filter(activo=False)
    
    clientes = clientes.order_by('nombre')
    
    # Paginación
    paginator = Paginator(clientes, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form_filtro': form_filtro,
    }
    
    return render(request, 'clientes/cliente_list.html', context)


@login_required
def cliente_crear(request):
    """
    Crea un nuevo cliente
    Acceso: admin y secretaria
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cliente creado exitosamente!')
            return redirect('cliente_listar')
        else:
            messages.error(request, 'Error al crear el cliente. Verifique los datos.')
    else:
        form = ClienteForm()
    
    context = {'form': form}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_editar(request, pk):
    """
    Edita un cliente existente
    Acceso: admin y secretaria
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permisos para acceder a esta sección.')
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    
    if request.method == 'POST':
        form = ClienteForm(request.POST, request.FILES, instance=cliente)
        if form.is_valid():
            form.save()
            messages.success(request, '¡Cliente actualizado exitosamente!')
            return redirect('cliente_listar')
        else:
            messages.error(request, 'Error al actualizar el cliente. Verifique los datos.')
    else:
        form = ClienteForm(instance=cliente)
    
    context = {'form': form, 'cliente': cliente}
    return render(request, 'clientes/cliente_form.html', context)


@login_required
def cliente_eliminar(request, pk):
    """
    Desactiva un cliente (soft delete)
    Acceso: admin y secretaria
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.activo = False
    cliente.save()
    
    messages.success(request, 'Cliente desactivado exitosamente.')
    return redirect('cliente_listar')


@login_required
def cliente_activar(request, pk):
    """
    Activa un cliente
    Acceso: admin y secretaria
    """
    if not request.user.puede_gestionar_rutas:
        messages.error(request, 'No tienes permisos para realizar esta acción.')
        return redirect('home')
    
    cliente = get_object_or_404(Cliente, pk=pk)
    cliente.activo = True
    cliente.save()
    
    messages.success(request, 'Cliente activado exitosamente.')
    return redirect('cliente_listar')


@login_required
def vendedor_crear_cliente(request):
    """
    Permite al vendedor crear un cliente nuevo que se auto-asigna a su ruta activa
    El cliente aparece inmediatamente en su planificación del día
    Acceso: solo vendedores
    """
    if not request.user.es_vendedor:
        messages.error(request, 'Esta sección es solo para vendedores.')
        return redirect('login')
    
    from asignaciones.models import Asignacion
    from rutas.models import RutaDetalle
    from planificacion.models import Planificacion
    from datetime import date
    
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
        form = ClienteForm(request.POST, request.FILES)
        if form.is_valid():
            # Crear cliente
            cliente = form.save()
            
            # Obtener el máximo orden_visita de la ruta
            max_orden = RutaDetalle.objects.filter(
                ruta=asignacion.ruta
            ).count() + 1
            
            # Asignar a la ruta del vendedor (crear RutaDetalle)
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
            
            messages.success(request, f'¡Cliente "{cliente.nombre}" registrado y agregado a tu ruta!')
            return redirect('planificacion_vendedor_dia')
        else:
            messages.error(request, 'Error al crear el cliente. Verifique los datos.')
    else:
        form = ClienteForm()
    
    context = {
        'form': form,
        'asignacion': asignacion,
        'es_vendedor': True
    }
    return render(request, 'clientes/vendedor_crear_cliente.html', context)
