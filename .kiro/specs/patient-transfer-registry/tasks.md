# Plan de Implementación: Sistema de Registro de Traslados de Pacientes

## Descripción General

Implementación incremental de la aplicación Django `traslados` siguiendo el patrón MVT con HTMX para actualizaciones parciales. Cada tarea construye sobre la anterior, comenzando por la estructura del proyecto y los modelos, avanzando por las vistas y plantillas, hasta los reportes y la limpieza de datos.

## Tareas

- [x] 1. Configurar estructura del proyecto Django y la app `traslados`
  - Crear el proyecto Django con el paquete de configuración `config/` (settings.py, urls.py, wsgi.py)
  - Crear la app `traslados` con la estructura de directorios: `services/`, `templates/traslados/partials/`, `static/traslados/css/` y `static/traslados/js/`
  - Registrar `traslados` en `INSTALLED_APPS`
  - Configurar `TEMPLATES`, `STATIC_URL`, `MEDIA_ROOT`, `LOGIN_URL = '/login/'` y `LOGIN_REDIRECT_URL = '/'` en settings.py
  - Instalar dependencias: `django`, `openpyxl`, `xhtml2pdf` (versiones fijas en requirements.txt)
  - Crear `base.html` con bloque de contenido, CDN de Tailwind CSS y bloque para scripts HTMX
  - _Requirements: 1.1, 2.1_

- [x] 2. Implementar modelos de datos y señales
  - [x] 2.1 Implementar el modelo `Perfil` con OneToOneField a `User` y campo `role` (FUNCIONARIO/DIRECTOR)
    - Agregar señal `post_save` en `User` para auto-crear/actualizar `Perfil`
    - Incluir docstring en la clase y en cada método
    - _Requirements: 1.3, 7.3_

  - [x] 2.2 Implementar el modelo `ControlMes` con campos `mes` (unique, 1–12), `estado` (ABIERTO/CERRADO), `fecha_cierre` y `cerrado_por`
    - Crear comando de gestión `inicializar_meses` (o señal en `AppConfig.ready()`) que garantice las 12 filas de `ControlMes` al iniciar
    - Incluir docstring en la clase y en cada método
    - _Requirements: 5.1_

  - [x] 2.3 Implementar el modelo `TrasladoPaciente` con los 15 campos más el campo derivado `mes`
    - Implementar `save()` para derivar `mes` desde `fecha` antes de llamar a `full_clean()`
    - Implementar `clean()` para rechazar fechas futuras y bloquear escritura en meses cerrados consultando `ControlMes`
    - Agregar índices en `mes` y `fecha`; ordenamiento por `['fecha', 'hora_reporte']`
    - Incluir docstring en la clase y en cada método
    - Verificar que `TrasladoPaciente` NO tiene campo `estado_cierre`
    - _Requirements: 4.1, 4.2, 4.3, 5.4_

  - [x] 2.4 Escribir prueba de propiedad para derivación de `mes` (Property 1)
    - **Property 1: Month derivation is consistent with fecha**
    - **Validates: Requirements 4.2**
    - Usar Hypothesis: para cualquier `fecha` válida, `TrasladoPaciente.mes == fecha.month` tras guardar

  - [x] 2.5 Escribir prueba de propiedad para bloqueo de mes cerrado (Property 2)
    - **Property 2: Closed month blocks all write operations**
    - **Validates: Requirements 3.9, 5.4**
    - Usar Hypothesis: para cualquier registro cuyo `mes` tenga `ControlMes.estado = CERRADO`, crear/actualizar/eliminar lanza `ValidationError`

  - [x] 2.6 Escribir prueba de propiedad para persistencia de campos (Property 4)
    - **Property 4: Record persistence preserves all fields**
    - **Validates: Requirements 3.7, 4.1, 4.2**
    - Usar Hypothesis: guardar un registro válido y recuperarlo; todos los campos deben ser iguales al input original, incluyendo `mes` derivado

  - [x] 2.7 Escribir prueba de propiedad para validación de campos obligatorios (Property 5)
    - **Property 5: Required field validation always rejects incomplete records**
    - **Validates: Requirements 3.8**
    - Usar Hypothesis: cualquier combinación con al menos un campo obligatorio (`fecha`, `hora_reporte`, `nombre_paciente`, `documento`) vacío debe ser rechazada sin persistir

  - [x] 2.8 Escribir tests unitarios para los modelos
    - `TrasladoPaciente.save()` deriva correctamente `mes` desde `fecha`
    - `TrasladoPaciente.clean()` lanza `ValidationError` para fechas futuras
    - `TrasladoPaciente.clean()` lanza `ValidationError` cuando `ControlMes.estado = CERRADO`
    - `ControlMes` tiene estado `ABIERTO` por defecto
    - Verificar que `TrasladoPaciente` no tiene atributo `estado_cierre`
    - _Requirements: 4.1, 4.2, 4.3, 5.1, 5.4_

