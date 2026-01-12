FROM python:3.12-slim

WORKDIR /app

COPY apps/audit_log/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY apps/audit_log/app ./app

# Shared libs (same monorepo convention as other services)
COPY libs ./libs

EXPOSE 8006

CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8006"]
