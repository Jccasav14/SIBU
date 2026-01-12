# SIBU Coverage Microservice (coverage)

FastAPI microservice responsible for managing **insurance coverages & policies** for the university insurance program.

It defines coverage rules that will be consumed by:
- **Vue frontend** (to display available coverages/policies)
- **claims microservice** (to calculate coverage caps and validate coverage rules)

This microservice **does not** manage individual claims/siniestros.

## Key Features

- JWT-protected API with strict role validation
  - `admin`: full CRUD
  - `insurance`: read-only
  - `professional` and any other role: **403**
- PostgreSQL persistence (dedicated database)
- Redis caching for read endpoints + prefix invalidation on writes
- Business rule: **no two active policies can overlap** for the same `claim_type` and date range
- Full Swagger docs at `/docs`

---

## Environment Variables

Required:

- `JWT_SECRET`
- `JWT_ALGORITHM`
- `COVERAGE_POSTGRES_DSN`  
  Example: `postgresql+asyncpg://coverage_user:coverage_pass@postgres:5432/coverage_db`
- `REDIS_URL`  
  Example: `redis://redis:6379/4`

Optional:

- `REDIS_TTL_SECONDS` (60–300 recommended; default: 120)

---

## Nx Commands

From the monorepo root:

```bash
nx serve coverage
nx test coverage
nx run coverage:docker-build
```

---

## Run with Docker (standalone build)

From the monorepo root:

```bash
docker build -f apps/coverage/Dockerfile -t sibu-coverage:latest .
docker run --rm -p 8010:8010   -e JWT_SECRET="change-me"   -e JWT_ALGORITHM="HS256"   -e COVERAGE_POSTGRES_DSN="postgresql+asyncpg://coverage_user:coverage_pass@host.docker.internal:5432/coverage_db"   -e REDIS_URL="redis://host.docker.internal:6379/4"   -e REDIS_TTL_SECONDS=120   sibu-coverage:latest
```

Swagger: `http://localhost:8010/docs`

---

## docker-compose snippet (monorepo)

```yaml
services:
  coverage:
    build:
      context: .
      dockerfile: apps/coverage/Dockerfile
    ports:
      - "8010:8010"
    environment:
      JWT_SECRET: "change-me"
      JWT_ALGORITHM: "HS256"
      COVERAGE_POSTGRES_DSN: "postgresql+asyncpg://coverage_user:coverage_pass@coverage-postgres:5432/coverage_db"
      REDIS_URL: "redis://coverage-redis:6379/4"
      REDIS_TTL_SECONDS: 120
    depends_on:
      - coverage-postgres
      - coverage-redis

  coverage-postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: coverage_user
      POSTGRES_PASSWORD: coverage_pass
      POSTGRES_DB: coverage_db
    ports:
      - "5436:5432"

  coverage-redis:
    image: redis:7
    ports:
      - "6384:6379"
```

---

## API Overview

### Health
- `GET /health`

### Coverage (admin + insurance)
- `GET /coverage`
- `GET /coverage/{id}`
- `GET /coverage/by-claim-type/{claim_type}`

### Coverage (admin only)
- `POST /coverage`
- `PATCH /coverage/{id}`
- `POST /coverage/{id}/activate`
- `POST /coverage/{id}/deactivate`

Caching (Redis):
- `GET /coverage` → `coverage:list`
- `GET /coverage/{id}` → `coverage:item:{id}`
- `GET /coverage/by-claim-type/{claim_type}` → `coverage:type:{claim_type}`

Cache invalidation happens on:
- create
- update
- activate/deactivate

---

## Curl Examples (using JWT)

> Tokens are expected to be issued by the `auth` microservice and must include a `role` claim.

Export a token:

```bash
export ADMIN_TOKEN="YOUR_ADMIN_JWT"
export INSURANCE_TOKEN="YOUR_INSURANCE_JWT"
```

List policies (admin or insurance):

```bash
curl -H "Authorization: Bearer $INSURANCE_TOKEN" http://localhost:8010/coverage
```

Create a policy (admin only):

```bash
curl -X POST http://localhost:8010/coverage \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "claim_type": "ACCIDENT",
    "name": "Accident Basic",
    "description": "Basic accident coverage up to $100",
    "max_coverage_amount": 100,
    "currency": "USD",
    "requires_documents": ["medical_report", "invoice"],
    "waiting_days": 0,
    "is_active": true,
    "valid_from": "2026-01-01",
    "valid_to": "2026-12-31"
  }'
```

Activate/deactivate (admin only):

```bash
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8010/coverage/<id>/deactivate
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" http://localhost:8010/coverage/<id>/activate
```

---

## Future Integration (no coupling)

- **Vue** will consume the read endpoints to display coverage policies and details.
- **claims** will query `/coverage/by-claim-type/{claim_type}` (and/or `/coverage/{id}`) to obtain the policy rules and compute coverage caps.

This microservice does not call other microservices and does not depend on `claims`.
