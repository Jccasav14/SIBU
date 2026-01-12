FROM python:3.12-slim
WORKDIR /app

COPY apps/claims/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/claims/app ./app
# Keep consistent with other services in the monorepo (optional shared libs)
COPY libs ./libs

EXPOSE 8009
CMD ["uvicorn", "app.main:app", "--host=0.0.0.0", "--port=8009"]
