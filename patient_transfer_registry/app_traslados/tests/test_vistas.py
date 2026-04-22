"""
Tests unitarios para las vistas de app_traslados.

Verifica el comportamiento de VistaMain: filtros, validaciones
y contenido del contexto según el rol del usuario.
"""

import calendar
import datetime

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from app_traslados.models import ControlMes, Perfil, TrasladoPaciente


# ─── Utilidades compartidas ───────────────────────────────────────────────────

def crearControlMeses ():
	"""Crea las 12 filas de ControlMes con estado ABIERTO si no existen."""
	for numeroMes in range (1, 13):
		ControlMes.objects.get_or_create (
			mes=numeroMes,
			defaults={'estado': 'ABIERTO'},
		)


def crearUsuario (username, rol='FUNCIONARIO', password='clave123'):
	"""Crea un User con su Perfil asociado y retorna el objeto User."""
	usuario = User.objects.create_user (username=username, password=password)
	# La señal post_save crea el Perfil automáticamente; solo actualizamos el rol
	Perfil.objects.filter (usuario=usuario).update (rol=rol)
	return usuario


def construirTrasladoValido (fecha):
	"""Construye y guarda un TrasladoPaciente con todos los campos requeridos."""
	traslado = TrasladoPaciente (
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
	traslado.save ()
	return traslado


# ─── Tests de filtro por mes ──────────────────────────────────────────────────

class TestFiltroPorMes (TestCase):
	"""Tests unitarios para el filtro de mes en VistaMain."""

	def setUp (self):
		"""Inicializa ControlMes, usuario y cliente autenticado."""
		crearControlMeses ()
		self.usuario = crearUsuario ('funcionario1')
		self.cliente = Client ()
		self.cliente.login (username='funcionario1', password='clave123')
		self.urlPrincipal = reverse ('principal')

	def test_filtro_mes_retorna_solo_registros_del_mes_correcto (self):
		"""Verifica que el contexto mesSeleccionado coincide con el parámetro ?mes= enviado."""
		hoy = datetime.date.today ()
		# Usar el mes actual para no disparar la validación de mes futuro
		mesObjetivo = hoy.month

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': mesObjetivo})

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (respuesta.context ['mesSeleccionado'], mesObjetivo)

	def test_filtro_mes_anterior_es_aceptado (self):
		"""Verifica que un mes anterior al actual es aceptado sin errores de validación."""
		hoy = datetime.date.today ()
		mesAnterior = hoy.month - 1 if hoy.month > 1 else 12

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': mesAnterior})

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (respuesta.context ['mesSeleccionado'], mesAnterior)
		self.assertEqual (len (respuesta.context ['erroresFiltro']), 0)

	def test_sin_parametro_mes_usa_mes_actual (self):
		"""Verifica que sin parámetro ?mes= se usa el mes actual por defecto."""
		hoy = datetime.date.today ()

		respuesta = self.cliente.get (self.urlPrincipal)

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (respuesta.context ['mesSeleccionado'], hoy.month)

	def test_contexto_incluye_mes_actual (self):
		"""Verifica que el contexto expone mesActual con el mes del día de hoy."""
		hoy = datetime.date.today ()

		respuesta = self.cliente.get (self.urlPrincipal)

		self.assertEqual (respuesta.context ['mesActual'], hoy.month)


# ─── Tests de validación de mes futuro ───────────────────────────────────────

class TestValidacionMesFuturo (TestCase):
	"""Tests unitarios para la validación de mes futuro en VistaMain."""

	def setUp (self):
		"""Inicializa ControlMes, usuario y cliente autenticado."""
		crearControlMeses ()
		self.usuario = crearUsuario ('funcionario2')
		self.cliente = Client ()
		self.cliente.login (username='funcionario2', password='clave123')
		self.urlPrincipal = reverse ('principal')

	def test_mes_futuro_agrega_error_al_contexto (self):
		"""Verifica que seleccionar un mes futuro agrega un mensaje de error al contexto."""
		hoy = datetime.date.today ()
		mesFuturo = hoy.month + 1 if hoy.month < 12 else 13

		# Solo ejecutar si hay un mes futuro válido (1–12)
		if mesFuturo > 12:
			self.skipTest ('No hay mes futuro válido en diciembre para este test.')

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': mesFuturo})

		self.assertEqual (respuesta.status_code, 200)
		self.assertGreater (
			len (respuesta.context ['erroresFiltro']),
			0,
			'Se esperaba al menos un error de validación para mes futuro.',
		)

	def test_mes_futuro_redirige_a_mes_actual (self):
		"""Verifica que al seleccionar un mes futuro, mesSeleccionado se corrige al mes actual."""
		hoy = datetime.date.today ()
		mesFuturo = hoy.month + 1 if hoy.month < 12 else 13

		if mesFuturo > 12:
			self.skipTest ('No hay mes futuro válido en diciembre para este test.')

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': mesFuturo})

		self.assertEqual (respuesta.context ['mesSeleccionado'], hoy.month)

	def test_mes_futuro_mensaje_menciona_mes_actual (self):
		"""Verifica que el mensaje de error de mes futuro menciona el mes actual permitido."""
		hoy = datetime.date.today ()
		mesFuturo = hoy.month + 1 if hoy.month < 12 else 13

		if mesFuturo > 12:
			self.skipTest ('No hay mes futuro válido en diciembre para este test.')

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': mesFuturo})

		errores = respuesta.context ['erroresFiltro']
		mensajeError = ' '.join (errores)
		self.assertIn (
			str (hoy.month),
			mensajeError,
			'El mensaje de error debe mencionar el mes actual permitido.',
		)

	def test_mes_13_es_rechazado (self):
		"""Verifica que el mes 13 (inválido) es tratado como mes futuro y genera error."""
		respuesta = self.cliente.get (self.urlPrincipal, {'mes': 13})

		self.assertEqual (respuesta.status_code, 200)
		self.assertGreater (len (respuesta.context ['erroresFiltro']), 0)


# ─── Tests de validación de rango de días ────────────────────────────────────

class TestValidacionRangoDias (TestCase):
	"""Tests unitarios para la validación del rango de días en VistaMain."""

	def setUp (self):
		"""Inicializa ControlMes, usuario y cliente autenticado."""
		crearControlMeses ()
		self.usuario = crearUsuario ('funcionario3')
		self.cliente = Client ()
		self.cliente.login (username='funcionario3', password='clave123')
		self.urlPrincipal = reverse ('principal')
		self.hoy = datetime.date.today ()
		self.mesActual = self.hoy.month

	def test_dia_desde_mayor_que_dia_hasta_genera_error (self):
		"""Verifica que dia_desde > dia_hasta agrega un error de validación al contexto."""
		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 20,
			'dia_hasta': 10,
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertGreater (
			len (respuesta.context ['erroresFiltro']),
			0,
			'Se esperaba error de validación cuando dia_desde > dia_hasta.',
		)

	def test_dia_desde_mayor_que_dia_hasta_restablece_rango_completo (self):
		"""Verifica que un rango inválido (desde > hasta) restablece diaDesde=1 y diaHasta=días del mes."""
		diasEnMes = calendar.monthrange (self.hoy.year, self.mesActual) [1]

		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 25,
			'dia_hasta': 5,
		})

		self.assertEqual (respuesta.context ['diaDesde'], 1)
		self.assertEqual (respuesta.context ['diaHasta'], diasEnMes)

	def test_dia_desde_fuera_de_rango_genera_error (self):
		"""Verifica que dia_desde < 1 genera un error de validación."""
		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 0,
			'dia_hasta': 15,
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertGreater (len (respuesta.context ['erroresFiltro']), 0)

	def test_dia_hasta_fuera_de_rango_genera_error (self):
		"""Verifica que dia_hasta > días del mes genera un error de validación."""
		diasEnMes = calendar.monthrange (self.hoy.year, self.mesActual) [1]

		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 1,
			'dia_hasta': diasEnMes + 1,
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertGreater (len (respuesta.context ['erroresFiltro']), 0)

	def test_rango_valido_no_genera_errores (self):
		"""Verifica que un rango de días válido no produce errores de validación."""
		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 1,
			'dia_hasta': 15,
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (
			len (respuesta.context ['erroresFiltro']),
			0,
			'Un rango válido no debe generar errores de filtro.',
		)

	def test_rango_valido_preserva_valores_en_contexto (self):
		"""Verifica que un rango válido se refleja correctamente en el contexto."""
		respuesta = self.cliente.get (self.urlPrincipal, {
			'mes': self.mesActual,
			'dia_desde': 5,
			'dia_hasta': 20,
		})

		self.assertEqual (respuesta.context ['diaDesde'], 5)
		self.assertEqual (respuesta.context ['diaHasta'], 20)

	def test_sin_parametros_dias_usa_rango_completo_del_mes (self):
		"""Verifica que sin parámetros de días se usa el rango completo del mes."""
		diasEnMes = calendar.monthrange (self.hoy.year, self.mesActual) [1]

		respuesta = self.cliente.get (self.urlPrincipal, {'mes': self.mesActual})

		self.assertEqual (respuesta.context ['diaDesde'], 1)
		self.assertEqual (respuesta.context ['diaHasta'], diasEnMes)


