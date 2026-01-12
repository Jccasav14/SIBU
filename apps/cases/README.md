# SIBU - Cases Microservice (FastAPI)

Microservicio **cases** para gestión de casos (tickets) con trazabilidad (timeline).
Arquitectura tipo **hexagonal/layers** similar a tu `auth`:

- `app/api`: endpoints + schemas
- `app/application/services`: lógica de negocio
- `app/domain`: entidades de dominio, enums, excepciones
- `app/infrastructure/db`: sesión, modelos ORM, repositorios
- `app/security`: dependencias de autenticación (JWT) y permisos

## Features (MVP funcional)
- Crear caso
- Listar casos (filtros: status, priority, mine)
- Obtener detalle de un caso
- Actualizar título/descripcion/prioridad
- Asignar profesional
- Cambiar estado (OPEN, IN_PROGRESS, RESOLVED, CLOSED)
- Timeline por caso (auditoría)
- Vincula el caso a un **student_id**
- Compartir un caso con **otro profesional** (por `user_id`) o con **otra área** (por `area`)
- Agregar y listar **notas** (historia clínica / seguimiento)

## Seguridad
Requiere `Authorization: Bearer <JWT>`.
El token se valida con:
- `JWT_SECRET` (o `SIBU_SUPER_SECRET_CAMBIAME`)
- `JWT_ALGORITHM` (default `HS256`)

El payload esperado puede incluir:
- `sub`: user_id (string/uuid)
- `roles`: lista o string (ej: ["admin"], ["professional"])
- `area` (opcional): área del profesional (ej: `PSY`, `SOCIAL`, `MEDICAL`)

> Si no tienes aún tokens reales, puedes desactivar la autenticación con `AUTH_DISABLED=true` (solo para desarrollo).

## Configuración por variables de entorno
- `POSTGRES_DSN` (ej: `postgresql://sibu:sibu@localhost:5433/sibu`)
  - Si no se define, usa SQLite local `sqlite:///./cases.db`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `CORS_ORIGINS` (default `*`)
- `AUTH_DISABLED` (default `false`)

## Nota sobre esquema de DB
Este servicio usa `Base.metadata.create_all` para crear tablas en arranque (MVP).
Si ya tenías una DB previa sin los nuevos campos/tablas, lo más simple en dev es:
- borrar el volumen `pgdata` (o recrear la DB),
- o dropear tablas `cases`, `case_timeline`, `case_access`, `case_notes`.

## Ejecutar local
```bash
cd apps/cases
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8003 --reload
```

## Docker
```bash
docker build -t sibu-cases -f apps/cases/Dockerfile .
docker run --rm -p 8003:8003 -e AUTH_DISABLED=true sibu-cases
```

## API Docs
- Swagger: `http://localhost:8003/docs`
