"""
Tests unitarios para los modelos de app_traslados.

Verifica el comportamiento concreto de TrasladoPaciente y ControlMes
con casos específicos y casos borde.
"""

import datetime

from django.core.exceptions import ValidationError
from django.test import TestCase

from app_traslados.models import ControlMes, TrasladoPaciente


def crearControlMeses ():
	"""Crea las 12 filas de ControlMes con estado ABIERTO si no existen."""
	for numeroMes in range (1, 13):
		ControlMes.objects.get_or_create (
			mes=numeroMes,
			defaults={'estado': 'ABIERTO'},
		)


def construirTrasladoValido (fecha=None):
	"""Construye y retorna un TrasladoPaciente con todos los campos requeridos."""
	if fecha is None:
		fecha = datetime.date.today ()
	return TrasladoPaciente (
		fecha=fecha,
		hora_reporte=datetime.time (8, 0),
		nombre_paciente='Paciente Prueba',
		documento='123456789',
		servicio='Urgencias',
		quien_reporta='Enfermera Prueba',
		destino='Hospital Central',
		procedimiento='Traslado de emergencia',
		medico='Dr. Prueba',
		conductor='Conductor Prueba',
		radio_operador='Radio Prueba',
		ambulancia='AMB-001',
	)


class TestDerivacionMes (TestCase):
	"""Tests unitarios para la derivación automática del campo mes desde fecha."""

	def setUp (self):
		"""Inicializa los 12 registros de ControlMes antes de cada prueba."""
		crearControlMeses ()

	def test_mes_derivado_correctamente_al_guardar (self):
		"""Verifica que save() asigna mes == fecha.month antes de persistir."""
		fecha = datetime.date (2024, 5, 15)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()

		self.assertEqual (traslado.mes, 5)

	def test_mes_derivado_en_enero (self):
		"""Verifica que el mes se deriva correctamente para enero (mes 1)."""
		fecha = datetime.date (2024, 1, 10)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()

		self.assertEqual (traslado.mes, 1)

	def test_mes_derivado_en_diciembre (self):
		"""Verifica que el mes se deriva correctamente para diciembre (mes 12)."""
		fecha = datetime.date (2023, 12, 31)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()

		self.assertEqual (traslado.mes, 12)

	def test_mes_derivado_persiste_en_base_de_datos (self):
		"""Verifica que el mes derivado se almacena correctamente y se recupera igual."""
		fecha = datetime.date (2024, 7, 20)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()

		trasladoRecuperado = TrasladoPaciente.objects.get (pk=traslado.pk)
		self.assertEqual (trasladoRecuperado.mes, 7)

	def test_mes_se_actualiza_al_cambiar_fecha (self):
		"""Verifica que mes se recalcula correctamente si se cambia la fecha antes de guardar."""
		fecha = datetime.date (2024, 3, 10)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()
		self.assertEqual (traslado.mes, 3)

		# Cambiar la fecha a otro mes y volver a guardar
		traslado.fecha = datetime.date (2024, 6, 10)
		traslado.save ()
		self.assertEqual (traslado.mes, 6)