- [x] 3. Crear migraciones y registrar modelos en admin
  - Ejecutar `makemigrations` y `migrate`
  - Registrar `Perfil`, `ControlMes` y `TrasladoPaciente` en `admin.py` con clases `ModelAdmin` básicas
  - _Requirements: 4.1, 5.1_

- [x] 4. Implementar autenticación (login, logout, recuperación de contraseña)
  - [x] 4.1 Implementar vista de login usando `LoginView` de Django con plantilla `login.html`
    - Plantilla: logo del hospital, campos usuario/contraseña, enlace "Recuperar Contraseña", botón "Ingresar", botón "Cancelar" (limpia campos con Alpine.js)
    - Configurar `LOGIN_URL`, `LOGIN_REDIRECT_URL` y `LOGOUT_REDIRECT_URL` en settings.py
    - Agregar URLs `/login/` y `/logout/` en `config/urls.py`
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6_

  - [x] 4.2 Implementar vista de recuperación de contraseña (`GET /recuperar-contrasena/`, `POST /recuperar-contrasena/`)
    - Siempre retornar el mismo mensaje genérico de contacto al DIRECTOR, sin revelar si el usuario existe
    - Plantilla `password_recovery.html`
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 4.3 Escribir prueba de propiedad para recuperación de contraseña (Property 11)
    - **Property 11: Password recovery never reveals user existence**
    - **Validates: Requirements 10.4**
    - Usar Hypothesis: para cualquier string como nombre de usuario (existente o no), el endpoint retorna el mismo mensaje genérico con el mismo código HTTP

  - [x] 4.4 Escribir tests unitarios para autenticación
    - Solicitudes no autenticadas redirigen a `/login/`
    - Credenciales inválidas muestran mensaje de error y no inician sesión
    - Recuperación de contraseña retorna mensaje genérico para usuario existente y no existente
    - _Requirements: 1.1, 1.3, 1.4, 10.4_

- [x] 5. Punto de control — Verificar que todas las pruebas pasan hasta aquí
  - Asegurarse de que todos los tests pasan. Consultar al usuario si surgen dudas.

- [x] 6. Implementar vista principal y filtros
  - [x] 6.1 Implementar vista `VistaMain` (CBV con `LoginRequiredMixin`) para `GET /`
    - Renderizar `main.html` con sidebar, barra de título y contenedor de tabla
    - Pasar al contexto: usuario actual, fecha actual, estado del mes seleccionado (`ControlMes`), rol del usuario
    - _Requirements: 2.1, 2.2, 2.3_

  - [x] 6.2 Implementar lógica de filtros en la vista principal
    - Leer parámetros `?mes=`, `?dia_desde=`, `?dia_hasta=` de la query string
    - Validar: mes no mayor al mes actual; dia_desde ≤ dia_hasta y dentro del rango del mes
    - Pasar mensajes de error de validación al contexto para mostrar en la barra de título
    - _Requirements: 2.4, 2.5, 2.6, 2.7_

  - [x] 6.3 Implementar plantilla `main.html` con sidebar condicional por rol
    - Sidebar: nombre de usuario, fecha actual, botón "Salir", menú "Reportes" (Excel, PDF), menú "Gestión" (Contraseña)
    - Sidebar DIRECTOR: agregar "Usuarios" en Gestión y botón "Limpiar datos del sistema"
    - Barra de título: selector de mes (máx. mes actual), selectores día desde/hasta, botón "Cerrar mes" solo para DIRECTOR
    - Contenedor de tabla con atributo `hx-get` apuntando a `/traslados/tabla/`
    - _Requirements: 2.2, 2.3, 2.4, 5.2_

  - [x] 6.4 Escribir tests unitarios para la vista principal
    - Filtro por mes retorna solo registros del mes correcto
    - Mes futuro muestra mensaje de validación
    - Rango de días inválido muestra mensaje de validación
    - Sidebar muestra opciones DIRECTOR solo para usuarios con rol DIRECTOR
    - _Requirements: 2.5, 2.6, 2.7_

