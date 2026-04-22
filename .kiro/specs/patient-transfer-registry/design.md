# Design Document

## Patient Transfer Registry (Sistema de Registro de Traslados de Pacientes)

---

## Overview

The Patient Transfer Registry is a Django web application that replaces an Excel-based workflow for recording and managing patient transport services. It provides role-based access for two user types (FUNCIONARIO and DIRECTOR), a spreadsheet-like central table for browsing and editing records, monthly close control, Excel/PDF report generation, and a data cleanup mechanism.

The system is designed for local deployment (single hospital), uses SQLite as the database for the MVP, and renders all UI server-side via Django Templates with HTMX for partial page updates (table refresh, modal dialogs) to avoid full-page reloads without introducing a heavy JS framework. The system does not store historical data across periods; all records belong to the current operational period.

### Key Design Decisions

- **Server-Side Rendering with HTMX**: Django Templates handle all rendering. HTMX handles partial updates (table refresh after save/delete, modal open/close) via `hx-get`/`hx-post` attributes. This keeps the stack simple while delivering a responsive UX.
- **SQLite for MVP**: Sufficient for a single-hospital deployment with low concurrent users. The ORM abstraction makes migration to PostgreSQL straightforward if needed later.
- **Django's built-in auth**: `django.contrib.auth` provides `User`, session management, and password hashing. A `Profile` model extends it with the role field.
- **Month-close enforcement at the model layer**: Validation in the model's `clean()` method and in views ensures closed months cannot be written to, regardless of UI state.
- **Report generation**: `openpyxl` for Excel and `ReportLab` (or `xhtml2pdf`) for PDF — both are pure-Python, well-maintained libraries with no external binary dependencies.

---

## Architecture

The application follows the standard Django MVT (Model-View-Template) pattern with a single Django app (`traslados`).

```
patient_transfer_registry/       ← Django project root
├── manage.py
├── config/                      ← Project settings package
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── traslados/                   ← Main application
│   ├── models.py                ← TrasladoPaciente, ControlMes, Profile
│   ├── views.py                 ← All views (auth, CRUD, reports, admin)
│   ├── forms.py                 ← ModelForms and utility forms
│   ├── urls.py                  ← App URL patterns
│   ├── admin.py
│   ├── services/
│   │   ├── report_excel.py      ← Excel generation logic
│   │   └── report_pdf.py        ← PDF generation logic
│   ├── templates/
│   │   └── traslados/
│   │       ├── base.html
│   │       ├── login.html
│   │       ├── main.html        ← Main view with sidebar + table
│   │       ├── partials/
│   │       │   ├── table.html   ← HTMX partial: table body
│   │       │   └── modal_form.html ← HTMX partial: create/edit modal
│   │       ├── password_change.html
│   │       ├── password_recovery.html
│   │       └── user_management.html
│   └── static/
│       └── traslados/
│           ├── css/style.css
│           └── js/main.js       ← Minimal JS: double-click handler
└── db.sqlite3
```

### Request Flow

```
Browser
  │
  ├─ Full page request ──► Django View ──► Template render ──► HTML response
  │
  └─ HTMX partial request ──► Django View ──► Partial template ──► HTML fragment
                                                                    (swapped into DOM)
```

### Authentication Flow

```
Unauthenticated request
  │
  ▼
LoginView (GET /login/)
  │  POST credentials
  ▼
authenticate() → success → redirect to /
                → failure → re-render login with error
```

---

## Components and Interfaces

### 1. Authentication Component

**Views:**
- `GET /login/` — render login form
- `POST /login/` — authenticate and redirect
- `POST /logout/` — end session, redirect to login
- `GET /password-recovery/` — render recovery info form
- `POST /password-recovery/` — show contact-director message

**Template:** `login.html`, `password_recovery.html`

**Behavior:**
- All views except `/login/` and `/password-recovery/` require `@login_required` (redirects to `/login/`).
- Login form fields: username, password. Displays hospital logo.
- Cancel button clears form fields (client-side JS).
- Recovery form accepts a username and always returns the same generic message (no user enumeration).

---

### 2. Main View Component

**Views:**
- `GET /` — render main view with current month's records

**URL parameters:** `?mes=<1-12>&dia_desde=<1-31>&dia_hasta=<1-31>`

