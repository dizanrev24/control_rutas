# Copilot instructions for control_rutas (Django 5)

Purpose: Dar a agentes de IA el contexto mínimo para trabajar con productividad en este repo. Mantén patrones existentes y el texto de UI en español.

## Big picture
- Stack: Django 5.2, custom user model `users.Usuario`, SQL Server vía `mssql-django` + `pyodbc` (ODBC Driver 18), crispy-forms con `crispy_bootstrap5` (+ Bootstrap 5 por CDN en templates).
- Apps y flujo:
  - `users`: Auth, dashboard, CRUD de usuarios. Las URLs raíz ya incluyen todas las apps en `core/urls.py`.
  - `clientes` ↔ `rutas` (via `Ruta` y `RutaDetalle`) ↔ `asignaciones` (ruta→vendedor) ↔ `planificacion` (plan diario) ↔ `ventas` (Venta + `DetalleVenta`) ↔ `pedidos` (Pedido + `DetallePedido`).
  - Relaciones clave: `RutaDetalle(ruta, cliente)`, `Asignacion(ruta, vendedor[rol=vendedor])`, `Planificacion(asignacion, ruta_detalle)`, `DetallePlanificacion(planificacion, geo/foto/estado)`, `Venta(detalle_planificacion, cliente)`, `Pedido(detalle_planificacion, cliente)`.
  - Vendedor: es el propio `users.Usuario` con `rol='vendedor'` (no hay perfil separado).
- Por qué así: separa catálogos (clientes, productos) del flujo operativo (rutas→asignaciones→planificación→visitas→ventas/pedidos) y centraliza roles/permisos en `Usuario`.

## Convenciones del proyecto
- Auth y routing:
  - `LOGIN_URL='login'`, `LOGIN_REDIRECT_URL='home'`. Usa `@login_required` / `LoginRequiredMixin` (ver `users.views`).
  - Logout solo por POST (`logout_view` + formulario oculto en `templates/base.html`). No crear GET logouts; siempre POST con CSRF.
  - Root URLs ya incluyen: `users`, `clientes`, `productos`, `rutas`, `asignaciones`, `camiones`, `planificacion`, `ventas`, `pedidos`, `reportes`. Al agregar apps nuevas, inclúyelas explícitamente en `core/urls.py` siguiendo el mismo patrón.
- Mensajes y UX:
  - Las vistas establecen `messages.success/error` y se renderizan como SweetAlert en `base.html`. Después de acciones, redirige.
  - Copia de UI en español en templates y modelos.
- Formularios/UI:
  - `django-crispy-forms` con Bootstrap 5. Sigue `users/forms.py` (helper, Layout, Row/Column).
  - Ventas/Pedidos usan formsets con `extra=0` y UI dinámica tipo POS en `templates/ventas/venta_form.html` y `templates/pedidos/pedido_form.html` (lista de productos cargados en camión vs. catálogo, buscador, “carrito” que sincroniza con el formset oculto).
- Modelo de datos:
  - Usuario: `AUTH_USER_MODEL='users.Usuario'` con helpers (`es_vendedor`, `puede_gestionar_rutas`, etc.). Usa `get_user_model()`/`settings.AUTH_USER_MODEL` en FKs.
  - Productos: estado en `Producto.estado` (usa `estado='activo'` para activos). No existe `Producto.activo`.
  - Soft-delete usuarios: alterna `is_active` en lugar de borrar (en flujos de `users`).
- Paginación: listas con `paginate_by = 10` por defecto.
- Media/archivos: `MEDIA_URL` y `MEDIA_ROOT` están configurados en `core/settings.py` y se sirven en desarrollo en `core/urls.py` con `static()` cuando `DEBUG=True`.

## Desarrollo local y flujos
- DB: SQL Server (ver `core/settings.py`). Requiere ODBC Driver 18. Ajusta credenciales por entorno.
- Comandos comunes:
  - Run: `python manage.py runserver`
  - Migrate: `python manage.py makemigrations`; `python manage.py migrate`
  - Superuser: `python manage.py createsuperuser`
  - Tests: pytest disponible (`pytest-django`) o `python manage.py test` (tests mínimos).
- Templates: se cargan desde `templates/` vía `TEMPLATES['DIRS']`. Layout base en `templates/base.html` (sidebar, SweetAlert, logout por POST).

## Al agregar funcionalidades
- Vistas: preferir CBVs con `LoginRequiredMixin`. Establecer `messages.success/error` y redirigir; mantener copia en español. Tomar de referencia `UsuarioCrear/Actualizar/Listar`.
- URLs: cablea las URLs de cada app en `core/urls.py` (por ejemplo, `path('clientes/', include('clientes.urls'))`). Usa nombres descriptivos (p. ej., `cliente_listar`).
- Permisos: verifica helpers de rol en `Usuario` (p. ej., `request.user.puede_gestionar_rutas`) antes de mutar entidades de ruta/asignación/plan.
- Modelos: referencia `settings.AUTH_USER_MODEL` en FKs; preserva `related_name` existentes y restricciones (`unique_together` en `RutaDetalle`, `Asignacion`, etc.). Mantén precisión de `DecimalField` consistente con `Producto`/ventas.

## Ejemplos del código
- Logout por POST: ver `templates/base.html` y `users.views.logout_view`.
- Soft delete de usuarios: `users.views.usuario_eliminar`.
- Composición y secuencia de rutas: `rutas.models.Ruta` + `RutaDetalle(orden_visita)`.
- Cadena asignación→planificación→visita→venta/pedido: `asignaciones.Asignacion` → `planificacion.Planificacion` → `planificacion.DetallePlanificacion` → `ventas.Venta` / `pedidos.Pedido`.
