# SIBU Notifications Service (Event-Driven)

Microservicio **event-driven** que consume eventos desde **Kafka** y ejecuta acciones de notificación (por ahora: log + almacenamiento en memoria para debug).

## Qué resuelve
- Arquitectura **Event-Driven**
- Comunicación **Kafka**
- Desacopla `cases` de `notifications` (no hay llamadas HTTP entre servicios)

## Variables de entorno
- `KAFKA_ENABLED` = `true|false` (default `true`)
- `KAFKA_BOOTSTRAP` = `kafka:29092` (docker) o `localhost:9092` (host)
- `KAFKA_TOPIC_CASE_EVENTS` = `sibu.case.events`
- `KAFKA_GROUP_ID` = `notifications-service`
- `CORS_ORIGINS` = `http://localhost:5173`

## Endpoints
- `GET /health` -> ok
- `GET /notifications/events` -> últimos eventos recibidos (debug)

## Docker Compose (snippet)
```yaml
  notifications:
    build:
      context: ..
      dockerfile: apps/notifications/Dockerfile
    environment:
      KAFKA_BOOTSTRAP: kafka:29092
      KAFKA_TOPIC_CASE_EVENTS: sibu.case.events
      KAFKA_GROUP_ID: notifications-service
      CORS_ORIGINS: http://localhost:5173
    ports:
      - "8004:8004"
    depends_on:
      kafka:
        condition: service_started
      zookeeper:
        condition: service_started
```

## Probar
1) `docker compose up -d --build notifications`
2) Swagger: `http://localhost:8004/docs`
3) Crea un caso (cuando `cases` publique eventos) y mira logs:
   `docker compose logs -f notifications`
