"""
Utilidades compartidas para el proyecto
"""
import hashlib
from math import radians, sin, cos, sqrt, atan2
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
import logging
from decimal import Decimal

logger = logging.getLogger(__name__)

# Preferencia de renderizador: se intenta WeasyPrint y se cae a xhtml2pdf si no está disponible


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


def _render_html_to_pdf(html_string: str) -> bytes:
    """
    Renderiza HTML a PDF intentando primero WeasyPrint y, si no está disponible,
    usando xhtml2pdf (ReportLab) como fallback.

    Returns: bytes del PDF
    Raises: Exception si ninguno está disponible
    """
    # 1) Intentar WeasyPrint
    try:
        from weasyprint import HTML  # type: ignore
        logger.info("Render PDF con WeasyPrint")
        html = HTML(string=html_string)
        return html.write_pdf()
    except Exception as e:
        logger.warning("WeasyPrint no disponible o falló: %s", e)

    # 2) Fallback: xhtml2pdf (pisa)
    try:
        from xhtml2pdf import pisa  # type: ignore
        logger.info("Render PDF con xhtml2pdf (fallback)")
        result = BytesIO()
        # xhtml2pdf espera una fuente tipo archivo o string; maneja CSS limitado
        pisa.CreatePDF(src=html_string, dest=result, encoding='utf-8')
        pdf_bytes = result.getvalue()
        result.close()
        if not pdf_bytes:
            raise Exception("xhtml2pdf no generó contenido")
        return pdf_bytes
    except Exception as e:
        logger.error("xhtml2pdf no disponible o falló: %s", e)
        raise Exception(
            "No fue posible generar el PDF. Instala WeasyPrint (con GTK) o xhtml2pdf. "
            "En Windows: instala el runtime GTK 3 y reinicia; como alternativa, 'pip install xhtml2pdf'."
        )


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
    
    # Intentar con ReportLab (no requiere GTK ni binarios externos)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import mm

        logger.info("Render PDF de venta con ReportLab")
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)

        styles = getSampleStyleSheet()
        elements = []

        titulo = f"Venta #{venta.id}"
        elements.append(Paragraph(titulo, styles['Title']))
        elements.append(Spacer(1, 6))

        info_cliente = f"Cliente: {venta.cliente.nombre}"
        elements.append(Paragraph(info_cliente, styles['Normal']))
        fecha_txt = f"Fecha: {timezone.localtime(venta.fecha).strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(fecha_txt, styles['Normal']))
        elements.append(Spacer(1, 12))

        # Tabla de detalles
        data = [["Producto", "Cant.", "Precio (Q)", "Subtotal (Q)"]]
        for det in venta.detalles.all():
            nombre = det.producto.nombre
            cant = f"{int(det.cantidad)}"
            precio = f"{det.precio_unitario:.2f}"
            subtotal = f"{det.subtotal:.2f}"
            data.append([nombre, cant, precio, subtotal])

        # Fila total
        total = venta.calcular_total()
        data.append(["", "", "Total", f"{total:.2f}"])

        table = Table(data, colWidths=[90*mm, 20*mm, 30*mm, 30*mm])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,1), (-1,-2), 'RIGHT'),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)

        if venta.observaciones:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Observaciones: {venta.observaciones}", styles['Italic']))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        logger.warning("ReportLab no disponible o falló: %s", e)

    # Fallback a HTML → PDF
    template = get_template('ventas/venta_pdf.html')
    context = {'venta': venta, 'now': timezone.now()}
    html_string = template.render(context)
    return _render_html_to_pdf(html_string)


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
    
    # Intentar con ReportLab primero
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.units import mm

        logger.info("Render PDF de pedido con ReportLab")
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)

        styles = getSampleStyleSheet()
        elements = []

        titulo = f"Pedido #{pedido.id}"
        elements.append(Paragraph(titulo, styles['Title']))
        elements.append(Spacer(1, 6))

        info_cliente = f"Cliente: {pedido.cliente.nombre}"
        elements.append(Paragraph(info_cliente, styles['Normal']))
        fecha_txt = f"Fecha: {timezone.localtime(pedido.fecha).strftime('%d/%m/%Y %H:%M')}"
        elements.append(Paragraph(fecha_txt, styles['Normal']))
        elements.append(Spacer(1, 12))

        data = [["Producto", "Cant.", "Precio (Q)", "Subtotal (Q)"]]
        for det in pedido.detalles.all():
            nombre = det.producto.nombre
            cant = f"{int(det.cantidad)}"
            precio = f"{det.precio_unitario:.2f}"
            subtotal = f"{det.subtotal:.2f}"
            data.append([nombre, cant, precio, subtotal])

        total = pedido.calcular_total()
        data.append(["", "", "Total", f"{total:.2f}"])

        table = Table(data, colWidths=[90*mm, 20*mm, 30*mm, 30*mm])
        table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
            ('ALIGN', (1,1), (-1,-2), 'RIGHT'),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('ALIGN', (3,0), (3,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME', (-2,-1), (-1,-1), 'Helvetica-Bold'),
        ]))
        elements.append(table)

        if pedido.observaciones:
            elements.append(Spacer(1, 12))
            elements.append(Paragraph(f"Observaciones: {pedido.observaciones}", styles['Italic']))

        doc.build(elements)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        logger.warning("ReportLab no disponible o falló: %s", e)

    # Fallback a HTML → PDF
    template = get_template('pedidos/pedido_pdf.html')
    context = {'pedido': pedido, 'now': timezone.now()}
    html_string = template.render(context)
    return _render_html_to_pdf(html_string)


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
