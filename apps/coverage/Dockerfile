FROM python:3.12-slim
WORKDIR /app

COPY apps/coverage/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/coverage/app /app/app
COPY apps/coverage/tests /app/tests
COPY apps/coverage/README.md /app/README.md

EXPOSE 8010
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8010"]
