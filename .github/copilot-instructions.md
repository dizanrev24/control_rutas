# Copilot instructions for control_rutas (Django 5)

Purpose: Give AI coding agents the minimum context to be productive in this repo. Keep changes aligned with existing patterns and Spanish UI copy.

## Big picture
- Stack: Django 5.2, custom user model `users.Usuario`, SQL Server via `mssql-django` + `pyodbc` (ODBC Driver 18), crispy-forms (+ Bootstrap via CDN).
- Apps and flow:
  - `users`: Auth, dashboard, user CRUD. Root URLs routed here from `core/urls.py`.
  - `clientes` ↔ `rutas` (via `Ruta` and `RutaDetalle`) ↔ `asignaciones` (route→vendedor) ↔ `planificacion` (daily plan) ↔ `ventas` (Sale + `DetalleVenta`). `vendedores` wraps a profile connected to `users.Usuario`.
  - Relationships: `RutaDetalle(ruta, cliente)`, `Asignacion(ruta, vendedor[rol=vendedor])`, `Planificacion(asignacion, ruta_detalle)`, `DetallePlanificacion(planificacion, geo/photo/state)`, `Venta(detalle_planificacion, cliente)`.
- Why this structure: separates catalog data (clientes, productos) from operational flow (rutas→asignaciones→planificación→visitas→ventas) and enforces user roles centrally on `Usuario`.

## Project conventions
- Auth & routing:
  - Root URLs include only `users.urls` (`core/urls.py`). Add new app URLs explicitly via `include()` when needed.
  - `LOGIN_URL='login'`, `LOGIN_REDIRECT_URL='home'`. Use `@login_required` / `LoginRequiredMixin` consistently (see `users.views`).
  - Logout is POST-only (`logout_view` + hidden form in `templates/base.html`). Don’t create GET logouts; submit a POST with CSRF.
- Messages & UX:
  - Success/error messages are set in views and rendered as SweetAlert in `base.html`. When adding actions, call `messages.success/error` then redirect.
  - Spanish labels/strings across templates and models. Keep UI text in Spanish.
- Forms/UI:
  - Uses `django-crispy-forms` helpers with Bootstrap layout (CDN Bootstrap 5 in templates). Follow patterns in `users/forms.py` (helper, Layout, Row/Column).
  - CRISPY settings use `bootstrap5`, but `crispy_bootstrap4` is installed in apps. Preserve current configuration unless explicitly changing UI system.
- Data model:
  - Custom user: `AUTH_USER_MODEL='users.Usuario'` with `rol` choices and helpers (`es_vendedor`, `puede_gestionar_rutas`, etc.). Always use `get_user_model()`/`settings.AUTH_USER_MODEL` in relations.
  - Soft-delete pattern: user “delete” toggles `is_active`; no hard delete in `users` flows.
- Pagination: list views default to `paginate_by = 10`.
- Media/files: Several `ImageField`s exist but no `MEDIA_*` settings. If implementing uploads, add `MEDIA_URL`, `MEDIA_ROOT`, and serve in dev URLs.

## Local development & workflows
- Database: SQL Server (default connection in `core/settings.py`). Requires ODBC Driver 18. Update env for prod; creds are local-only placeholders.
- Common commands:
  - Run: `python manage.py runserver`
  - Migrate: `python manage.py makemigrations`; `python manage.py migrate`
  - Superuser: `python manage.py createsuperuser`
  - Tests: pytest is available (`pytest-django`), or `python manage.py test` (tests currently minimal).
- Templates: loaded from `templates/` via `TEMPLATES['DIRS']`. Base layout in `templates/base.html` includes sidebar, SweetAlert, and the POST logout form.

## When adding features
- Views: prefer CBVs with `LoginRequiredMixin`. Set `messages.success/error` and redirect; keep Spanish copy. Mirror `UsuarioCrear/Actualizar/Listar` patterns.
- URLs: wire app URLs in `core/urls.py` (e.g., `path('clientes/', include('clientes.urls'))`). Keep route names descriptive (e.g., `cliente_listar`).
- Permissions: check role helpers on `Usuario` (e.g., `request.user.puede_gestionar_rutas`) before mutating route/assignment/plan entities.
- Models: reference `settings.AUTH_USER_MODEL` for user FKs; preserve existing `related_name`s and `unique_together` constraints (e.g., `RutaDetalle`, `Asignacion`).
- Consistency: maintain ordering and `verbose_name*_` meta declarations as in current models. Keep `DecimalField` precision consistent with `Producto`/ventas models.

## Examples from codebase
- POST-only logout via hidden form: see `templates/base.html` and `users.views.logout_view`.
- Soft delete users by toggling `is_active`: `users.views.usuario_eliminar`.
- Route composition and sequencing: `rutas.models.Ruta` + `RutaDetalle(orden_visita)`.
- Assignment and planning chain: `asignaciones.Asignacion` → `planificacion.Planificacion` → `planificacion.DetallePlanificacion` → `ventas.Venta`.
