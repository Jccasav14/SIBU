FROM python:3.12-slim
WORKDIR /app

COPY apps/auth/requirements.txt .
RUN pip install -r requirements.txt

COPY apps/auth/app ./app
COPY libs ./libs

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8000"]
