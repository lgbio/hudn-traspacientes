# 🧾 Prompt para Kiro – Alineación FINAL de Requerimientos y Diseño

Actualiza **AMBOS documentos** (Requirements y Design) aplicando EXACTAMENTE los siguientes cambios. Mantén formatos actuales:
- Requirements: User Stories + Acceptance Criteria ("THE Sistema SHALL…")
- Design: secciones técnicas y código

NO agregar nuevas funcionalidades. Solo corregir inconsistencias y ambigüedades.

---

## 1) ❌ Eliminación TOTAL de uso de Año

Aplicar en Requirements y Design:

- NO usar `año` en modelo ni lógica
- NO mencionar persistencia histórica

Actualizar nombres de archivos:

- `traslados_<mes>.xlsx`
- `traslados_<mes>.pdf`

Actualizar también:
- propiedades
- tests
- documentación

---

## 2) ✔ Modelo de Cierre de Mes (consistencia)

- MANTENER `ControlMes` como única fuente de estado
- ELIMINAR cualquier referencia a `estado_cierre` en `TrasladoPaciente`

Regla global (en ambos docs):

IF `ControlMes.estado = CERRADO`
THEN THE Sistema SHALL impedir crear, editar y eliminar registros

---

## 3) ✔ Regla de Fecha (simplificación)

Reemplazar cualquier mención a “periodo operativo” por:

- THE Sistema SHALL rechazar fechas futuras
- NO agregar más restricciones

---

## 4) ✔ Doble Click (unificar comportamiento)

Unificar Requirements y Design a:

- WHEN el usuario hace doble click sobre una fila
  AND el mes está ABIERTO
  THEN THE Sistema SHALL abrir el modal de edición

- IF el mes está CERRADO
  THEN THE Sistema SHALL ignorar el evento (sin mensaje)

---

## 5) ✔ Limpieza de Datos (seguridad UX)

Extender en ambos documentos:

- BEFORE ejecutar la limpieza
  THE Sistema SHOULD sugerir generar reportes (Excel/PDF)

Mantener:
- confirmación obligatoria
- eliminación total de registros
- reset de `ControlMes` a ABIERTO

---

## 6) ✔ Actualización sin Recarga (explicitar tecnología)

Alinear ambos documentos:

- THE Sistema SHALL actualizar la tabla sin recargar la página completa
- Implementación SHALL usar **HTMX** (preferido) o AJAX

---

## 7) ⚠️ Simplificación de Testing (Design)

Modificar sección de pruebas:

- MANTENER:
  - Unit tests
  - Integration tests

- REMOVER o marcar como FUTURO:
  - Property-based testing (Hypothesis)

---

## 8) ✔ Consistencia General

Asegurar en ambos documentos:

- No existe `año`
- No existe `estado_cierre` en `TrasladoPaciente`
- Todas las reglas de cierre usan `ControlMes`
- Naming y comportamiento coinciden entre Requirements y Design

---

## Resultado Esperado

- Requirements y Design completamente alineados
- Sin contradicciones
- Modelo limpio y consistente
- Listo para implementación directa

---

No extender alcance. No agregar features. Solo aplicar estas correcciones.
