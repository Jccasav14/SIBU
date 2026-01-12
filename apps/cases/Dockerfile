FROM python:3.11-slim

WORKDIR /app

# Copiamos requirements primero para cache
COPY apps/cases/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copiamos el microservicio
COPY apps/cases/app /app/apps/cases/app

EXPOSE 8003

ENV PYTHONPATH=/app

CMD ["python", "-m", "uvicorn", "apps.cases.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
