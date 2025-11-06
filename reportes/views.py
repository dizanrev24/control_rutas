"""
Vistas para los reportes administrativos.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect
from django.db.models import Count, Q, Sum, F
from planificacion.models import DetallePlanificacion
from ventas.models import Venta, DetalleVenta
from django.utils import timezone
from datetime import timedelta


@login_required
def reporte_fotos_duplicadas(request):
    """
    Reporte de fotos duplicadas usando el campo hash_foto.
    
    Identifica visitas donde se usó la misma foto (mismo hash).
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para ver reportes.')
        return redirect('home')
    
    # Buscar hashes duplicados
    # Agrupar por hash_foto y contar cuántas veces aparece
    duplicados = DetallePlanificacion.objects.filter(
        hash_foto__isnull=False
    ).values('hash_foto').annotate(
        total=Count('id')
    ).filter(total__gt=1).order_by('-total')
    
    # Para cada hash duplicado, obtener los detalles
    resultados = []
    for dup in duplicados:
        hash_foto = dup['hash_foto']
        detalles = DetallePlanificacion.objects.filter(
            hash_foto=hash_foto
        ).select_related(
            'planificacion__ruta_detalle__cliente',
            'planificacion__asignacion__vendedor'
        ).order_by('-planificacion__fecha')
        
        resultados.append({
            'hash': hash_foto,
            'total': dup['total'],
            'detalles': detalles
        })
    
    context = {
        'resultados': resultados,
        'total_hashes_duplicados': len(resultados),
        'total_registros_afectados': sum(r['total'] for r in resultados),
    }
    
    return render(request, 'reportes/fotos_duplicadas.html', context)


@login_required
def reporte_ubicaciones_invalidas(request):
    """
    Reporte de ubicaciones inválidas.
    
    Muestra visitas donde ubicacion_valida = False.
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para ver reportes.')
        return redirect('home')
    
    # Obtener todas las planificaciones con ubicación inválida
    invalidas = DetallePlanificacion.objects.filter(
        ubicacion_valida=False
    ).select_related(
        'planificacion__ruta_detalle__cliente',
        'planificacion__asignacion__vendedor',
        'planificacion__asignacion__ruta'
    ).order_by('-planificacion__fecha')
    
    # Agrupar por vendedor
    por_vendedor = {}
    for detalle in invalidas:
        vendedor = detalle.planificacion.asignacion.vendedor.get_full_name() or detalle.planificacion.asignacion.vendedor.username
        if vendedor not in por_vendedor:
            por_vendedor[vendedor] = []
        por_vendedor[vendedor].append(detalle)
    
    context = {
        'invalidas': invalidas,
        'por_vendedor': por_vendedor,
        'total_invalidas': invalidas.count(),
    }
    
    return render(request, 'reportes/ubicaciones_invalidas.html', context)


@login_required
def reporte_ventas_por_vendedor(request):
    """
    Reporte de ventas por vendedor.
    
    Muestra totales de ventas agrupados por vendedor con filtros de fecha.
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para ver reportes.')
        return redirect('home')
    
    # Filtros de fecha (por defecto último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    if request.GET.get('fecha_inicio'):
        try:
            fecha_inicio = timezone.datetime.strptime(
                request.GET.get('fecha_inicio'), '%Y-%m-%d'
            ).date()
        except:
            pass
    
    if request.GET.get('fecha_fin'):
        try:
            fecha_fin = timezone.datetime.strptime(
                request.GET.get('fecha_fin'), '%Y-%m-%d'
            ).date()
        except:
            pass
    
    # Obtener ventas en el rango de fechas
    ventas = Venta.objects.filter(
        fecha__range=[fecha_inicio, fecha_fin]
    ).select_related(
        'detalle_planificacion__planificacion__asignacion__vendedor'
    )
    
    # Agrupar por vendedor
    vendedores_stats = {}
    
    for venta in ventas:
        vendedor = venta.detalle_planificacion.planificacion.asignacion.vendedor
        nombre_vendedor = vendedor.get_full_name() or vendedor.username
        
        if nombre_vendedor not in vendedores_stats:
            vendedores_stats[nombre_vendedor] = {
                'vendedor': vendedor,
                'total_ventas': 0,
                'total_monto': 0,
                'ventas': []
            }
        
        vendedores_stats[nombre_vendedor]['total_ventas'] += 1
        vendedores_stats[nombre_vendedor]['total_monto'] += venta.total
        vendedores_stats[nombre_vendedor]['ventas'].append(venta)
    
    # Ordenar por total_monto descendente
    vendedores_ordenados = sorted(
        vendedores_stats.items(),
        key=lambda x: x[1]['total_monto'],
        reverse=True
    )
    
    # Calcular totales generales
    total_general = sum(v['total_monto'] for _, v in vendedores_ordenados)
    total_ventas = sum(v['total_ventas'] for _, v in vendedores_ordenados)
    
    context = {
        'vendedores_stats': vendedores_ordenados,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,
        'total_general': total_general,
        'total_ventas': total_ventas,
    }
    
    return render(request, 'reportes/ventas_por_vendedor.html', context)


@login_required
def reporte_dashboard(request):
    """
    Dashboard de reportes con resumen general.
    """
    if not request.user.puede_generar_reportes:
        messages.error(request, 'No tienes permiso para ver reportes.')
        return redirect('home')
    
    # Estadísticas rápidas
    fotos_duplicadas_count = DetallePlanificacion.objects.filter(
        foto_duplicada=True
    ).count()
    
    ubicaciones_invalidas_count = DetallePlanificacion.objects.filter(
        ubicacion_valida=False
    ).count()
    
    # Ventas del mes actual
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    ventas_mes = Venta.objects.filter(
        fecha__gte=primer_dia_mes
    ).aggregate(
        total=Sum('total')
    )['total'] or 0
    
    context = {
        'fotos_duplicadas_count': fotos_duplicadas_count,
        'ubicaciones_invalidas_count': ubicaciones_invalidas_count,
        'ventas_mes': ventas_mes,
        'mes_actual': hoy.strftime('%B %Y'),
    }
    
    return render(request, 'reportes/dashboard.html', context)