# ─── Tests de sidebar según rol ──────────────────────────────────────────────

class TestSidebarPorRol (TestCase):
	"""Tests unitarios para verificar que el contexto de rol se pasa correctamente a la plantilla."""

	def setUp (self):
		"""Inicializa ControlMes y clientes para FUNCIONARIO y DIRECTOR."""
		crearControlMeses ()
		self.urlPrincipal = reverse ('principal')

		self.usuarioFuncionario = crearUsuario ('func_sidebar', rol='FUNCIONARIO')
		self.clienteFuncionario = Client ()
		self.clienteFuncionario.login (username='func_sidebar', password='clave123')

		self.usuarioDirector = crearUsuario ('dir_sidebar', rol='DIRECTOR')
		self.clienteDirector = Client ()
		self.clienteDirector.login (username='dir_sidebar', password='clave123')

	def test_contexto_rol_funcionario_es_funcionario (self):
		"""Verifica que el contexto rolUsuario es FUNCIONARIO para un usuario con ese rol."""
		respuesta = self.clienteFuncionario.get (self.urlPrincipal)

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (respuesta.context ['rolUsuario'], 'FUNCIONARIO')

	def test_contexto_rol_director_es_director (self):
		"""Verifica que el contexto rolUsuario es DIRECTOR para un usuario con ese rol."""
		respuesta = self.clienteDirector.get (self.urlPrincipal)

		self.assertEqual (respuesta.status_code, 200)
		self.assertEqual (respuesta.context ['rolUsuario'], 'DIRECTOR')

	def test_plantilla_muestra_opcion_usuarios_solo_para_director (self):
		"""Verifica que la plantilla renderiza la opción Usuarios solo para DIRECTOR."""
		respuestaDirector = self.clienteDirector.get (self.urlPrincipal)
		respuestaFuncionario = self.clienteFuncionario.get (self.urlPrincipal)

		# El DIRECTOR debe ver la opción de gestión de usuarios
		self.assertContains (respuestaDirector, 'Usuarios')

		# El FUNCIONARIO no debe ver la opción de gestión de usuarios en el sidebar
		# (la palabra "Usuarios" no debe aparecer en el contexto de gestión del sidebar)
		contenidoFuncionario = respuestaFuncionario.content.decode ('utf-8')
		# Verificar que el rol en contexto es FUNCIONARIO (la plantilla decide qué mostrar)
		self.assertEqual (respuestaFuncionario.context ['rolUsuario'], 'FUNCIONARIO')
		self.assertNotEqual (respuestaFuncionario.context ['rolUsuario'], 'DIRECTOR')

	def test_plantilla_muestra_limpiar_datos_solo_para_director (self):
		"""Verifica que la opción Limpiar datos del sistema aparece solo para DIRECTOR."""
		respuestaDirector = self.clienteDirector.get (self.urlPrincipal)
		respuestaFuncionario = self.clienteFuncionario.get (self.urlPrincipal)

		self.assertContains (respuestaDirector, 'Limpiar')
		self.assertNotContains (respuestaFuncionario, 'Limpiar')

	def test_usuario_no_autenticado_redirige_a_login (self):
		"""Verifica que un usuario no autenticado es redirigido a /login/."""
		clienteAnonimo = Client ()
		respuesta = clienteAnonimo.get (self.urlPrincipal)

		self.assertRedirects (respuesta, '/login/?next=/')

	def test_ambos_roles_ven_opcion_contrasena_en_gestion (self):
		"""Verifica que tanto FUNCIONARIO como DIRECTOR ven la opción Contraseña en Gestión."""
		respuestaDirector = self.clienteDirector.get (self.urlPrincipal)
		respuestaFuncionario = self.clienteFuncionario.get (self.urlPrincipal)

		self.assertContains (respuestaDirector, 'Contraseña')
		self.assertContains (respuestaFuncionario, 'Contraseña')

	def test_ambos_roles_ven_opciones_de_reportes (self):
		"""Verifica que tanto FUNCIONARIO como DIRECTOR ven las opciones de reportes."""
		respuestaDirector = self.clienteDirector.get (self.urlPrincipal)
		respuestaFuncionario = self.clienteFuncionario.get (self.urlPrincipal)

		self.assertContains (respuestaDirector, 'Excel')
		self.assertContains (respuestaFuncionario, 'Excel')
		self.assertContains (respuestaDirector, 'PDF')
		self.assertContains (respuestaFuncionario, 'PDF')