- [x] 7. Implementar CRUD de traslados con HTMX
  - [x] 7.1 Implementar vista HTMX `GET /traslados/tabla/` que retorna el partial `table.html`
    - Aplicar filtros `mes`, `dia_desde`, `dia_hasta` al queryset de `TrasladoPaciente`
    - Cada `<tr>` debe incluir atributo `data-mes-estado` con el valor de `ControlMes.estado` para ese mes
    - Botones de acción deshabilitados si `ControlMes.estado = CERRADO`
    - _Requirements: 3.1, 3.9_

  - [x] 7.2 Implementar vista HTMX `GET /traslados/nuevo/` que retorna el partial `modal_form.html` vacío
    - Retornar 403 si el mes está cerrado
    - _Requirements: 3.2, 5.4, 5.5_

  - [x] 7.3 Implementar vista HTMX `POST /traslados/nuevo/` para crear un registro
    - Validar formulario; si inválido, retornar `modal_form.html` con errores
    - Si válido, guardar y retornar `table.html` actualizado (HTMX swap)
    - Retornar 403 si el mes está cerrado
    - _Requirements: 3.7, 3.8, 5.4, 5.5_

  - [x] 7.4 Implementar vistas HTMX `GET /traslados/<id>/editar/` y `POST /traslados/<id>/editar/`
    - GET: retornar `modal_form.html` precargado con datos del registro; 404 si no existe; 403 si mes cerrado
    - POST: validar, guardar y retornar `table.html` actualizado; errores en modal; 403 si mes cerrado
    - _Requirements: 3.3, 3.7, 3.8, 5.4, 5.5_

  - [x] 7.5 Implementar vista HTMX `DELETE /traslados/<id>/eliminar/` para eliminar un registro
    - Mostrar diálogo de confirmación antes de eliminar (implementar como partial HTMX o con Alpine.js)
    - Retornar `table.html` actualizado tras eliminar; 404 si no existe; 403 si mes cerrado
    - _Requirements: 3.5, 3.6, 5.4, 5.5_

  - [x] 7.6 Implementar plantillas `table.html` y `modal_form.html`
    - `table.html`: tabla con todas las columnas definidas en Req. 3.1, atributo `data-mes-estado` en cada `<tr>`, botones de acción con `hx-get`/`hx-delete`
    - `modal_form.html`: formulario vertical etiqueta:campo, botones "Guardar" y "Cancelar", mensajes de error por campo
    - _Requirements: 3.1, 3.2, 3.3, 3.8_

  - [x] 7.7 Implementar el manejador de doble clic en `static/traslados/js/main.js`
    - Escuchar `dblclick` en elementos `<tr>` de la tabla
    - Si `data-mes-estado == "ABIERTO"`, disparar la misma solicitud HTMX que el botón "[e] Editar" de esa fila
    - Si `data-mes-estado == "CERRADO"`, ignorar el evento silenciosamente (sin mensaje, sin acción)
    - _Requirements: 3.4, 3.5_

  - [x] 7.8 Implementar manejo de errores HTMX en `main.js`
    - Escuchar el evento `htmx:responseError` y mostrar una notificación toast con el mensaje de error
    - _Requirements: 3.9, 5.5_

  - [x] 7.9 Escribir prueba de propiedad para el filtro de registros (Property 3)
    - **Property 3: Filter returns only matching records**
    - **Validates: Requirements 2.5**
    - Usar Hypothesis: para cualquier combinación de `mes` y rango de días, el queryset retorna solo registros donde `fecha.month == mes` y `dia_desde <= fecha.day <= dia_hasta`

  - [x] 7.10 Escribir prueba de propiedad para bloqueo de mes cerrado en vistas (Property 2 — capa de vista)
    - **Property 2: Closed month blocks all write operations (view layer)**
    - **Validates: Requirements 3.9, 5.4**
    - Verificar que las vistas de creación, edición y eliminación retornan HTTP 403 cuando `ControlMes.estado = CERRADO`

  - [ ]* 7.11 Escribir tests unitarios para las vistas CRUD
    - Crear registro válido persiste y retorna tabla actualizada
    - Crear registro con campos obligatorios vacíos retorna errores en modal
    - Editar registro en mes cerrado retorna 403
    - Eliminar registro en mes cerrado retorna 403
    - GET de registro inexistente retorna 404
    - _Requirements: 3.7, 3.8, 5.4, 5.5_

