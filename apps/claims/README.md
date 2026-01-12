# SIBU Claims Microservice (#9)

**Service:** `claims`  
**Port:** `8009`  
**Tech:** FastAPI + Async SQLAlchemy + Postgres (dedicated) + Redis (mandatory cache)  

## What this microservice does

This service manages **university insurance claims ("siniestros")**.

It is **NOT** appointment billing and it does **NOT** charge students for appointments.

Typical use cases:
- Accident reimbursement (e.g., broken leg) up to a coverage cap (e.g., `$100`).
- Family death support according to the coverage.
- Illnesses or other covered events.

It covers the full workflow:
`create (DRAFT) -> submit -> review (approve/reject) -> payment -> close`.

## Roles & Access (mandatory)

All endpoints except `/health` require JWT and role authorization.

Allowed roles:
- `insurance`
- `admin`

Forbidden:
- `professional` (will receive **403**)

All protected endpoints use:
`Depends(require_insurance_or_admin)`

## Environment Variables

```env
# Security
JWT_SECRET=supersecret
JWT_ALGORITHM=HS256

# Postgres (dedicated database for claims)
CLAIMS_POSTGRES_DSN=postgresql+asyncpg://claims:claims@claims-postgres:5432/claims

# Redis (mandatory cache)
REDIS_URL=redis://redis:6379/3
REDIS_TTL_SECONDS=120

# Optional integrations (degraded mode)
USERS_URL=http://users:8000

AUDIT_LOG_ENABLED=true
AUDIT_LOG_URL=http://audit_log:8006
AUDIT_LOG_TIMEOUT_SECONDS=2

# Optional Mongo archive (degraded mode)
MONGO_ENABLED=false
MONGO_URI=mongodb://mongo:27017
MONGO_DB=claims_history
```

## Nx Commands

From repo root:

```bash
nx serve claims
nx test claims
nx lint claims
nx run claims:docker-build
```

## Docker Build & Run

Build (repo root):

```bash
docker build -f apps/claims/Dockerfile -t sibu-claims:local .
```

Run (example):

```bash
docker run --rm -p 8009:8009 \
  -e JWT_SECRET=supersecret \
  -e JWT_ALGORITHM=HS256 \
  -e CLAIMS_POSTGRES_DSN=postgresql+asyncpg://claims:claims@claims-postgres:5432/claims \
  -e REDIS_URL=redis://redis:6379/3 \
  sibu-claims:local
```

## docker-compose snippet

```yaml
services:
  claims-postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: claims
      POSTGRES_PASSWORD: claims
      POSTGRES_DB: claims
    ports:
      - "5439:5432"

  redis:
    image: redis:7
    ports:
      - "6380:6379"

  claims:
    build:
      context: .
      dockerfile: apps/claims/Dockerfile
    environment:
      JWT_SECRET: supersecret
      JWT_ALGORITHM: HS256
      CLAIMS_POSTGRES_DSN: postgresql+asyncpg://claims:claims@claims-postgres:5432/claims
      REDIS_URL: redis://redis:6379/3
      REDIS_TTL_SECONDS: 120
      AUDIT_LOG_ENABLED: "false"
      MONGO_ENABLED: "false"
    ports:
      - "8009:8009"
    depends_on:
      - claims-postgres
      - redis
```

## API Overview

Health:
- `GET /health`

Claims:
- `POST /claims` (create claim in `DRAFT`)
- `GET /claims` (list with optional filters: `status`, `type`, `student_id`)
- `GET /claims/{id}` (details)
- `PATCH /claims/{id}` (edit allowed fields only if `DRAFT`)
- `POST /claims/{id}/submit` (`DRAFT -> SUBMITTED`)
- `POST /claims/{id}/review` (`SUBMITTED/UNDER_REVIEW -> APPROVED/REJECTED`)
- `POST /claims/{id}/payment` (`APPROVED -> PAID + CLOSED`)
- `GET /claims/{id}/timeline`

Documents:
- `POST /claims/{id}/documents`
- `GET /claims/{id}/documents`

Dashboard:
- `GET /claims/overview`

## Redis Cache (mandatory)

Cached endpoints:
- `GET /claims`
- `GET /claims/overview`
- `GET /claims/{id}`
- `GET /claims/{id}/documents`
- `GET /claims/{id}/timeline`

Invalidation is executed on create/update/submit/review/payment/document.

## Mongo (optional)

Mongo is used **only** as an optional long-term archive for **non-sensitive** claim timeline events.
If Mongo is down, the service continues in **degraded mode** (warning logs only).

## Frontend readiness

This service is designed for a future Vue UI:
- A menu section **"Insurance / Claims"** visible only for `insurance` and `admin`.
- Endpoints return clean JSON (no raw SQLAlchemy models).
- Filtering and dashboard endpoints are ready for tables + KPI cards.

## Curl Examples

> Replace `<TOKEN>` with a JWT that contains `{ "role": "admin" }` or `{ "role": "insurance" }`.

Create claim:

```bash
curl -X POST http://localhost:8009/claims \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id":"0102030405",
    "claim_type":"ACCIDENT",
    "occurred_at":"2025-12-31T00:00:00Z",
    "reported_at":"2025-12-31T00:00:00Z",
    "description":"Broken leg",
    "requested_amount":80,
    "coverage_cap":100
  }'
```

Submit:

```bash
curl -X POST http://localhost:8009/claims/<ID>/submit \
  -H "Authorization: Bearer <TOKEN>"
```

Review approve:

```bash
curl -X POST http://localhost:8009/claims/<ID>/review \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"decision":"APPROVE","approved_amount":95}'
```

Pay:

```bash
curl -X POST http://localhost:8009/claims/<ID>/payment \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"payment_method":"BANK_TRANSFER","payment_reference":"REF-123"}'
```