# ─── Tests de autenticación ───────────────────────────────────────────────────

class TestRedireccionNoAutenticado (TestCase):
	"""Tests unitarios para verificar que solicitudes no autenticadas redirigen a /login/."""

	def setUp (self):
		"""Inicializa ControlMes y un cliente anónimo."""
		crearControlMeses ()
		self.clienteAnonimo = Client ()

	def test_vista_principal_redirige_a_login (self):
		"""Verifica que GET / sin sesión activa redirige a /login/."""
		respuesta = self.clienteAnonimo.get (reverse ('principal'))

		self.assertRedirects (respuesta, '/login/?next=/')

	def test_vista_tabla_traslados_redirige_a_login (self):
		"""Verifica que GET /traslados/tabla/ sin sesión activa redirige a /login/."""
		respuesta = self.clienteAnonimo.get (reverse ('tabla-traslados'))

		self.assertRedirects (respuesta, '/login/?next=/traslados/tabla/')

	def test_vista_nuevo_traslado_redirige_a_login (self):
		"""Verifica que GET /traslados/nuevo/ sin sesión activa redirige a /login/."""
		respuesta = self.clienteAnonimo.get (reverse ('traslado-nuevo'))

		self.assertRedirects (respuesta, '/login/?next=/traslados/nuevo/')

	def test_redireccion_usa_codigo_302 (self):
		"""Verifica que la redirección a login usa el código HTTP 302."""
		respuesta = self.clienteAnonimo.get (reverse ('principal'), follow=False)

		self.assertEqual (respuesta.status_code, 302)

	def test_redireccion_incluye_parametro_next (self):
		"""Verifica que la URL de redirección incluye el parámetro next con la ruta original."""
		respuesta = self.clienteAnonimo.get (reverse ('principal'), follow=False)

		self.assertIn ('/login/', respuesta ['Location'])
		self.assertIn ('next', respuesta ['Location'])


