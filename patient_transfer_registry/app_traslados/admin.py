# Registro de modelos en el panel de administración de Django.
# Implementado en la Tarea 3.

from django.contrib import admin

from .models import ControlMes, Perfil, TrasladoPaciente


class AdminPerfil (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo Perfil."""

	list_display = ['usuario', 'rol']
	list_filter = ['rol']
	search_fields = ['usuario__username']


class AdminControlMes (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo ControlMes."""

	list_display = ['mes', 'estado', 'fecha_cierre', 'cerrado_por']
	list_filter = ['estado']
	ordering = ['mes']


class AdminTrasladoPaciente (admin.ModelAdmin):
	"""Configuración del panel de administración para el modelo TrasladoPaciente."""

	list_display = [
		'fecha',
		'mes',
		'nombre_paciente',
		'documento',
		'servicio',
		'destino',
		'conductor',
		'ambulancia',
	]
	list_filter = ['mes', 'servicio', 'destino']
	search_fields = ['nombre_paciente', 'documento', 'conductor']
	ordering = ['fecha', 'hora_reporte']


admin.site.register (Perfil, AdminPerfil)
admin.site.register (ControlMes, AdminControlMes)
admin.site.register (TrasladoPaciente, AdminTrasladoPaciente)