- [x] 8. Punto de control — Verificar que todas las pruebas pasan hasta aquí
  - Asegurarse de que todos los tests pasan. Consultar al usuario si surgen dudas.

- [x] 9. Implementar control de cierre de mes
  - Implementar vista `POST /mes/<mes>/cerrar/` (DIRECTOR only) que cambia `ControlMes.estado` a CERRADO
  - Crear decorador `director_required` que retorna HTTP 403 para usuarios no DIRECTOR
  - Aplicar `director_required` a la vista de cierre de mes
  - Actualizar `main.html` para mostrar el botón "Cerrar mes" solo a usuarios DIRECTOR
  - _Requirements: 5.2, 5.3, 5.4_

- [x] 10. Implementar generación de reportes Excel y PDF
  - [x] 10.1 Implementar `services/report_excel.py` con función `generarExcel (queryset, mes)`
    - Usar `openpyxl`; hoja única con encabezados en español correspondientes a todos los campos de `TrasladoPaciente`
    - Una fila por registro; si no hay registros, solo encabezados
    - Retornar bytes del archivo; nombre: `traslados_<mes>.xlsx`
    - Incluir docstring en la función
    - _Requirements: 6.1, 6.3, 6.5, 6.6_

  - [x] 10.2 Implementar `services/report_pdf.py` con función `generarPdf (queryset, mes)`
    - Usar `xhtml2pdf`; renderizar plantilla HTML a PDF en orientación horizontal (landscape)
    - Encabezados en español, una fila por registro; si no hay registros, solo encabezados
    - Retornar bytes del archivo; nombre: `traslados_<mes>.pdf`
    - Incluir docstring en la función
    - _Requirements: 6.2, 6.4, 6.5, 6.6_

  - [x] 10.3 Implementar vistas `GET /reportes/excel/` y `GET /reportes/pdf/`
    - Leer parámetros de filtro `?mes=`, `?dia_desde=`, `?dia_hasta=` (mismos que vista principal)
    - Llamar al servicio correspondiente y retornar `HttpResponse` con `Content-Disposition: attachment; filename="..."`
    - Manejar errores de generación con página de error amigable y log de excepción
    - _Requirements: 6.1, 6.2, 6.6_

  - [x] 10.4 Escribir prueba de propiedad para contenido del Excel (Property 9)
    - **Property 9: Excel report contains correct headers and exactly the filtered records**
    - **Validates: Requirements 6.1, 6.3**
    - Usar Hypothesis: para cualquier filtro activo, el Excel generado contiene exactamente una fila por registro del queryset filtrado y los encabezados en español correctos

  - [x] 10.5 Escribir prueba de propiedad para nombre de archivo de reportes (Property 10)
    - **Property 10: Report filename follows the required format**
    - **Validates: Requirements 6.6**
    - Usar Hypothesis: para cualquier valor de `mes` (1–12), el header `Content-Disposition` contiene `traslados_<mes>.xlsx` o `traslados_<mes>.pdf` según el tipo

  - [x] 10.6 Escribir tests unitarios para los servicios de reporte
    - `generarExcel()` retorna bytes de un `.xlsx` válido con encabezados en español correctos
    - `generarExcel()` sin registros retorna hoja con solo encabezados
    - `generarPdf()` retorna bytes no vacíos
    - Nombre de archivo sigue el formato `traslados_<mes>.xlsx` / `traslados_<mes>.pdf`
    - _Requirements: 6.3, 6.4, 6.5, 6.6_

