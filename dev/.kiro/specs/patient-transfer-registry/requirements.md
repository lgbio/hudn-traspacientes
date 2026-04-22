# Requirements Document

## Introduction

Sistema web Django para el registro y gestión de servicios de traslado de pacientes. Reemplaza el proceso actual basado en hojas de cálculo Excel, permitiendo a los usuarios (FUNCIONARIO y DIRECTOR) registrar, consultar, editar y eliminar registros de traslados, generar reportes en Excel y PDF, y controlar el cierre mensual de registros. El sistema no conserva datos históricos; los registros son limpiados por el DIRECTOR cuando se requiere reiniciar el sistema.

---

## Glossary

- **Sistema**: La aplicación web Django de registro de traslados de pacientes.
- **FUNCIONARIO**: Usuario estándar con permisos para crear, editar y eliminar registros (en meses abiertos), generar reportes y cambiar su contraseña.
- **DIRECTOR**: Usuario administrador con todos los permisos del FUNCIONARIO más gestión de usuarios, cierre de mes y limpieza de datos del sistema.
- **TrasladoPaciente**: Entidad principal que representa un registro de servicio de traslado de paciente.
- **Mes**: Período mensual (1–12) al que pertenece un registro de traslado.
- **EstadoCierre**: Estado booleano de un mes que indica si está ABIERTO (editable) o CERRADO (solo lectura).
- **Reporte**: Archivo generado (Excel o PDF) con los registros de traslado filtrados por mes o rango de fechas.
- **ControlMes**: Entidad que almacena el estado de cierre de cada mes.
- **Sesión**: Período de autenticación activa de un usuario en el Sistema.

---

## Requirements

### Requirement 1: Autenticación de Usuarios

**User Story:** Como usuario del sistema, quiero iniciar sesión con mis credenciales, para que pueda acceder de forma segura a las funciones según mi rol.

#### Acceptance Criteria

1. WHEN un usuario accede a la URL del Sistema sin sesión activa, THE Sistema SHALL redirigir al usuario a la pantalla de inicio de sesión.
2. THE pantalla de inicio de sesión SHALL mostrar el logo del hospital, un campo "Usuario", un campo "Contraseña", un enlace "Recuperar Contraseña", un botón "Ingresar" y un botón "Cancelar".
3. WHEN el usuario envía credenciales válidas, THE Sistema SHALL iniciar una sesión autenticada y redirigir al usuario a la vista principal.
4. IF el usuario envía credenciales inválidas, THEN THE Sistema SHALL mostrar un mensaje de error indicando que las credenciales son incorrectas y no iniciar sesión.
5. WHEN el usuario hace clic en "Cancelar", THE Sistema SHALL limpiar los campos del formulario de inicio de sesión.
6. WHEN el usuario hace clic en "Salir" en la vista principal, THE Sistema SHALL cerrar la sesión activa y redirigir al usuario a la pantalla de inicio de sesión.

---

### Requirement 2: Vista Principal y Navegación

**User Story:** Como usuario autenticado, quiero una vista principal organizada con panel lateral y tabla central, para que pueda navegar y operar el sistema de forma eficiente.

#### Acceptance Criteria

1. WHILE el usuario tiene una sesión activa, THE Sistema SHALL mostrar la vista principal con: un panel lateral izquierdo, una barra de título superior derecha con controles de filtro, y un panel central con la tabla de registros.
2. THE panel lateral izquierdo SHALL mostrar: el nombre del usuario actual, la fecha actual, el botón "Salir", el menú "Reportes" con opciones "Excel" y "PDF", y el menú "Gestión" con la opción "Contraseña".
3. WHERE el usuario autenticado tiene el rol DIRECTOR, THE panel lateral izquierdo SHALL mostrar adicionalmente la opción "Usuarios" dentro del menú "Gestión" y la opción "Limpiar datos del sistema".
4. THE barra de título SHALL mostrar un selector de mes ("Mes") con valor predeterminado al mes actual, y un selector de rango de días ("Día Desde" y "Día Hasta").
5. WHEN el usuario selecciona un mes o rango de días, THE Sistema SHALL actualizar la tabla central mostrando únicamente los registros que correspondan al filtro aplicado.
6. IF el usuario selecciona un mes posterior al mes actual, THEN THE Sistema SHALL mostrar un mensaje de validación indicando que solo se permiten meses anteriores o el mes actual.
7. IF el usuario ingresa un rango de días inválido (Desde > Hasta, o días fuera del rango del mes), THEN THE Sistema SHALL mostrar un mensaje de validación indicando el error.

---

### Requirement 3: Registro de Traslados de Pacientes (CRUD)

**User Story:** Como FUNCIONARIO, quiero crear, editar y eliminar registros de traslados, para que la información de cada servicio quede correctamente registrada en el sistema.

#### Acceptance Criteria

