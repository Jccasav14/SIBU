FROM python:3.12-slim
WORKDIR /app

COPY apps/reports/requirements.txt .
RUN pip install -r requirements.txt

COPY apps/reports/app ./app
COPY libs ./libs

EXPOSE 8007
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8007"]
