"""
Servicio de generación de reportes PDF para traslados de pacientes.
"""

import io

from django.template.loader import render_to_string
from xhtml2pdf import pisa


def generarPdf (queryset, mes):
	"""Genera un archivo PDF con los registros del queryset dado.

	Renderiza la plantilla HTML `partials/reporte_pdf.html` y la convierte a
	PDF en orientación horizontal (landscape) usando xhtml2pdf. Si el queryset
	está vacío, el PDF contiene solo los encabezados con un mensaje indicativo.

	Args:
		queryset: QuerySet de TrasladoPaciente con los registros a incluir.
		mes: Número de mes (1–12) usado para nombrar el archivo.

	Returns:
		tuple: (bytes del archivo .pdf, nombre del archivo str)

	Raises:
		ValueError: Si xhtml2pdf reporta errores durante la conversión.
	"""
	contexto = {
		'registros': queryset,
		'mes': mes,
	}

	htmlContenido = render_to_string (
		'traslados/partials/reporte_pdf.html',
		contexto,
	)

	buffer = io.BytesIO ()
	resultado = pisa.CreatePDF (
		src=htmlContenido,
		dest=buffer,
		encoding='utf-8',
	)

	if resultado.err:
		raise ValueError (f'Error al generar el PDF: {resultado.err}')

	buffer.seek (0)
	nombreArchivo = f'traslados_{mes}.pdf'
	return buffer.getvalue (), nombreArchivo