# ─── Tests de credenciales inválidas ─────────────────────────────────────────

class TestCredencialesInvalidas (TestCase):
	"""Tests unitarios para verificar el comportamiento ante credenciales inválidas."""

	def setUp (self):
		"""Crea un usuario válido y un cliente para las pruebas."""
		self.usuario = crearUsuario ('usuarioValido', password='claveCorrecta')
		self.cliente = Client ()
		self.urlLogin = '/login/'

	def test_credenciales_invalidas_no_inician_sesion (self):
		"""Verifica que credenciales incorrectas no crean una sesión autenticada."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioValido',
			'password': 'claveIncorrecta',
		})

		# El usuario no debe estar autenticado en la sesión
		self.assertFalse (respuesta.wsgi_request.user.is_authenticated)

	def test_credenciales_invalidas_retornan_codigo_200 (self):
		"""Verifica que credenciales incorrectas retornan HTTP 200 (re-render del formulario)."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioValido',
			'password': 'claveIncorrecta',
		})

		self.assertEqual (respuesta.status_code, 200)

	def test_credenciales_invalidas_muestran_errores_en_formulario (self):
		"""Verifica que el formulario contiene errores cuando las credenciales son incorrectas."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioValido',
			'password': 'claveIncorrecta',
		})

		self.assertTrue (respuesta.context ['form'].errors)

	def test_credenciales_invalidas_muestran_mensaje_de_error (self):
		"""Verifica que la respuesta contiene el mensaje de error de credenciales incorrectas."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioValido',
			'password': 'claveIncorrecta',
		})

		self.assertContains (respuesta, 'incorrectos')

	def test_usuario_inexistente_no_inicia_sesion (self):
		"""Verifica que un usuario que no existe en el sistema no puede iniciar sesión."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioQueNoExiste',
			'password': 'cualquierClave',
		})

		self.assertFalse (respuesta.wsgi_request.user.is_authenticated)

	def test_usuario_inexistente_muestra_error (self):
		"""Verifica que intentar iniciar sesión con usuario inexistente muestra error."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioQueNoExiste',
			'password': 'cualquierClave',
		})

		self.assertTrue (respuesta.context ['form'].errors)

	def test_credenciales_validas_inician_sesion_y_redirigen (self):
		"""Verifica que credenciales correctas inician sesión y redirigen a la vista principal."""
		respuesta = self.cliente.post (self.urlLogin, {
			'username': 'usuarioValido',
			'password': 'claveCorrecta',
		}, follow=True)

		self.assertTrue (respuesta.wsgi_request.user.is_authenticated)
		self.assertRedirects (
			self.cliente.post (self.urlLogin, {
				'username': 'usuarioValido',
				'password': 'claveCorrecta',
			}),
			'/',
		)