- [x] 11. Implementar gestión de usuarios (DIRECTOR only)
  - [x] 11.1 Implementar vistas de listado y creación de usuarios (`GET /usuarios/`, `GET /usuarios/nuevo/`, `POST /usuarios/nuevo/`)
    - Aplicar `director_required` a todas las vistas
    - Listado: mostrar todos los usuarios con nombre de usuario y rol
    - Creación: campos username, contraseña inicial, rol; capturar `IntegrityError` para username duplicado
    - Plantilla `user_management.html`
    - _Requirements: 7.1, 7.2, 7.3, 7.4_

  - [x] 11.2 Implementar vistas de cambio de contraseña y eliminación de usuarios (`GET /usuarios/<id>/password/`, `POST /usuarios/<id>/password/`, `POST /usuarios/<id>/eliminar/`)
    - Cambio de contraseña: nueva contraseña + confirmación; sin verificar contraseña actual (DIRECTOR cambia la de otro usuario)
    - Eliminación: diálogo de confirmación antes de proceder
    - _Requirements: 7.5, 7.6, 7.7, 7.8_

  - [ ]* 11.3 Escribir prueba de propiedad para username duplicado (Property 8)
    - **Property 8: Duplicate username is always rejected**
    - **Validates: Requirements 7.4**
    - Usar Hypothesis: para cualquier username ya existente, intentar crear otro usuario con el mismo nombre no modifica el conteo total de usuarios

  - [ ]* 11.4 Escribir prueba de propiedad para listado completo de usuarios (Property 12)
    - **Property 12: User management page lists all users**
    - **Validates: Requirements 7.2**
    - Usar Hypothesis: para cualquier conjunto de usuarios registrados, la página de gestión muestra todos con username y rol correctos sin omitir ninguno

  - [ ]* 11.5 Escribir tests unitarios para gestión de usuarios
    - Vistas de gestión de usuarios retornan 403 para usuarios FUNCIONARIO
    - Crear usuario con username duplicado muestra error y no crea duplicado
    - Cambio de contraseña con confirmación no coincidente muestra error
    - Eliminación de usuario requiere confirmación
    - _Requirements: 7.1, 7.4, 7.7, 7.8_

- [x] 12. Implementar cambio de contraseña propia
  - Implementar vistas `GET /perfil/contrasena/` y `POST /perfil/contrasena/` con `LoginRequiredMixin`
  - Formulario: contraseña actual, nueva contraseña, confirmar nueva contraseña
  - Validar contraseña actual con `user.check_password()`; verificar que nueva y confirmación coincidan
  - Plantilla `password_change.html`
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [ ]* 12.1 Escribir prueba de propiedad para cambio de contraseña propia (Property 7)
    - **Property 7: Self password change correctness**
    - **Validates: Requirements 8.3, 8.4, 8.5**
    - Usar Hypothesis: el cambio de contraseña tiene éxito si y solo si la contraseña actual es correcta Y nueva == confirmación; cualquier otra combinación es rechazada sin modificar la contraseña almacenada

  - [ ]* 12.2 Escribir tests unitarios para cambio de contraseña propia
    - Contraseña actual incorrecta muestra error y no actualiza
    - Nueva contraseña y confirmación no coincidentes muestran error y no actualizan
    - Datos válidos actualizan la contraseña y muestran mensaje de éxito
    - _Requirements: 8.3, 8.4, 8.5_

- [x] 13. Implementar limpieza anual de datos (DIRECTOR only)
  - Implementar vista `POST /sistema/limpiar/` con `director_required`
  - Antes del diálogo de confirmación, mostrar sugerencia de generar reportes Excel y PDF con enlaces directos
  - Diálogo de confirmación con advertencia explícita de acción irreversible
  - En POST confirmado: `TrasladoPaciente.objects.all().delete()` + resetear todos los `ControlMes.estado` a ABIERTO
  - Redirigir a vista principal con mensaje de éxito tras la limpieza
  - Si el DIRECTOR cancela, no realizar ninguna modificación
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

  - [ ]* 13.1 Escribir prueba de propiedad para limpieza anual (Property 6)
    - **Property 6: Annual cleanup resets all state**
    - **Validates: Requirements 9.3**
    - Usar Hypothesis: para cualquier estado del sistema (N registros, combinación de meses abiertos/cerrados), tras ejecutar la limpieza el conteo de `TrasladoPaciente` es 0 y todos los `ControlMes` tienen `estado = ABIERTO`

  - [ ]* 13.2 Escribir tests unitarios para limpieza de datos
    - Vista retorna 403 para usuarios FUNCIONARIO
    - POST confirmado elimina todos los registros y resetea todos los meses a ABIERTO
    - Cancelar no modifica ningún dato
    - _Requirements: 9.1, 9.3, 9.4, 9.5_

- [x] 14. Punto de control final — Verificar que todas las pruebas pasan
  - Asegurarse de que todos los tests pasan. Consultar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia los requisitos específicos para trazabilidad
- Los puntos de control garantizan validación incremental
- Las pruebas de propiedad (Hypothesis) validan las propiedades de corrección universales definidas en el diseño
- Los tests unitarios validan ejemplos específicos y casos borde
- El campo `mes` de `TrasladoPaciente` es siempre derivado de `fecha`; no existe campo `estado_cierre` en ese modelo
- El estado de cierre de mes es gestionado exclusivamente por `ControlMes`
- La app Django se llama `traslados` (prefijo `app_` según convención del proyecto)
