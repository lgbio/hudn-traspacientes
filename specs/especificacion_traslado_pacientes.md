# 📄 Especificación Funcional – App Registro de Traslado de Pacientes (MVP)

---

# 🎯 Objetivo General

Desarrollar una aplicación web basada en Django que permita registrar, gestionar y generar reportes de los servicios de traslado de pacientes de manera eficiente, segura y estructurada, reemplazando el uso de hojas de cálculo y optimizando el proceso de digitación para que los usuarios registren la información de forma rápida, simple y con el mínimo esfuerzo.

---

# 1. 🧩 Modelo de Datos

## Entidad: TrasladoPaciente

Campos:

- fecha
- hora_reporte
- hora_egreso
- hora_ingreso
- nombre_paciente
- documento
- servicio
- quien_reporta
- destino
- procedimiento
- medico
- conductor
- radio_operador
- ambulancia
- observacion
- mes (1–12)
- estado_cierre (boolean)

## Reglas

- NO existe persistencia histórica
- NO se usa año
- Los datos corresponden únicamente al periodo operativo actual

---

# 2. 🧹 Gestión de Datos

## Limpieza Anual

- El sistema NO conserva datos históricos
- Al iniciar un nuevo año:
  - El DIRECTOR debe eliminar todos los registros

## Acción del sistema

- Debe existir una opción:
  - "Limpiar datos del sistema"

## Flujo

1. Usuario DIRECTOR ejecuta acción
2. Sistema solicita confirmación
3. Sistema elimina todos los registros

---

# 3. 👤 Roles y Permisos

## FUNCIONARIO

- Crear registros
- Editar registros (solo si el mes está abierto)
- Eliminar registros (solo si el mes está abierto)
- Generar reportes (Excel / PDF)
- Cambiar contraseña

## DIRECTOR

- Todas las funciones del FUNCIONARIO
- Gestionar usuarios
- Cerrar mes
- Limpiar datos del sistema

---

# 4. 🔒 Control de Mes

## Regla

- Un mes puede estar ABIERTO o CERRADO

## Comportamiento

IF mes está cerrado
THEN no se permite:
- crear
- editar
- eliminar registros

---

# 5. 🖥️ Interfaz de Usuario

## 5.1 Login

- Usuario
- Contraseña
- Botón ingresar

---

## 5.2 Vista Principal

### Header

- Selector de mes (por defecto mes actual)
- Rango de fechas (desde / hasta)

### Sidebar

Secciones:

**Usuario**
- Nombre
- Fecha actual
- Logout

**Reportes**
- Exportar Excel
- Exportar PDF

**Gestión**
- Cambiar contraseña
- Usuarios (solo DIRECTOR)

---

## 5.3 Tabla de Registros

- Visual tipo Excel (solo apariencia)
- No edición directa en celdas

### Columnas

- Acciones
- Fecha
- Hora reporte
- Hora egreso
- Hora ingreso
- Nombre paciente
- Documento
- ... (resto de campos)

---

## 5.4 Acciones por Registro

- Editar → abre modal
- Eliminar → confirmación
- Adicionar → crea nuevo registro

---

## 5.5 Formulario (Modal)

- Layout vertical
- Campos del modelo

### Validaciones

- fecha: obligatoria
- nombre_paciente: obligatorio
- documento: solo numérico
- horas: formato HH:MM

---

# 6. 📊 Reportes

## Tipos

- Excel
- PDF

## Alcance

- Por mes
- Por rango de fechas

---

# 7. ⚙️ Requisitos Técnicos

## Backend

- Django
- SQLite (MVP)

## Frontend

- Django Templates (SSR)
- HTMX (opcional)

---

# 8. 🚀 Alcance MVP

Incluye:

- CRUD de registros
- Filtro por mes
- Edición mediante modal
- Exportación Excel
- Control de cierre de mes
- Gestión básica de usuarios

No incluye:

- Históricos
- Edición tipo Excel (inline)
- Frontend complejo (SPA)

---

# 9. 🧭 Nota de Diseño

El sistema NO es una hoja de cálculo.

Es una aplicación controlada con:

- validaciones
- reglas de negocio
- flujo estructurado

Esto permite:

- menor error humano
- mejor mantenimiento
- desarrollo más rápido