**Template:** `main.html` (includes sidebar, title bar, table partial)

**Sidebar contents (all users):**
- Current username and date
- "Salir" button
- Reportes menu: Excel, PDF
- Gestión menu: Contraseña

**Sidebar contents (DIRECTOR only):**
- Gestión menu: Usuarios
- "Limpiar datos del sistema" button

**Title bar:**
- Month selector (default: current month, max: current month)
- Day-from / Day-to selectors

**Filter validation:**
- Month > current month → validation error message
- Day-from > Day-to or out of month range → validation error message

---

### 3. Transfer Records CRUD Component

**Views:**
- `GET /traslados/tabla/` — HTMX partial: filtered table body
- `GET /traslados/nuevo/` — HTMX partial: empty create modal
- `POST /traslados/nuevo/` — create record, return updated table partial
- `GET /traslados/<id>/editar/` — HTMX partial: pre-filled edit modal
- `POST /traslados/<id>/editar/` — update record, return updated table partial
- `DELETE /traslados/<id>/eliminar/` — delete record, return updated table partial

**Table columns (in order):**
Acciones | FECHA | HORA REPORTE | HORA DE EGRESO | HORA DE INGRESO | NOMBRE DE PACIENTE | DOCUMENTO | SERVICIO | QUIEN REPORTA | DESTINO | PROCEDIMIENTO | MÉDICO | CONDUCTOR | RADIO OPERADOR | AMBULANCIA DE TRASLADO | OBSERVACIÓN

**Action buttons per row:**
- `[+] Adicionar` — opens create modal (disabled if month closed)
- `[e] Editar` — opens edit modal (disabled if month closed)
- `[x] Eliminar` — shows confirmation dialog (disabled if month closed)

**Double-click behavior:**
- A minimal JS snippet (or Alpine.js) listens for `dblclick` on `<tr>` elements.
- Each row carries a `data-mes-estado` attribute set server-side to `ABIERTO` or `CERRADO`.
- If `data-mes-estado == "ABIERTO"`, the double-click triggers the same HTMX request as the `[e] Editar` button for that row.
- If `data-mes-estado == "CERRADO"`, the event is ignored silently — no message, no action.

**Modal dialog:**
- Rendered as an HTMX partial swapped into a `<dialog>` element or a dedicated modal container.
- Form layout: vertical label:field pairs.
- Buttons: "Guardar" (submit), "Cancelar" (closes modal).

**Validation:**
- Required fields: `fecha`, `hora_reporte`, `nombre_paciente`, `documento`.
- Server-side validation via Django form; errors returned in the modal partial.
- Date validation: reject future dates (`fecha > today`). No other date restrictions.
- Month-close check: enforced via `ControlMes` — if `ControlMes.estado = CERRADO` for the record's month, return HTTP 403 with an error message. `TrasladoPaciente` has no `estado_cierre` field.

---

### 4. Month Close Control Component

**Views:**
- `POST /mes/<mes>/cerrar/` — DIRECTOR only: close a month

**Behavior:**
- The main view shows a "Cerrar mes" button in the title bar only when the authenticated user is DIRECTOR.
- Closing a month sets `ControlMes.estado = CERRADO` for that month. `ControlMes` is the single source of truth for month state.
- Once closed, all CRUD operations for records in that month are blocked at the view layer (HTTP 403) and at the model layer (`clean()` raises `ValidationError`). The `TrasladoPaciente` model has no `estado_cierre` field.
- There is no "reopen" operation in the MVP (by design — the DIRECTOR can use the annual cleanup to reset all months).

---

### 5. Report Generation Component

**Views:**
- `GET /reportes/excel/` — generate and stream Excel file
- `GET /reportes/pdf/` — generate and stream PDF file

**URL parameters:** `?mes=<1-12>&dia_desde=<1-31>&dia_hasta=<1-31>` (mirrors main view filter)

**Excel generation (`report_excel.py`):**
- Uses `openpyxl`.
- Single worksheet with Spanish column headers.
- One row per `TrasladoPaciente` record matching the filter.
- File name: `traslados_<mes>.xlsx`.
- If no records: headers only, no data rows.

