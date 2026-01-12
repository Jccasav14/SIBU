FROM python:3.12-slim

WORKDIR /app

# System deps (optional but useful for cryptography wheels)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY apps/appointments/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/appointments /app/apps/appointments

ENV PYTHONPATH=/app
EXPOSE 8005

CMD ["python","-m","uvicorn","apps.appointments.app.main:app","--host","0.0.0.0","--port","8005"]