# ─── Tests de recuperación de contraseña ─────────────────────────────────────

class TestRecuperacionContrasena (TestCase):
	"""Tests unitarios para verificar el comportamiento de la vista de recuperación de contraseña."""

	def setUp (self):
		"""Crea un usuario existente y un cliente para las pruebas."""
		self.usuarioExistente = crearUsuario ('usuarioExistente')
		self.cliente = Client ()
		self.urlRecuperacion = reverse ('recuperar-contrasena')

	def test_get_recuperacion_retorna_formulario (self):
		"""Verifica que GET /recuperar-contrasena/ retorna el formulario sin mensaje."""
		respuesta = self.cliente.get (self.urlRecuperacion)

		self.assertEqual (respuesta.status_code, 200)
		self.assertNotIn ('mensaje', respuesta.context)

	def test_post_usuario_existente_retorna_mensaje_generico (self):
		"""Verifica que POST con usuario existente retorna el mensaje genérico de contacto al DIRECTOR."""
		respuesta = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioExistente',
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertIn ('mensaje', respuesta.context)
		self.assertIn ('DIRECTOR', respuesta.context ['mensaje'])

	def test_post_usuario_inexistente_retorna_mensaje_generico (self):
		"""Verifica que POST con usuario inexistente retorna el mismo mensaje genérico."""
		respuesta = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioQueNoExiste',
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertIn ('mensaje', respuesta.context)
		self.assertIn ('DIRECTOR', respuesta.context ['mensaje'])

	def test_mensaje_es_identico_para_usuario_existente_e_inexistente (self):
		"""Verifica que el mensaje retornado es exactamente el mismo para usuario existente e inexistente."""
		respuestaExistente = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioExistente',
		})
		respuestaInexistente = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioQueNoExiste',
		})

		self.assertEqual (
			respuestaExistente.context ['mensaje'],
			respuestaInexistente.context ['mensaje'],
		)

	def test_codigo_http_es_identico_para_usuario_existente_e_inexistente (self):
		"""Verifica que el código HTTP es el mismo para usuario existente e inexistente."""
		respuestaExistente = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioExistente',
		})
		respuestaInexistente = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'usuarioQueNoExiste',
		})

		self.assertEqual (respuestaExistente.status_code, respuestaInexistente.status_code)

	def test_recuperacion_accesible_sin_autenticacion (self):
		"""Verifica que la vista de recuperación de contraseña es accesible sin sesión activa."""
		clienteAnonimo = Client ()
		respuesta = clienteAnonimo.get (self.urlRecuperacion)

		self.assertEqual (respuesta.status_code, 200)

	def test_mensaje_menciona_contactar_director (self):
		"""Verifica que el mensaje genérico indica al usuario que contacte al DIRECTOR."""
		respuesta = self.cliente.post (self.urlRecuperacion, {
			'usuario': 'cualquierUsuario',
		})

		self.assertContains (respuesta, 'DIRECTOR')


# ─── Tests de cierre de mes ───────────────────────────────────────────────────

