# SIBU Microservicio #7 — Reports (CQRS Read Model + Reportería & Analytics)

Microservicio **reports** para consultas rápidas (dashboards), KPIs y exportaciones **async**.  
Construye **read models/materializaciones** consumiendo eventos de **Kafka** y procesa **jobs** de exportación vía **RabbitMQ**.

> Importante: este servicio **NO** expone flujos/endpoints de estudiante para reservas/casos.

## Features

- ✅ **CQRS Read Model**: materializa métricas diarias en Postgres desde Kafka.
- ✅ **Jobs async** con RabbitMQ:
  - Exportaciones: CSV / XLSX (guardado en `/tmp/exports`).
  - Reintentos y **DLQ** recomendado (implementado con dead-letter exchange).
- ✅ Integración opcional con **audit-log** por REST (proxy/aggregator) **sin duplicar payload sensible**.
- ✅ **JWT + Roles**:
  - `admin`: acceso global a reportes.
  - `professional`: solo `/reports/mine` y `/reports/audit` (mine) si `REPORTS_PROFESSIONAL_CAN_VIEW_MINE=true`.
- ✅ **Degraded mode**: arranca aunque Kafka/Rabbit/Audit-log estén caídos.
- ✅ Cache Redis para queries de dashboard (TTL 60–300s recomendado).
- ✅ `GET /metrics` (Prometheus) opcional.

---

## Variables de entorno (obligatorio)

- `REPORTS_POSTGRES_DSN`
- `REDIS_URL`
- `CORS_ORIGINS`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `KAFKA_BOOTSTRAP`
- `KAFKA_TOPICS`
- `KAFKA_GROUP_ID`
- `RABBITMQ_URL`
- `RABBITMQ_QUEUE`
- `AUDIT_LOG_URL`
- `REPORTS_PROFESSIONAL_CAN_VIEW_MINE`

Ejemplo (local):

```bash
export REPORTS_POSTGRES_DSN="postgresql+asyncpg://sibu:sibu@localhost:5437/sibu_reports"
export REDIS_URL="redis://localhost:6379/1"
export CORS_ORIGINS="http://localhost:5174"
export JWT_SECRET="SIBU_SUPER_SECRET_CAMBIAME"
export JWT_ALGORITHM="HS256"
export KAFKA_BOOTSTRAP="localhost:9092"
export KAFKA_TOPICS="sibu.user.events,sibu.case.events,sibu.appointment.events"
export KAFKA_GROUP_ID="reports-service"
export RABBITMQ_URL="amqp://guest:guest@localhost:5672/"
export RABBITMQ_QUEUE="sibu.reports.queue"
export AUDIT_LOG_URL="http://localhost:8006"
export REPORTS_PROFESSIONAL_CAN_VIEW_MINE="false"
```

---

## Correr local (Nx)

Desde el root del monorepo:

```bash
npx nx serve reports
```

Puerto: `8007`

---

## Correr con Docker

Build:

```bash
npx nx run reports:docker-build
```

Run:

```bash
docker run --rm -p 8007:8007 --env-file .env sibu-reports:local
```

---

## docker-compose (snippet)

> Nota: `audit_log` ya existe. Aquí solo se referencia.

```yaml
services:
  reports:
    build:
      context: .
      dockerfile: apps/reports/Dockerfile
    environment:
      REPORTS_POSTGRES_DSN: postgresql+asyncpg://sibu:sibu@reports-postgres:5432/sibu_reports
      REDIS_URL: redis://reports-redis:6379/1
      CORS_ORIGINS: http://localhost:5174
      JWT_SECRET: SIBU_SUPER_SECRET_CAMBIAME
      JWT_ALGORITHM: HS256
      KAFKA_BOOTSTRAP: kafka:9092
      KAFKA_TOPICS: sibu.user.events,sibu.case.events,sibu.appointment.events
      KAFKA_GROUP_ID: reports-service
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
      RABBITMQ_QUEUE: sibu.reports.queue
      AUDIT_LOG_URL: http://audit_log:8006
      REPORTS_PROFESSIONAL_CAN_VIEW_MINE: "false"
    ports:
      - "8007:8007"
    depends_on:
      - reports-postgres
      - reports-redis
      - kafka
      - rabbitmq
      - audit_log

  reports-postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: sibu
      POSTGRES_PASSWORD: sibu
      POSTGRES_DB: sibu_reports
    ports:
      - "5437:5432"

  reports-redis:
    image: redis:7
    ports:
      - "6381:6379"

  # kafka, rabbitmq y audit_log deben existir en tu stack del monorepo
```

---

## API (Swagger)

- `GET /health`
- `GET /reports/summary?window=24h|7d|30d`
- `GET /reports/activity?from=&to=&service=&event_type=&severity=&role=`
- `GET /reports/cases?from=&to=`
- `GET /reports/appointments?from=&to=`
- `GET /reports/security?from=&to=`
- `GET /reports/top-actors?from=&to=&limit=10`
- `GET /reports/audit?...` (proxy hacia audit-log)
- `POST /reports/export` (async, RabbitMQ)
- `GET /reports/export/{job_id}` (status)
- `GET /reports/export/{job_id}/download` (download cuando está listo)
- `GET /reports/mine?from=&to=` (solo professional si habilitado)
- `GET /metrics` (opcional)

---

## Ejemplo de eventos Kafka (JSON)

### 1) Case event (cuenta en cases_metrics + daily_metrics)

Topic: `sibu.case.events`

```json
{
  "event_type": "case.created",
  "service": "cases",
  "severity": "info",
  "timestamp": "2025-12-30T18:40:00Z",
  "actor": "pro1@uce.edu.ec",
  "role": "professional"
}
```

### 2) Security event (cuenta en security_metrics)

Topic: `sibu.user.events`

```json
{
  "event_type": "auth.login.failed",
  "service": "auth",
  "severity": "warn",
  "timestamp": "2025-12-30T18:42:00Z",
  "actor": "admin@uce.edu.ec",
  "role": "admin"
}
```

---

## Ejemplo de job RabbitMQ (export)

Queue: `sibu.reports.queue`

```json
{
  "action": "export",
  "job_id": "8c0c9d4dfb5f4b72a3432c9c7e4b1f0a",
  "type": "cases",
  "params": {
    "from": "2025-12-01",
    "to": "2025-12-30",
    "format": "csv",
    "filters": {},
    "requested_by": "admin@uce.edu.ec",
    "role": "admin"
  }
}
```

---

## Notas de robustez

- Si Kafka está caído: el consumer entra en retry con backoff, **sin tumbar el API**.
- Si RabbitMQ está caído: la API sigue levantando; el endpoint `/reports/export` fallará con `503`/error si no puede publicar.
- Si audit-log está caído: `/reports/audit` devuelve `503` y **reports** sigue levantado.

---

## TODO sugeridos (futuro)

- Alembic migrations.
- Export de audit via audit-log (`/audit/export.csv`) o implementación de export proxy.
- MinIO/S3 para persistir exports.
- Métricas Prometheus por tipo de evento (Counters) + histogram de latencia.