class TestValidacionFechaFutura (TestCase):
	"""Tests unitarios para la validación de fechas futuras en TrasladoPaciente."""

	def setUp (self):
		"""Inicializa los 12 registros de ControlMes antes de cada prueba."""
		crearControlMeses ()

	def test_fecha_futura_lanza_validation_error (self):
		"""Verifica que clean() lanza ValidationError cuando fecha es futura."""
		fechaFutura = datetime.date.today () + datetime.timedelta (days=1)
		traslado = construirTrasladoValido (fechaFutura)

		with self.assertRaises (ValidationError):
			traslado.clean ()

	def test_fecha_futura_impide_guardado (self):
		"""Verifica que save() lanza ValidationError para fechas futuras y no persiste."""
		fechaFutura = datetime.date.today () + datetime.timedelta (days=30)
		traslado = construirTrasladoValido (fechaFutura)

		with self.assertRaises (ValidationError):
			traslado.save ()

		self.assertFalse (TrasladoPaciente.objects.filter (pk=traslado.pk).exists ())

	def test_fecha_futura_lejana_lanza_validation_error (self):
		"""Verifica que una fecha muy lejana en el futuro también es rechazada."""
		fechaFutura = datetime.date.today () + datetime.timedelta (days=365)
		traslado = construirTrasladoValido (fechaFutura)

		with self.assertRaises (ValidationError):
			traslado.clean ()

	def test_fecha_hoy_es_valida (self):
		"""Verifica que la fecha de hoy no es considerada futura y se acepta."""
		traslado = construirTrasladoValido (datetime.date.today ())

		# No debe lanzar excepción
		traslado.clean ()

	def test_fecha_pasada_es_valida (self):
		"""Verifica que una fecha pasada es aceptada sin error."""
		fechaPasada = datetime.date.today () - datetime.timedelta (days=10)
		traslado = construirTrasladoValido (fechaPasada)

		# No debe lanzar excepción
		traslado.clean ()

	def test_error_de_fecha_futura_incluye_campo_fecha (self):
		"""Verifica que el ValidationError de fecha futura referencia el campo 'fecha'."""
		fechaFutura = datetime.date.today () + datetime.timedelta (days=1)
		traslado = construirTrasladoValido (fechaFutura)

		try:
			traslado.clean ()
			self.fail ("Se esperaba ValidationError pero no se lanzó.")
		except ValidationError as error:
			self.assertIn ('fecha', error.message_dict)


class TestBloqueoMesCerrado (TestCase):
	"""Tests unitarios para el bloqueo de escritura en meses cerrados."""

	def setUp (self):
		"""Inicializa los 12 registros de ControlMes antes de cada prueba."""
		crearControlMeses ()

	def _cerrarMes (self, numeroMes):
		"""Cierra el mes indicado actualizando su ControlMes a CERRADO."""
		ControlMes.objects.filter (mes=numeroMes).update (estado='CERRADO')

	def _abrirMes (self, numeroMes):
		"""Abre el mes indicado actualizando su ControlMes a ABIERTO."""
		ControlMes.objects.filter (mes=numeroMes).update (estado='ABIERTO')

	def test_clean_lanza_error_cuando_mes_cerrado (self):
		"""Verifica que clean() lanza ValidationError cuando el mes del registro está cerrado."""
		self._cerrarMes (1)
		fecha = datetime.date (2024, 1, 15)
		traslado = construirTrasladoValido (fecha)

		with self.assertRaises (ValidationError):
			traslado.clean ()

	def test_save_lanza_error_cuando_mes_cerrado (self):
		"""Verifica que save() lanza ValidationError y no persiste en mes cerrado."""
		self._cerrarMes (3)
		fecha = datetime.date (2024, 3, 10)
		traslado = construirTrasladoValido (fecha)

		with self.assertRaises (ValidationError):
			traslado.save ()

		self.assertFalse (TrasladoPaciente.objects.filter (pk=traslado.pk).exists ())

	def test_actualizar_en_mes_cerrado_lanza_error (self):
		"""Verifica que actualizar un registro en un mes cerrado lanza ValidationError."""
		fecha = datetime.date (2024, 4, 5)
		traslado = construirTrasladoValido (fecha)
		traslado.save ()

		# Cerrar el mes después de guardar
		self._cerrarMes (4)

		traslado.observacion = 'Modificación no permitida'
		with self.assertRaises (ValidationError):
			traslado.save ()

		# Verificar que la observación no fue modificada en la base de datos
		trasladoEnBD = TrasladoPaciente.objects.get (pk=traslado.pk)
		self.assertNotEqual (trasladoEnBD.observacion, 'Modificación no permitida')

	def test_mes_abierto_permite_guardado (self):
		"""Verifica que un mes en estado ABIERTO permite guardar registros sin error."""
		self._abrirMes (5)
		fecha = datetime.date (2024, 5, 20)
		traslado = construirTrasladoValido (fecha)

		# No debe lanzar excepción
		traslado.save ()
		self.assertTrue (TrasladoPaciente.objects.filter (pk=traslado.pk).exists ())

	def test_mes_sin_control_mes_permite_guardado (self):
		"""Verifica que si no existe ControlMes para el mes, el guardado no es bloqueado."""
		# Eliminar el ControlMes del mes 6 para simular ausencia
		ControlMes.objects.filter (mes=6).delete ()
		fecha = datetime.date (2024, 6, 15)
		traslado = construirTrasladoValido (fecha)

		# No debe lanzar excepción (ControlMes.DoesNotExist es ignorado)
		traslado.save ()
		self.assertTrue (TrasladoPaciente.objects.filter (pk=traslado.pk).exists ())