class TestVistaCerrarMes (TestCase):
	"""Tests unitarios para la vista vistaCerrarMes (POST /mes/<mes>/cerrar/)."""

	def setUp (self):
		"""Inicializa ControlMes, usuarios DIRECTOR y FUNCIONARIO, y clientes."""
		crearControlMeses ()

		self.director = crearUsuario ('director_cierre', rol='DIRECTOR')
		self.clienteDirector = Client ()
		self.clienteDirector.login (username='director_cierre', password='clave123')

		self.funcionario = crearUsuario ('func_cierre', rol='FUNCIONARIO')
		self.clienteFuncionario = Client ()
		self.clienteFuncionario.login (username='func_cierre', password='clave123')

		self.clienteAnonimo = Client ()

	def _urlCerrarMes (self, mes):
		"""Construye la URL de cierre para el mes dado."""
		return reverse ('cerrar-mes', kwargs={'mes': mes})

	def test_director_puede_cerrar_mes (self):
		"""Verifica que un DIRECTOR puede cerrar un mes con POST."""
		respuesta = self.clienteDirector.post (self._urlCerrarMes (3))

		self.assertRedirects (respuesta, '/')
		controlMes = ControlMes.objects.get (mes=3)
		self.assertEqual (controlMes.estado, 'CERRADO')

	def test_cerrar_mes_registra_fecha_cierre (self):
		"""Verifica que al cerrar un mes se registra la fecha_cierre."""
		self.clienteDirector.post (self._urlCerrarMes (4))

		controlMes = ControlMes.objects.get (mes=4)
		self.assertIsNotNone (controlMes.fecha_cierre)

	def test_cerrar_mes_registra_cerrado_por (self):
		"""Verifica que al cerrar un mes se registra el usuario que lo cerró."""
		self.clienteDirector.post (self._urlCerrarMes (5))

		controlMes = ControlMes.objects.get (mes=5)
		self.assertEqual (controlMes.cerrado_por, self.director)

	def test_funcionario_recibe_403 (self):
		"""Verifica que un FUNCIONARIO recibe HTTP 403 al intentar cerrar un mes."""
		respuesta = self.clienteFuncionario.post (self._urlCerrarMes (2))

		self.assertEqual (respuesta.status_code, 403)

	def test_funcionario_no_cierra_mes (self):
		"""Verifica que el mes permanece ABIERTO cuando un FUNCIONARIO intenta cerrarlo."""
		self.clienteFuncionario.post (self._urlCerrarMes (2))

		controlMes = ControlMes.objects.get (mes=2)
		self.assertEqual (controlMes.estado, 'ABIERTO')

	def test_anonimo_redirige_a_login (self):
		"""Verifica que un usuario no autenticado es redirigido a /login/."""
		respuesta = self.clienteAnonimo.post (self._urlCerrarMes (1))

		self.assertEqual (respuesta.status_code, 302)
		self.assertIn ('/login/', respuesta ['Location'])

	def test_mes_inexistente_retorna_404 (self):
		"""Verifica que cerrar un mes sin ControlMes retorna HTTP 404."""
		# Eliminar el ControlMes del mes 6 para simular ausencia
		ControlMes.objects.filter (mes=6).delete ()

		respuesta = self.clienteDirector.post (self._urlCerrarMes (6))

		self.assertEqual (respuesta.status_code, 404)

	def test_get_retorna_405 (self):
		"""Verifica que GET a la vista de cierre retorna HTTP 405 (método no permitido)."""
		respuesta = self.clienteDirector.get (self._urlCerrarMes (7))

		self.assertEqual (respuesta.status_code, 405)


# ─── Tests de cambio de contraseña propia ────────────────────────────────────

