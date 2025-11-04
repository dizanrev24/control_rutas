"""
Utilidades compartidas para el proyecto
"""
import hashlib
from math import radians, sin, cos, sqrt, atan2
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template

# WeasyPrint requiere GTK instalado en Windows
# Descomentar cuando GTK esté instalado
# from weasyprint import HTML


def calcular_hash_md5(archivo):
    """
    Calcula el hash MD5 de un archivo
    
    Args:
        archivo: Archivo de imagen (UploadedFile)
    
    Returns:
        str: Hash MD5 hexadecimal
    """
    hash_md5 = hashlib.md5()
    
    # Leer el archivo en chunks para archivos grandes
    for chunk in archivo.chunks():
        hash_md5.update(chunk)
    
    # Regresar el puntero al inicio del archivo
    archivo.seek(0)
    
    return hash_md5.hexdigest()


def calcular_distancia_haversine(lat1, lon1, lat2, lon2):
    """
    Calcula la distancia entre dos puntos geográficos usando la fórmula de Haversine
    
    Args:
        lat1: Latitud del primer punto (float)
        lon1: Longitud del primer punto (float)
        lat2: Latitud del segundo punto (float)
        lon2: Longitud del segundo punto (float)
    
    Returns:
        float: Distancia en metros
    """
    # Radio de la Tierra en metros
    R = 6371000
    
    # Convertir grados a radianes
    lat1_rad = radians(float(lat1))
    lat2_rad = radians(float(lat2))
    delta_lat = radians(float(lat2) - float(lat1))
    delta_lon = radians(float(lon2) - float(lon1))
    
    # Fórmula de Haversine
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distancia = R * c
    
    return distancia


def validar_ubicacion(lat_cliente, lon_cliente, lat_visita, lon_visita, margen=100):
    """
    Valida si la ubicación de la visita está dentro del margen aceptable
    
    Args:
        lat_cliente: Latitud del cliente registrado
        lon_cliente: Longitud del cliente registrado
        lat_visita: Latitud capturada en la visita
        lon_visita: Longitud capturada en la visita
        margen: Margen de error aceptable en metros (default: 100)
    
    Returns:
        tuple: (es_valida: bool, distancia: float)
    """
    if not all([lat_cliente, lon_cliente, lat_visita, lon_visita]):
        return False, None
    
    distancia = calcular_distancia_haversine(lat_cliente, lon_cliente, lat_visita, lon_visita)
    es_valida = distancia <= margen
    
    return es_valida, distancia


def generar_pdf_venta(venta):
    """
    Genera un PDF de una venta
    
    Args:
        venta: Instancia del modelo Venta
    
    Returns:
        bytes: Contenido del PDF
    
    Nota: Requiere GTK instalado en Windows para WeasyPrint
    """
    from django.utils import timezone
    
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as e:
        # WeasyPrint no disponible
        raise Exception(
            'WeasyPrint requiere GTK. '
            'Descarga: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer'
        )
    
    template = get_template('ventas/venta_pdf.html')
    
    context = {
        'venta': venta,
        'now': timezone.now(),
    }
    
    html_string = template.render(context)
    html = HTML(string=html_string)
    
    # Generar y retornar PDF como bytes
    return html.write_pdf()


def generar_pdf_pedido(pedido):
    """
    Genera un PDF de un pedido
    
    Args:
        pedido: Instancia del modelo Pedido
    
    Returns:
        bytes: Contenido del PDF
    
    Nota: Requiere GTK instalado en Windows para WeasyPrint
    """
    from django.utils import timezone
    
    try:
        from weasyprint import HTML
    except (ImportError, OSError) as e:
        # WeasyPrint no disponible
        raise Exception(
            'WeasyPrint requiere GTK. '
            'Descarga: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer'
        )
    
    template = get_template('pedidos/pedido_pdf.html')
    
    context = {
        'pedido': pedido,
        'now': timezone.now(),
    }
    
    html_string = template.render(context)
    html = HTML(string=html_string)
    
    # Generar y retornar PDF como bytes
    return html.write_pdf()


def verificar_foto_duplicada(hash_foto):
    """
    Verifica si una foto con el mismo hash ya existe
    
    Args:
        hash_foto: Hash MD5 de la foto
    
    Returns:
        tuple: (es_duplicada: bool, detalle_planificacion_anterior)
    """
    from planificacion.models import DetallePlanificacion
    
    detalle_anterior = DetallePlanificacion.objects.filter(
        hash_foto=hash_foto
    ).exclude(hash_foto='').first()
    
    if detalle_anterior:
        return True, detalle_anterior
    
    return False, None