class TestControlMesEstadoPorDefecto (TestCase):
	"""Tests unitarios para el estado por defecto de ControlMes."""

	def test_estado_por_defecto_es_abierto (self):
		"""Verifica que un ControlMes recién creado tiene estado ABIERTO por defecto."""
		# Usar un número de mes que no colisione con otros tests; get_or_create
		# para tolerar que crearControlMeses() ya haya insertado este mes.
		controlMes, _ = ControlMes.objects.get_or_create (mes=7)

		self.assertEqual (controlMes.estado, 'ABIERTO')

	def test_esta_cerrado_retorna_false_para_mes_abierto (self):
		"""Verifica que estaCerrado() retorna False cuando el estado es ABIERTO."""
		controlMes, _ = ControlMes.objects.get_or_create (mes=8, defaults={'estado': 'ABIERTO'})
		# Asegurar que está abierto en caso de que ya existiera cerrado
		controlMes.estado = 'ABIERTO'
		controlMes.save ()

		self.assertFalse (controlMes.estaCerrado ())

	def test_esta_cerrado_retorna_true_para_mes_cerrado (self):
		"""Verifica que estaCerrado() retorna True cuando el estado es CERRADO."""
		controlMes, _ = ControlMes.objects.get_or_create (mes=9, defaults={'estado': 'CERRADO'})
		controlMes.estado = 'CERRADO'
		controlMes.save ()

		self.assertTrue (controlMes.estaCerrado ())

	def test_todos_los_meses_inicializados_estan_abiertos (self):
		"""Verifica que todos los meses creados por crearControlMeses() tienen estado ABIERTO."""
		crearControlMeses ()

		mesesCerrados = ControlMes.objects.filter (estado='CERRADO').count ()
		self.assertEqual (mesesCerrados, 0)

	def test_control_mes_cubre_los_12_meses (self):
		"""Verifica que crearControlMeses() crea exactamente 12 registros."""
		crearControlMeses ()

		totalMeses = ControlMes.objects.count ()
		self.assertEqual (totalMeses, 12)


class TestAusenciaAtributoEstadoCierre (TestCase):
	"""Tests unitarios para verificar que TrasladoPaciente no tiene campo estado_cierre."""

	def test_traslado_paciente_no_tiene_atributo_estado_cierre (self):
		"""Verifica que el modelo TrasladoPaciente no define el atributo estado_cierre."""
		self.assertFalse (
			hasattr (TrasladoPaciente, 'estado_cierre'),
			"TrasladoPaciente no debe tener el atributo 'estado_cierre'.",
		)

	def test_instancia_traslado_no_tiene_atributo_estado_cierre (self):
		"""Verifica que una instancia de TrasladoPaciente no expone estado_cierre."""
		traslado = TrasladoPaciente ()

		self.assertFalse (
			hasattr (traslado, 'estado_cierre'),
			"Una instancia de TrasladoPaciente no debe tener el atributo 'estado_cierre'.",
		)

	def test_campos_del_modelo_no_incluyen_estado_cierre (self):
		"""Verifica que los campos del modelo no incluyen ninguno llamado estado_cierre."""
		nombresCampos = [campo.name for campo in TrasladoPaciente._meta.get_fields ()]

		self.assertNotIn (
			'estado_cierre',
			nombresCampos,
			"El campo 'estado_cierre' no debe existir en TrasladoPaciente.",
		)