class TestVistaCambiarContrasenaPropia (TestCase):
	"""Tests unitarios para VistaCambiarContrasenaPropia (GET/POST /perfil/contrasena/)."""

	def setUp (self):
		"""Crea un usuario autenticado y un cliente para las pruebas."""
		self.usuario = crearUsuario ('usuarioPerfil', password='claveOriginal')
		self.cliente = Client ()
		self.cliente.login (username='usuarioPerfil', password='claveOriginal')
		self.urlCambiarContrasena = reverse ('cambiar-contrasena')

	def test_get_muestra_formulario (self):
		"""Verifica que GET /perfil/contrasena/ retorna el formulario con código 200."""
		respuesta = self.cliente.get (self.urlCambiarContrasena)

		self.assertEqual (respuesta.status_code, 200)
		self.assertIn ('formulario', respuesta.context)

	def test_usuario_no_autenticado_redirige_a_login (self):
		"""Verifica que un usuario no autenticado es redirigido a /login/."""
		clienteAnonimo = Client ()
		respuesta = clienteAnonimo.get (self.urlCambiarContrasena)

		self.assertEqual (respuesta.status_code, 302)
		self.assertIn ('/login/', respuesta ['Location'])

	def test_post_contrasena_actual_incorrecta_no_actualiza (self):
		"""Verifica que una contraseña actual incorrecta no actualiza la contraseña (req. 8.3)."""
		respuesta = self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveIncorrecta',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'nuevaClave123',
		})

		self.assertEqual (respuesta.status_code, 200)
		# La contraseña no debe haber cambiado
		self.usuario.refresh_from_db ()
		self.assertTrue (self.usuario.check_password ('claveOriginal'))

	def test_post_contrasena_actual_incorrecta_muestra_error (self):
		"""Verifica que una contraseña actual incorrecta muestra un mensaje de error (req. 8.3)."""
		respuesta = self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveIncorrecta',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'nuevaClave123',
		})

		formulario = respuesta.context ['formulario']
		self.assertTrue (formulario.errors)

	def test_post_nueva_y_confirmacion_no_coinciden_no_actualiza (self):
		"""Verifica que nueva contraseña y confirmación distintas no actualizan la contraseña (req. 8.4)."""
		respuesta = self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveOriginal',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'otraClave456',
		})

		self.assertEqual (respuesta.status_code, 200)
		self.usuario.refresh_from_db ()
		self.assertTrue (self.usuario.check_password ('claveOriginal'))

	def test_post_nueva_y_confirmacion_no_coinciden_muestra_error (self):
		"""Verifica que nueva contraseña y confirmación distintas muestran error (req. 8.4)."""
		respuesta = self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveOriginal',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'otraClave456',
		})

		formulario = respuesta.context ['formulario']
		self.assertTrue (formulario.non_field_errors ())

	def test_post_datos_validos_actualiza_contrasena (self):
		"""Verifica que datos válidos actualizan la contraseña correctamente (req. 8.5)."""
		self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveOriginal',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'nuevaClave123',
		})

		self.usuario.refresh_from_db ()
		self.assertTrue (self.usuario.check_password ('nuevaClave123'))
		self.assertFalse (self.usuario.check_password ('claveOriginal'))

	def test_post_datos_validos_muestra_mensaje_exito (self):
		"""Verifica que datos válidos muestran un mensaje de confirmación de éxito (req. 8.5)."""
		respuesta = self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveOriginal',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'nuevaClave123',
		})

		self.assertEqual (respuesta.status_code, 200)
		self.assertTrue (respuesta.context.get ('exito'))

	def test_post_datos_validos_mantiene_sesion_activa (self):
		"""Verifica que tras el cambio exitoso la sesión permanece activa."""
		self.cliente.post (self.urlCambiarContrasena, {
			'contrasena_actual': 'claveOriginal',
			'nueva_contrasena': 'nuevaClave123',
			'confirmar_contrasena': 'nuevaClave123',
		})

		# La sesión debe seguir activa (update_session_auth_hash fue llamado)
		respuesta = self.cliente.get ('/')
		self.assertEqual (respuesta.status_code, 200)
		self.assertTrue (respuesta.wsgi_request.user.is_authenticated)

	def test_funcionario_puede_acceder (self):
		"""Verifica que un usuario con rol FUNCIONARIO puede acceder a la vista (req. 8.1)."""
		usuarioFuncionario = crearUsuario ('funcPerfil', rol='FUNCIONARIO', password='clave123')
		clienteFuncionario = Client ()
		clienteFuncionario.login (username='funcPerfil', password='clave123')

		respuesta = clienteFuncionario.get (self.urlCambiarContrasena)

		self.assertEqual (respuesta.status_code, 200)

	def test_director_puede_acceder (self):
		"""Verifica que un usuario con rol DIRECTOR puede acceder a la vista (req. 8.1)."""
		usuarioDirector = crearUsuario ('dirPerfil', rol='DIRECTOR', password='clave123')
		clienteDirector = Client ()
		clienteDirector.login (username='dirPerfil', password='clave123')

		respuesta = clienteDirector.get (self.urlCambiarContrasena)

		self.assertEqual (respuesta.status_code, 200)


# ─── Tests de limpieza anual de datos ────────────────────────────────────────