1. THE tabla central SHALL mostrar una columna "Acciones" como primera columna, seguida de las columnas: FECHA, HORA REPORTE, HORA DE EGRESO, HORA DE INGRESO, NOMBRE DE PACIENTE, DOCUMENTO, SERVICIO, QUIEN REPORTA, DESTINO, PROCEDIMIENTO, MÉDICO, CONDUCTOR, RADIO OPERADOR, AMBULANCIA DE TRASLADO, OBSERVACIÓN.
2. WHEN el usuario hace clic en el botón "[+] Adicionar" de una fila, THE Sistema SHALL abrir un diálogo modal con un formulario en disposición vertical (etiqueta:campo) para ingresar un nuevo registro, con botones "Guardar" y "Cancelar".
3. WHEN el usuario hace clic en el botón "[e] Editar" de una fila, THE Sistema SHALL abrir un diálogo modal con el formulario precargado con los datos del registro seleccionado, con botones "Guardar" y "Cancelar".
4. WHEN el usuario hace doble clic sobre una fila de la tabla AND el mes correspondiente tiene `ControlMes.estado = ABIERTO`, THE Sistema SHALL abrir el diálogo modal de edición con el formulario precargado con los datos del registro correspondiente.
5. IF el mes correspondiente tiene `ControlMes.estado = CERRADO`, THEN THE Sistema SHALL ignorar el evento de doble clic sin mostrar ningún mensaje.
5. WHEN el usuario hace clic en "[x] Eliminar" de una fila, THE Sistema SHALL mostrar un diálogo de confirmación con advertencia antes de proceder con la eliminación.
6. WHEN el usuario confirma la eliminación, THE Sistema SHALL eliminar el registro y actualizar la tabla.
7. WHEN el usuario guarda un registro nuevo o editado con datos válidos, THE Sistema SHALL persistir el registro en la base de datos y actualizar la tabla sin recargar la página completa usando HTMX.
8. IF el usuario intenta guardar un registro con campos obligatorios vacíos (fecha, hora_reporte, nombre_paciente, documento), THEN THE Sistema SHALL mostrar mensajes de validación por campo y no persistir el registro.
9. WHILE `ControlMes.estado = CERRADO` para el mes del registro, THE Sistema SHALL deshabilitar los botones "[+] Adicionar", "[e] Editar" y "[x] Eliminar" para los registros de ese mes.

---

### Requirement 4: Modelo de Datos TrasladoPaciente

**User Story:** Como sistema, quiero almacenar todos los campos de un traslado de paciente, para que la información sea completa y consistente con el proceso operativo actual.

#### Acceptance Criteria

1. THE Sistema SHALL almacenar cada TrasladoPaciente con los campos: fecha (date), hora_reporte (time), hora_egreso (time, opcional), hora_ingreso (time, opcional), nombre_paciente (text), documento (text), servicio (text), quien_reporta (text), destino (text), procedimiento (text), medico (text), conductor (text), radio_operador (text), ambulancia (text), observacion (text, opcional), mes (integer 1–12).
2. THE Sistema SHALL derivar automáticamente el campo mes a partir del campo fecha al momento de guardar el registro.
3. IF el valor del campo fecha es una fecha futura, THEN THE Sistema SHALL rechazar el registro y mostrar un mensaje de validación.

---

### Requirement 5: Control de Cierre de Mes

**User Story:** Como DIRECTOR, quiero cerrar el registro de un mes, para que los registros de ese período queden protegidos contra modificaciones.

#### Acceptance Criteria

1. THE Sistema SHALL mantener un registro de ControlMes con el estado (ABIERTO/CERRADO) para cada mes (1–12).
2. WHERE el usuario autenticado tiene el rol DIRECTOR, THE Sistema SHALL mostrar una opción para cerrar el mes seleccionado actualmente.
3. WHEN el DIRECTOR confirma el cierre de un mes, THE Sistema SHALL cambiar `ControlMes.estado` a CERRADO para ese mes.
4. IF `ControlMes.estado = CERRADO` para un mes, THEN THE Sistema SHALL impedir la creación, edición y eliminación de registros TrasladoPaciente pertenecientes a ese mes.
5. IF un usuario intenta crear, editar o eliminar un registro en un mes con `ControlMes.estado = CERRADO`, THEN THE Sistema SHALL mostrar un mensaje indicando que el mes está cerrado y la operación no está permitida.

---

### Requirement 6: Generación de Reportes

**User Story:** Como usuario autenticado, quiero generar reportes en Excel y PDF de los registros de traslados, para que pueda compartir y archivar la información mensual.

#### Acceptance Criteria

1. WHEN el usuario hace clic en "Reportes > Excel", THE Sistema SHALL generar y descargar un archivo Excel (.xlsx) con todos los registros del mes y rango de días actualmente seleccionados en el filtro.
2. WHEN el usuario hace clic en "Reportes > PDF", THE Sistema SHALL generar y descargar un archivo PDF con todos los registros del mes y rango de días actualmente seleccionados en el filtro.
3. THE archivo Excel generado SHALL contener una hoja con encabezados de columna en español correspondientes a todos los campos de TrasladoPaciente, y una fila por cada registro incluido en el filtro.
4. THE archivo PDF generado SHALL contener una tabla con encabezados de columna en español y una fila por cada registro incluido en el filtro, con formato legible para impresión.
5. IF el filtro activo no retorna registros, THEN THE Sistema SHALL generar el archivo con encabezados pero sin filas de datos, e informar al usuario que no hay registros para el período seleccionado.
6. THE Sistema SHALL nombrar los archivos generados con el formato: `traslados_<mes>.xlsx` y `traslados_<mes>.pdf` respectivamente.

