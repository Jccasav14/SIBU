# SIBU – Microservicio `admin` (#8)

Backoffice de SIBU (solo rol **admin**). Maneja **catálogos**, **settings/flags**, moderación de estados (delegando a `users`), y un dashboard simple.

✅ **NO duplica** auditoría (eso es `audit_log`) ni creación de profesionales (eso es `users`).

## Puerto

* Docker / Uvicorn: **8008**

## Variables de entorno

Obligatorias:

```env
JWT_SECRET=...
JWT_ALGORITHM=HS256
ADMIN_POSTGRES_DSN=postgresql+asyncpg://user:pass@admin-postgres:5432/sibu_admin
REDIS_URL=redis://redis:6379/2
```

Opcionales:

```env
USERS_URL=http://users:8000
AUDIT_LOG_URL=http://audit-log:8000

# Si tu `users` tiene rutas diferentes para cambiar status, ajusta:
USERS_PATCH_USER_STATUS_ENDPOINT=/users/admin/users/{email}/status
USERS_PATCH_PROFESSIONAL_STATUS_ENDPOINT=/users/admin/professionals/{email}/status
```

## Nx

Desde el root del monorepo:

```bash
nx serve admin
nx test admin
nx run admin:docker-build
```

## Docker compose (snippet)

> Ejemplo mínimo. Ajusta redes/volúmenes a tu monorepo.

```yaml
services:
  admin:
    build:
      context: .
      dockerfile: apps/admin/Dockerfile
    environment:
      JWT_SECRET: "dev-secret"
      JWT_ALGORITHM: "HS256"
      ADMIN_POSTGRES_DSN: "postgresql+asyncpg://postgres:postgres@admin-postgres:5432/sibu_admin"
      REDIS_URL: "redis://redis:6379/2"
      USERS_URL: "http://users:8000"      # opcional
      AUDIT_LOG_URL: "http://audit-log:8000" # opcional
    ports:
      - "8008:8008"
    depends_on:
      - admin-postgres
      - redis

  admin-postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: sibu_admin
    ports:
      - "5439:5432"

  redis:
    image: redis:7
    ports:
      - "6382:6379"
```

## API (Swagger)

* `GET /health`

Catálogos:
* `GET /admin/catalog/areas`
* `POST /admin/catalog/areas`
* `PATCH /admin/catalog/areas/{id}`
* `GET /admin/catalog/services`
* `POST /admin/catalog/services`
* `PATCH /admin/catalog/services/{id}`

Settings / Flags:
* `GET /admin/settings`
* `PUT /admin/settings/{key}`
* `GET /admin/flags`
* `PUT /admin/flags/{key}`

Moderación (delegado a `users` si está disponible):
* `PATCH /admin/users/{email}/status`
* `PATCH /admin/professionals/{email}/status`

Dashboard:
* `GET /admin/overview`

## Redis (obligatorio)

Se cachea con TTL (60–300s) y se invalida por prefijo:

* `admin:catalog:*`
* `admin:settings`
* `admin:flags`
* `admin:overview`

Al actualizar catálogos/settings/flags se ejecuta `invalidate_prefix("admin:")` o `invalidate_prefix("admin:catalog:")`.

## Audit log (integración)

Este microservicio puede enviar eventos **livianos** a `audit_log` por REST (**best-effort**):

* Configura `AUDIT_LOG_URL`.
* `admin` **reenvía el mismo Authorization header** del request del admin hacia `audit_log`.

📌 **¿Debo modificar `audit_log`?**

No necesariamente.

En tu implementación actual de `audit_log`, el endpoint `POST /audit/events` exige `require_admin`. Como la llamada de `admin` reusa el token del admin (UI/backoffice), va a funcionar.

Si en el futuro quieres service-to-service sin token humano, ahí sí conviene extender `audit_log` para aceptar un shared-secret / mTLS / client credentials.

## Ejemplos cURL

> Reemplaza `$TOKEN_ADMIN` por un JWT con claims `{email, role: "admin"}`.

```bash
curl -s http://localhost:8008/health

curl -s http://localhost:8008/admin/catalog/areas \
  -H "Authorization: Bearer $TOKEN_ADMIN"

curl -s -X POST http://localhost:8008/admin/catalog/areas \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Psicología","enabled":true}'

curl -s -X PUT http://localhost:8008/admin/flags/maintenance_mode \
  -H "Authorization: Bearer $TOKEN_ADMIN" \
  -H "Content-Type: application/json" \
  -d '{"enabled":true}'

curl -s http://localhost:8008/admin/overview \
  -H "Authorization: Bearer $TOKEN_ADMIN"
```
