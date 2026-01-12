# SIBU · Microservicio #6: audit_log (Audit Log)

Servicio central de auditoría para SIBU. Consume eventos **Kafka + RabbitMQ + MQTT** y los persiste en **MongoDB**. Expone una API REST (FastAPI/Swagger) para dashboard en Vue (solo **admin**; opcional **professional** solo "mine").

## 1) Features

- ✅ Ingesta multi-canal:
  - Kafka: topics configurables (`KAFKA_TOPICS`).
  - RabbitMQ: cola configurable (`RABBITMQ_QUEUE`) para jobs/reintentos.
  - MQTT: topics configurables (`MQTT_TOPICS`) para estado/telemetría.
- ✅ Robustez: si Kafka/Rabbit/MQTT caen, **la API REST se mantiene arriba** y los consumidores reintentan.
- ✅ MongoDB: colección `audit_events` + índices.
- ✅ Seguridad: JWT (mismo `JWT_SECRET/JWT_ALGORITHM` del monorepo). Por defecto, **solo admin** puede ver auditoría global.
- ✅ API REST: filtros, paginación, detalle, summary, top actors, security feed, export CSV.

## 2) Estructura

```
apps/audit_log/
  Dockerfile
  requirements.txt
  project.json
  README.md
  app/
    main.py
    settings.py
    api/routes.py
    domain/schemas.py
    infrastructure/
      mongo.py
      repository.py
      consumers/
        kafka_consumer.py
        rabbit_consumer.py
        mqtt_subscriber.py
    security/jwt.py
  tests/
```

## 3) Variables de entorno

```bash
# Mongo
MONGO_URI=mongodb://localhost:27017
MONGO_DB=audit

# CORS
CORS_ORIGINS=http://localhost:5174

# JWT
JWT_SECRET=SIBU_SUPER_SECRET_CAMBIAME
JWT_ALGORITHM=HS256

# Kafka
KAFKA_BOOTSTRAP=localhost:9092
KAFKA_TOPICS=sibu.events,sibu.user.events,sibu.cases.events,sibu.appointments.events
KAFKA_GROUP_ID=audit-log

# RabbitMQ
RABBITMQ_URL=amqp://guest:guest@localhost:5672/
RABBITMQ_QUEUE=sibu.audit.queue

# MQTT
MQTT_BROKER=localhost
MQTT_PORT=1883
MQTT_TOPICS=sibu/professionals/+/status,sibu/system/#,sibu/telemetry/#

# Opcionales
AUDIT_PROFESSIONAL_CAN_VIEW_MINE=false
AUDIT_CONSUMERS_ENABLED=true
LOG_LEVEL=INFO
```

## 4) Ejecutar local

### 4.1 Con venv (fuera de Docker)

```bash
cd apps/audit_log
pip install -r requirements.txt

# Windows (Nx similar a otros ms)
python -m uvicorn app.main:app --host 0.0.0.0 --port 8006 --reload
```

Swagger:

- `http://localhost:8006/docs`

### 4.2 Con Nx

```bash
npx nx serve audit-log
```

## 5) Docker Compose (snippet)

> Nota: esto es un **snippet** para integrar en tu `docker-compose.yml` del monorepo.

```yaml
services:
  mongo-audit:
    image: mongo:7
    ports:
      - "27017:27017"
    volumes:
      - mongo_audit:/data/db

  audit-log:
    build:
      context: .
      dockerfile: apps/audit_log/Dockerfile
    environment:
      MONGO_URI: mongodb://mongo-audit:27017
      MONGO_DB: audit
      JWT_SECRET: SIBU_SUPER_SECRET_CAMBIAME
      JWT_ALGORITHM: HS256
      CORS_ORIGINS: http://localhost:5174
      KAFKA_BOOTSTRAP: kafka:9092
      KAFKA_TOPICS: sibu.events,sibu.user.events,sibu.cases.events,sibu.appointments.events
      RABBITMQ_URL: amqp://guest:guest@rabbitmq:5672/
      RABBITMQ_QUEUE: sibu.audit.queue
      MQTT_BROKER: mosquitto
      MQTT_PORT: 1883
      MQTT_TOPICS: sibu/professionals/+/status,sibu/system/#,sibu/telemetry/#
    ports:
      - "8006:8000"
    depends_on:
      - mongo-audit

volumes:
  mongo_audit:
```

## 6) API (resumen)

> Todos los endpoints de auditoría global requieren `role=admin`.

- `GET /health`
- `GET /audit/events` (filtros + paginación)
- `GET /audit/events/{event_id}`
- `GET /audit/entities/{entity_type}/{entity_id}`
- `GET /audit/summary` (24h y 7d)
- `GET /audit/top-actors`
- `GET /audit/security`
- `GET /audit/export.csv`
- `GET /audit/mine` (solo professional, si `AUDIT_PROFESSIONAL_CAN_VIEW_MINE=true`)
- `POST /audit/events` (opcional, admin/service-to-service)

## 7) Ejemplos de eventos

### Kafka (JSON)

Ejemplo payload:

```json
{
  "event_id": "0e1c2f31-0d41-4f01-9a2f-2b8fd4df2b4d",
  "type": "case.shared",
  "service": "cases",
  "actor": "pro1@u.edu",
  "actor_role": "professional",
  "entity_type": "case",
  "entity_id": "case_123",
  "timestamp": "2025-12-29T12:00:00Z",
  "correlation_id": "corr-abc",
  "severity": "INFO",
  "tags": ["derivation"]
}
```

### RabbitMQ (job/work events)

```json
{
  "event_id": "...",
  "job_type": "notifications.send",
  "status": "failed",
  "error_message": "SMTP timeout",
  "service": "notifications",
  "actor": "system",
  "severity": "ERROR",
  "correlation_id": "corr-xyz"
}
```

### MQTT (status/telemetría)

Topic:

```
sibu/professionals/pro1@u.edu/status
```

Payload:

```json
{
  "type": "professional.status",
  "status": "online",
  "timestamp": "2025-12-29T12:00:00Z"
}
```

## 8) Tests

```bash
cd apps/audit_log
pytest -q
```

Los tests usan un `FakeRepo` (in-memory) para validar auth/roles y redacción de secretos.