---

### Requirement 7: Gestión de Usuarios

**User Story:** Como DIRECTOR, quiero crear, eliminar y cambiar la contraseña de usuarios, para que pueda administrar el acceso al sistema.

#### Acceptance Criteria

1. WHERE el usuario autenticado tiene el rol DIRECTOR, THE Sistema SHALL mostrar una pantalla de gestión de usuarios accesible desde "Gestión > Usuarios".
2. THE pantalla de gestión de usuarios SHALL listar todos los usuarios del sistema con su nombre de usuario y rol.
3. WHEN el DIRECTOR crea un nuevo usuario, THE Sistema SHALL requerir: nombre de usuario, contraseña inicial y rol (FUNCIONARIO o DIRECTOR).
4. IF el DIRECTOR intenta crear un usuario con un nombre de usuario ya existente, THEN THE Sistema SHALL mostrar un mensaje de error y no crear el usuario duplicado.
5. WHEN el DIRECTOR elimina un usuario, THE Sistema SHALL mostrar un diálogo de confirmación antes de proceder.
6. WHEN el DIRECTOR confirma la eliminación de un usuario, THE Sistema SHALL eliminar el usuario del sistema.
7. WHEN el DIRECTOR cambia la contraseña de un usuario, THE Sistema SHALL requerir la nueva contraseña y su confirmación, y actualizar la contraseña si ambos valores coinciden.
8. IF la nueva contraseña y su confirmación no coinciden, THEN THE Sistema SHALL mostrar un mensaje de error y no actualizar la contraseña.

---

### Requirement 8: Cambio de Contraseña Propia

**User Story:** Como usuario autenticado, quiero cambiar mi propia contraseña, para que pueda mantener la seguridad de mi cuenta.

#### Acceptance Criteria

1. THE Sistema SHALL mostrar la opción "Gestión > Contraseña" a todos los usuarios autenticados independientemente de su rol.
2. WHEN el usuario accede a "Gestión > Contraseña", THE Sistema SHALL mostrar un formulario con campos: "Contraseña actual", "Nueva contraseña" y "Confirmar nueva contraseña".
3. IF el usuario ingresa una contraseña actual incorrecta, THEN THE Sistema SHALL mostrar un mensaje de error y no actualizar la contraseña.
4. IF la nueva contraseña y la confirmación no coinciden, THEN THE Sistema SHALL mostrar un mensaje de error y no actualizar la contraseña.
5. WHEN el usuario envía el formulario con datos válidos, THE Sistema SHALL actualizar la contraseña y mostrar un mensaje de confirmación de éxito.

---

### Requirement 9: Limpieza Anual de Datos

**User Story:** Como DIRECTOR, quiero limpiar todos los registros del sistema cuando sea necesario reiniciarlo, para que el sistema comience un nuevo período operativo sin datos anteriores.

#### Acceptance Criteria

1. WHERE el usuario autenticado tiene el rol DIRECTOR, THE Sistema SHALL mostrar la opción "Limpiar datos del sistema" en el panel lateral.
2. WHEN el DIRECTOR hace clic en "Limpiar datos del sistema", THE Sistema SHOULD sugerir al usuario generar los reportes Excel y PDF antes de proceder, indicando que los datos serán eliminados permanentemente.
3. WHEN el DIRECTOR decide continuar, THE Sistema SHALL mostrar un diálogo de confirmación con advertencia explícita indicando que esta acción eliminará todos los registros de traslados y restablecerá el estado de todos los meses a ABIERTO, y que la acción es irreversible.
4. WHEN el DIRECTOR confirma la limpieza, THE Sistema SHALL eliminar todos los registros TrasladoPaciente y restablecer `ControlMes.estado` a ABIERTO para todos los meses.
5. IF el DIRECTOR cancela el diálogo de confirmación, THEN THE Sistema SHALL no realizar ninguna modificación a los datos.

---

### Requirement 10: Recuperación de Contraseña

**User Story:** Como usuario, quiero recuperar el acceso a mi cuenta si olvido mi contraseña, para que pueda seguir usando el sistema sin intervención inmediata del DIRECTOR.

#### Acceptance Criteria

1. THE pantalla de inicio de sesión SHALL mostrar un enlace "Recuperar Contraseña".
2. WHEN el usuario hace clic en "Recuperar Contraseña", THE Sistema SHALL mostrar un formulario para ingresar el nombre de usuario registrado.
3. WHEN el usuario envía el formulario de recuperación con un nombre de usuario válido, THE Sistema SHALL notificar al usuario que debe contactar al DIRECTOR para restablecer su contraseña.
4. IF el nombre de usuario ingresado no existe en el sistema, THEN THE Sistema SHALL mostrar el mismo mensaje genérico de contacto al DIRECTOR, sin revelar si el usuario existe o no.
