---
inclusion: always
---

# Reglas de Código — Quiroinfo

## Alcance de las reglas de nomenclatura

Estas reglas aplican **únicamente al código de dominio** de la aplicación.
NO modificar ni traducir nombres estándar de Django, Python ni librerías externas.
Los nombres del framework (Django, Python, librerías) deben permanecer en inglés.

## Nomenclatura (código de dominio)

- Todos los identificadores de dominio deben estar en **español**.
- Esto incluye: modelos, variables, funciones, clases, URLs personalizadas y lógica de negocio.
- NO usar inglés para conceptos de dominio.

## Estilo de nomenclatura

- Clases y otros tipos: **PascalCase** con inicial mayúscula (ej. `SesionActiva`, `EstadoQuirurgico`).
- Funciones y variables: **camelCase** con inicial minúscula (ej. `siguienteEstado`, `codigoPaciente`).
- Este estilo sigue la convención Java: uppercase para tipos, lowercase para instancias y funciones.

## Apps Django

- Las apps Django deben comenzar con el prefijo `app_`.

## URLs y rutas

- Las rutas personalizadas de la aplicación deben estar en español.
- Las rutas estándar de Django pueden permanecer en inglés:
  - `/login/`
  - `/logout/`
  - `/admin/`

## Constantes y enumeraciones

- Los enums y constantes de dominio deben estar en español.
- Ejemplo:
  - `EN_PREPARACION`
  - `EN_CIRUGIA`
  - `EN_RECUPERACION`

## Estilo de sintaxis

- Dejar un espacio entre el nombre de función o variable y los paréntesis/corchetes.
  - Ejemplo: `FuncionEjemplo ()`, `variableEjemplo []`

## Indentación

- Usar **tabs** para indentar (1 tab = 4 espacios). No usar espacios para indentar.
- Aplica a funciones, clases, bloques de control, y cualquier bloque de código.

## Documentación de clases y funciones

- Toda clase debe incluir un docstring corto que describa su propósito.
- Toda función o método debe incluir un docstring corto que describa qué hace.
- El docstring debe ir inmediatamente después de la declaración, entre comillas triples `"""`.
- Ejemplo:
  ```python
  class SesionServicio:
      """Gestiona la creación y actualización de sesiones quirúrgicas."""

      def aplicarEstado (self, paciente, nuevoEstado):
          """Crea o actualiza la sesión del paciente con el nuevo estado."""
          ...
  ```

## Diseño de funciones

- Funciones cortas: máximo ~30 líneas.
- Una sola responsabilidad por función.

## Vistas

- Usar Class-Based Views (CBV) cuando aplique.
- Usar `LoginRequiredMixin` para proteger vistas privadas.

## Frontend

- Evitar JavaScript personalizado; preferir HTMX para interacciones dinámicas.
- Alpine.js solo para comportamientos ligeros de UI (modales, dropdowns).
- Templates simples y reutilizables; evitar lógica compleja en templates.
- Tailwind CSS por CDN en el MVP.