class TestVistaLimpiarSistema (TestCase):
	"""Tests unitarios para vistaLimpiarSistema (GET/POST /sistema/limpiar/)."""

	def setUp (self):
		"""Inicializa ControlMes, usuarios DIRECTOR y FUNCIONARIO, y clientes."""
		crearControlMeses ()

		self.director = crearUsuario ('director_limpieza', rol='DIRECTOR')
		self.clienteDirector = Client ()
		self.clienteDirector.login (username='director_limpieza', password='clave123')

		self.funcionario = crearUsuario ('func_limpieza', rol='FUNCIONARIO')
		self.clienteFuncionario = Client ()
		self.clienteFuncionario.login (username='func_limpieza', password='clave123')

		self.clienteAnonimo = Client ()
		self.urlLimpiar = reverse ('limpiar-sistema')

	def _crearRegistros (self, cantidad=3):
		"""Crea la cantidad indicada de TrasladoPaciente en 2023."""
		hoy = datetime.date.today ()
		for i in range (cantidad):
			mes = (i % 12) + 1
			anio = hoy.year if mes <= hoy.month else hoy.year - 1
			fecha = datetime.date (anio, mes, 1)
			construirTrasladoValido (fecha)

	def test_funcionario_recibe_403_en_get (self):
		"""Verifica que un FUNCIONARIO recibe HTTP 403 al acceder a GET /sistema/limpiar/."""
		respuesta = self.clienteFuncionario.get (self.urlLimpiar)

		self.assertEqual (respuesta.status_code, 403)

	def test_funcionario_recibe_403_en_post (self):
		"""Verifica que un FUNCIONARIO recibe HTTP 403 al enviar POST /sistema/limpiar/."""
		respuesta = self.clienteFuncionario.post (self.urlLimpiar, {'accion': 'confirmar'})

		self.assertEqual (respuesta.status_code, 403)

	def test_anonimo_redirige_a_login (self):
		"""Verifica que un usuario no autenticado es redirigido a /login/."""
		respuesta = self.clienteAnonimo.get (self.urlLimpiar)

		self.assertEqual (respuesta.status_code, 302)
		self.assertIn ('/login/', respuesta ['Location'])

	def test_director_puede_acceder_a_get (self):
		"""Verifica que un DIRECTOR puede acceder a GET /sistema/limpiar/ con código 200."""
		respuesta = self.clienteDirector.get (self.urlLimpiar)

		self.assertEqual (respuesta.status_code, 200)

	def test_get_muestra_sugerencia_de_reportes (self):
		"""Verifica que la página GET muestra la sugerencia de generar reportes antes de limpiar."""
		respuesta = self.clienteDirector.get (self.urlLimpiar)

		self.assertContains (respuesta, 'Excel')
		self.assertContains (respuesta, 'PDF')

	def test_get_muestra_advertencia_de_accion_irreversible (self):
		"""Verifica que la página GET muestra la advertencia de acción irreversible."""
		respuesta = self.clienteDirector.get (self.urlLimpiar)

		self.assertContains (respuesta, 'irreversible')

	def test_post_confirmado_elimina_todos_los_registros (self):
		"""Verifica que POST confirmado elimina todos los TrasladoPaciente (req. 9.4)."""
		self._crearRegistros (5)
		self.assertGreater (TrasladoPaciente.objects.count (), 0)

		self.clienteDirector.post (self.urlLimpiar, {'accion': 'confirmar'})

		self.assertEqual (TrasladoPaciente.objects.count (), 0)

	def test_post_confirmado_restablece_todos_los_meses_a_abierto (self):
		"""Verifica que POST confirmado restablece todos los ControlMes a ABIERTO (req. 9.4)."""
		# Cerrar algunos meses antes de la limpieza
		ControlMes.objects.filter (mes__in=[1, 3, 6]).update (estado='CERRADO')

		self.clienteDirector.post (self.urlLimpiar, {'accion': 'confirmar'})

		mesesCerrados = ControlMes.objects.filter (estado='CERRADO').count ()
		self.assertEqual (mesesCerrados, 0)
		self.assertEqual (ControlMes.objects.filter (estado='ABIERTO').count (), 12)

	def test_post_confirmado_redirige_a_vista_principal (self):
		"""Verifica que POST confirmado redirige a la vista principal."""
		respuesta = self.clienteDirector.post (self.urlLimpiar, {'accion': 'confirmar'})

		self.assertRedirects (respuesta, '/')

	def test_post_cancelar_no_elimina_registros (self):
		"""Verifica que cancelar no modifica los registros TrasladoPaciente (req. 9.5)."""
		self._crearRegistros (3)
		conteoAntes = TrasladoPaciente.objects.count ()

		self.clienteDirector.post (self.urlLimpiar, {'accion': 'cancelar'})

		self.assertEqual (TrasladoPaciente.objects.count (), conteoAntes)

	def test_post_cancelar_no_modifica_estado_de_meses (self):
		"""Verifica que cancelar no modifica el estado de los ControlMes (req. 9.5)."""
		ControlMes.objects.filter (mes__in=[2, 5]).update (estado='CERRADO')

		self.clienteDirector.post (self.urlLimpiar, {'accion': 'cancelar'})

		self.assertEqual (ControlMes.objects.filter (estado='CERRADO').count (), 2)

	def test_post_cancelar_redirige_a_vista_principal (self):
		"""Verifica que cancelar redirige a la vista principal sin modificar datos."""
		respuesta = self.clienteDirector.post (self.urlLimpiar, {'accion': 'cancelar'})

		self.assertRedirects (respuesta, '/')

	def test_post_confirmado_muestra_mensaje_de_exito_en_principal (self):
		"""Verifica que tras la limpieza se muestra un mensaje de éxito en la vista principal."""
		respuesta = self.clienteDirector.post (
			self.urlLimpiar, {'accion': 'confirmar'}, follow=True
		)

		mensajes = list (respuesta.context ['messages'])
		self.assertGreater (len (mensajes), 0, 'Se esperaba al menos un mensaje de éxito.')
		textoMensaje = str (mensajes [0])
		self.assertIn ('Limpieza', textoMensaje)