**PDF generation (`report_pdf.py`):**
- Uses `xhtml2pdf` (renders an HTML template to PDF) or `ReportLab` (programmatic table).
- Preferred: `xhtml2pdf` — allows reusing a Django template for the PDF layout, keeping styling consistent.
- File name: `traslados_<mes>.pdf`.
- Landscape orientation for readability given the number of columns.

**Response type:** `HttpResponse` with `Content-Disposition: attachment; filename="..."`.

---

### 6. User Management Component (DIRECTOR only)

**Views:**
- `GET /usuarios/` — list all users
- `GET /usuarios/nuevo/` — create user form
- `POST /usuarios/nuevo/` — create user
- `GET /usuarios/<id>/password/` — change password form
- `POST /usuarios/<id>/password/` — change password
- `POST /usuarios/<id>/eliminar/` — delete user (with confirmation)

**Access control:** All views decorated with a custom `@director_required` decorator that returns HTTP 403 for non-DIRECTOR users.

**User creation fields:** username, initial password, role (FUNCIONARIO / DIRECTOR).

**Duplicate username:** Django's `User` model enforces uniqueness; the form catches `IntegrityError` and shows an error message.

**Password change:** Requires new password + confirmation. No current-password check (DIRECTOR is changing another user's password).

---

### 7. Self Password Change Component

**Views:**
- `GET /perfil/password/` — self password change form
- `POST /perfil/password/` — validate and update

**Access control:** `@login_required` only (all roles).

**Form fields:** current password, new password, confirm new password.

**Validation:** Current password verified with `user.check_password()`. New password and confirmation must match.

---

### 8. Data Cleanup Component (DIRECTOR only)

**Views:**
- `POST /sistema/limpiar/` — delete all records and reset month states

**Access control:** `@director_required`.

**Behavior:**
- Before showing the confirmation dialog, THE Sistema SHOULD display a suggestion to generate Excel and PDF reports first, with direct links to both report actions.
- A confirmation dialog with an explicit irreversible-action warning is shown before the POST is submitted.
- On POST: `TrasladoPaciente.objects.all().delete()` + reset all `ControlMes.estado` to `ABIERTO`.
- Returns redirect to main view with a success message.

---

## Data Models

### `Profile` (extends `django.contrib.auth.models.User`)

```python
class Profile(models.Model):
    ROLE_CHOICES = [
        ('FUNCIONARIO', 'Funcionario'),
        ('DIRECTOR', 'Director'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='FUNCIONARIO')

    def __str__(self):
        return f"{self.user.username} ({self.role})"
```

Signals (`post_save` on `User`) auto-create/update the `Profile` when a `User` is saved.

---

### `ControlMes`

```python
class ControlMes(models.Model):
    ESTADO_CHOICES = [
        ('ABIERTO', 'Abierto'),
        ('CERRADO', 'Cerrado'),
    ]
    mes = models.IntegerField(unique=True)  # 1–12
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ABIERTO')
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    cerrado_por = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name='meses_cerrados'
    )

    class Meta:
        ordering = ['mes']

    def __str__(self):
        return f"Mes {self.mes}: {self.estado}"
```

A management command (or `AppConfig.ready()` signal) ensures all 12 `ControlMes` rows exist on startup.

---

### `TrasladoPaciente`

```python
class TrasladoPaciente(models.Model):
    fecha           = models.DateField()
    hora_reporte    = models.TimeField()
    hora_egreso     = models.TimeField(null=True, blank=True)
    hora_ingreso    = models.TimeField(null=True, blank=True)
    nombre_paciente = models.CharField(max_length=255)
    documento       = models.CharField(max_length=50)
    servicio        = models.CharField(max_length=100)
    quien_reporta   = models.CharField(max_length=100)
    destino         = models.CharField(max_length=100)
    procedimiento   = models.CharField(max_length=255)
    medico          = models.CharField(max_length=100)
    conductor       = models.CharField(max_length=100)
    radio_operador  = models.CharField(max_length=100)
    ambulancia      = models.CharField(max_length=100)
    observacion     = models.TextField(blank=True, default='')
    mes             = models.IntegerField(editable=False)  # derived from fecha

    class Meta:
        ordering = ['fecha', 'hora_reporte']
        indexes = [
            models.Index(fields=['mes']),
            models.Index(fields=['fecha']),
        ]

    def save(self, *args, **kwargs):
        self.mes = self.fecha.month
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self):
        from django.core.exceptions import ValidationError
        import datetime
        if self.fecha:
            self.mes = self.fecha.month
            today = datetime.date.today()
            if self.fecha > today:
                raise ValidationError({'fecha': 'La fecha no puede ser futura.'})
            # Check month is not closed via ControlMes (single source of truth)
            try:
                control = ControlMes.objects.get(mes=self.mes)
                if control.estado == 'CERRADO':
                    raise ValidationError(
                        'El mes está cerrado. No se pueden crear ni modificar registros.'
                    )
            except ControlMes.DoesNotExist:
                pass

    def __str__(self):
        return f"{self.fecha} – {self.nombre_paciente}"
```

---

### Database Schema Summary

| Table | Key Fields |
|---|---|
| `auth_user` | id, username, password (hashed), is_active |
| `traslados_profile` | id, user_id (FK), role |
| `traslados_controlmes` | id, mes (unique), estado, fecha_cierre, cerrado_por_id |
| `traslados_trasladopaciente` | id, fecha, hora_reporte, hora_egreso, hora_ingreso, nombre_paciente, documento, servicio, quien_reporta, destino, procedimiento, medico, conductor, radio_operador, ambulancia, observacion, mes |

> **Note:** `TrasladoPaciente` has no `estado_cierre` field. Month close state is managed exclusively via `ControlMes`.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Month derivation is consistent with fecha

*For any* `TrasladoPaciente` record saved with a valid `fecha`, the `mes` field SHALL equal `fecha.month`.

**Validates: Requirements 4.2**

---

### Property 2: Closed month blocks all write operations

*For any* `TrasladoPaciente` record whose `mes` corresponds to a `ControlMes` with `estado = CERRADO`, any attempt to create, update, or delete that record SHALL be rejected — both at the model layer (raising `ValidationError`) and at the view layer (returning HTTP 403).

**Validates: Requirements 3.9, 5.4**

---

### Property 3: Filter returns only matching records

*For any* combination of `mes` and optional day range `[dia_desde, dia_hasta]`, the set of `TrasladoPaciente` records returned by the filter queryset SHALL contain only records where `fecha.month == mes` and, if a day range is provided, `dia_desde <= fecha.day <= dia_hasta`. No record outside the filter bounds SHALL appear in the result.

**Validates: Requirements 2.5**

---

### Property 4: Record persistence preserves all fields

*For any* valid `TrasladoPaciente` data (all required fields present, fecha not in the future, month open), saving the record and then retrieving it from the database SHALL yield an object with all fields equal to the original input values, including the automatically derived `mes`.

**Validates: Requirements 3.7, 4.1, 4.2**

---

### Property 5: Required field validation always rejects incomplete records

*For any* `TrasladoPaciente` form submission where one or more of the required fields (`fecha`, `hora_reporte`, `nombre_paciente`, `documento`) are blank or missing, the system SHALL reject the submission with field-level validation errors and SHALL NOT persist any record to the database.

**Validates: Requirements 3.8**

---

### Property 6: Annual cleanup resets all state

*For any* system state — any number of `TrasladoPaciente` records and any combination of open/closed `ControlMes` states — after the annual cleanup operation completes, the count of `TrasladoPaciente` records SHALL be zero and every `ControlMes` row SHALL have `estado = ABIERTO`.

**Validates: Requirements 9.3**

---

### Property 7: Self password change correctness

*For any* authenticated user, a self-password-change request SHALL succeed (updating the stored password) if and only if the provided current password matches the stored password AND the new password and confirmation are identical. Any other combination SHALL be rejected without modifying the stored password.

**Validates: Requirements 8.3, 8.4, 8.5**

---

### Property 8: Duplicate username is always rejected

*For any* username that already exists in the system, an attempt to create a new user with that same username SHALL be rejected and the total user count SHALL remain unchanged.

**Validates: Requirements 7.4**

---

### Property 9: Excel report contains correct headers and exactly the filtered records

*For any* active filter (mes, optional dia_desde/dia_hasta), the generated Excel file SHALL contain a single worksheet with Spanish column headers matching all `TrasladoPaciente` fields, and exactly one data row per record in the filtered queryset — no more, no fewer.

**Validates: Requirements 6.1, 6.3**

---

### Property 10: Report filename follows the required format

*For any* mes value (1–12) and any report type (Excel or PDF), the `Content-Disposition` header of the generated report response SHALL contain a filename matching the pattern `traslados_<mes>.xlsx` or `traslados_<mes>.pdf` respectively.

**Validates: Requirements 6.6**

---

### Property 11: Password recovery never reveals user existence

*For any* username — whether it exists in the system or not — a POST to the password recovery endpoint SHALL return the same generic contact-director message with the same HTTP status code, revealing no information about whether the username is registered.

**Validates: Requirements 10.4**

---

### Property 12: User management page lists all users

*For any* set of users registered in the system, the user management page (accessible to DIRECTOR) SHALL display every user with their correct username and role, and SHALL NOT omit any registered user.

**Validates: Requirements 7.2**

---

## Error Handling

### Validation Errors (HTTP 200 with form errors)
- Required fields missing on `TrasladoPaciente` form → field-level error messages in modal.
- Future date on `fecha` → field-level error on `fecha`.
- Day range invalid (from > to, or out of month bounds) → inline message in title bar.
- Month > current month selected → inline message in title bar.
- Duplicate username on user creation → form-level error message.
- Password mismatch or wrong current password → form-level error message.

### Authorization Errors (HTTP 403)
- Non-DIRECTOR accessing DIRECTOR-only views → 403 page with message.
- Any user attempting CRUD on a closed month → 403 response (HTMX partial shows error toast/message).

### Not Found (HTTP 404)
- Record ID not found on edit/delete → 404 page.

### Server Errors (HTTP 500)
- Report generation failure (e.g., library error) → error page with user-friendly message; exception logged.

### HTMX Error Handling
- HTMX requests that return non-2xx responses are handled via `htmx:responseError` event listener in `main.js`, which displays a toast notification with the error message.

---

## Testing Strategy

### Unit Tests

Unit tests cover individual model methods, form validation, and service functions. They use Django's `TestCase` with an in-memory SQLite database.

**Model tests (`tests/test_models.py`):**
- `TrasladoPaciente.save()` correctly derives `mes` from `fecha`.
- `TrasladoPaciente.clean()` raises `ValidationError` for future dates.
- `TrasladoPaciente.clean()` raises `ValidationError` when `ControlMes.estado = CERRADO` for the record's month.
- `ControlMes` default state is `ABIERTO`.
- `TrasladoPaciente` has no `estado_cierre` field.

**Form tests (`tests/test_forms.py`):**
- Required fields (`fecha`, `hora_reporte`, `nombre_paciente`, `documento`) trigger errors when blank.
- Optional fields (`hora_egreso`, `hora_ingreso`, `observacion`) are accepted when blank.

**Service tests (`tests/test_services.py`):**
- `generate_excel()` returns a valid `.xlsx` byte stream with correct Spanish headers.
- `generate_excel()` with no records returns headers-only sheet.
- `generate_excel()` filename matches `traslados_<mes>.xlsx`.
- `generate_pdf()` returns a non-empty byte stream.
- `generate_pdf()` filename matches `traslados_<mes>.pdf`.
- Filter queryset returns only records matching `mes` and day range.

**View tests (`tests/test_views.py`):**
- Unauthenticated requests redirect to `/login/`.
- DIRECTOR-only views return 403 for FUNCIONARIO users.
- CRUD views return 403 when `ControlMes.estado = CERRADO` for the target month.
- Password recovery always returns the same generic message regardless of username existence.
- Table update responses use HTMX partial (no full-page reload).

### Integration Tests

- Full login/logout flow via Django test client.
- HTMX partial endpoints return correct HTML fragments.
- Report download endpoints return correct `Content-Disposition` headers and non-empty file content.
- Month close → CRUD blocked end-to-end flow.
- Data cleanup → zero records + all `ControlMes` rows reset to `ABIERTO`.

### Manual / Acceptance Tests

- Visual verification of spreadsheet-like table appearance.
- Double-click opens edit modal on open months; silently ignored on closed months.
- Modal form layout (vertical label:field pairs).
- PDF landscape orientation and print readability.
- Cleanup flow shows report suggestion before confirmation dialog.

### Property-Based Tests (Future)

Property-based testing with Hypothesis is deferred to a future iteration. The correctness properties defined in this document serve as the specification for those future tests.
