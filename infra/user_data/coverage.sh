#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker git nmap-ncat curl

# -----------------------------
# Swap (prevents OOM lockups)
# -----------------------------
if ! swapon --show | grep -q "^/swapfile"; then
  (fallocate -l 1G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=1024) >/dev/null 2>&1 || true
  chmod 600 /swapfile || true
  mkswap /swapfile >/dev/null 2>&1 || true
  swapon /swapfile || true
  grep -q "^/swapfile " /etc/fstab 2>/dev/null || echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
fi

groupadd -f docker || true
systemctl enable --now docker
usermod -aG docker ec2-user || true
chmod 666 /var/run/docker.sock || true
sleep 3

docker network create sibu-net || true

# =============================
# Terraform vars -> Bash vars
# =============================
DATA_IP="<DATA_IP>"
HOST_PORT="8010"
CONTAINER_PORT="8010"

# =============================
# Wait for DATA dependencies
# =============================
echo "Waiting for Postgres at $DATA_IP:5432 ..."
for i in {1..90}; do
  nc -z "$DATA_IP" 5432 && break
  sleep 2
done

echo "Waiting for Kafka at $DATA_IP:29092 ..."
for i in {1..90}; do
  nc -z "$DATA_IP" 29092 && break
  sleep 2
done

echo "Waiting for RabbitMQ at $DATA_IP:5672 ..."
for i in {1..90}; do
  nc -z "$DATA_IP" 5672 && break
  sleep 2
done

echo "Waiting for Redis at $DATA_IP:6379 ..."
for i in {1..90}; do
  nc -z "$DATA_IP" 6379 && break
  sleep 2
done

sleep 3

# =============================
# Common envs (robustos)
# =============================
DB_HOST="$DATA_IP"
DB_PORT="5432"
DB_USER="sibu"
DB_PASSWORD="sibu"
DB_NAME="sibu"

DATABASE_URL="postgresql+asyncpg://$DB_USER:$DB_PASSWORD@$DATA_IP:$DB_PORT/$DB_NAME"
POSTGRES_DSN="$DATABASE_URL"
POSTGRES_HOST="$DATA_IP"
POSTGRES_PORT="$DB_PORT"
POSTGRES_USER="$DB_USER"
POSTGRES_PASSWORD="$DB_PASSWORD"
POSTGRES_DB="$DB_NAME"

KAFKA_BOOTSTRAP_SERVERS="$DATA_IP:29092"
KAFKA_BOOTSTRAP="$DATA_IP:29092"
KAFKA_BROKER="$DATA_IP:29092"
KAFKA_URL="$DATA_IP:29092"

RABBITMQ_URL="amqp://guest:guest@$DATA_IP:5672/"
AMQP_URL="$RABBITMQ_URL"

REDIS_URL="redis://$DATA_IP:6379/0"
CACHE_REDIS_URL="$REDIS_URL"

# 🔐 JWT (misma clave que auth para que no salga 'Token inválido')
JWT_SECRET="SIBU_SUPER_SECRET_CAMBIAME"
JWT_ALGORITHM="HS256"

docker pull jccasav/sibu-coverage:qa
docker rm -f sibu-coverage || true

docker run -d \
  --name sibu-coverage \
  --restart always \
  -p "$HOST_PORT:$CONTAINER_PORT" \
  --network sibu-net \
  --add-host "postgres:$DATA_IP" \
  --add-host "db:$DATA_IP" \
  --add-host "sibu-postgres:$DATA_IP" \
  --add-host "redis:$DATA_IP" \
  --add-host "rabbit:$DATA_IP" \
  --add-host "rabbitmq:$DATA_IP" \
  --add-host "sibu-rabbit:$DATA_IP" \
  --add-host "kafka:$DATA_IP" \
  --add-host "zookeeper:$DATA_IP" \
  -e "DB_HOST=$DB_HOST" \
  -e "DB_PORT=$DB_PORT" \
  -e "DB_USER=$DB_USER" \
  -e "DB_PASSWORD=$DB_PASSWORD" \
  -e "DB_NAME=$DB_NAME" \
  -e "DATABASE_URL=$DATABASE_URL" \
  -e "POSTGRES_DSN=$POSTGRES_DSN" \
  -e "POSTGRES_HOST=$POSTGRES_HOST" \
  -e "POSTGRES_PORT=$POSTGRES_PORT" \
  -e "POSTGRES_USER=$POSTGRES_USER" \
  -e "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" \
  -e "POSTGRES_DB=$POSTGRES_DB" \
  -e "KAFKA_BOOTSTRAP_SERVERS=$KAFKA_BOOTSTRAP_SERVERS" \
  -e "KAFKA_BOOTSTRAP=$KAFKA_BOOTSTRAP" \
  -e "KAFKA_BROKER=$KAFKA_BROKER" \
  -e "KAFKA_URL=$KAFKA_URL" \
  -e "RABBITMQ_URL=$RABBITMQ_URL" \
  -e "AMQP_URL=$AMQP_URL" \
  -e "REDIS_URL=$REDIS_URL" \
  -e "CACHE_REDIS_URL=$CACHE_REDIS_URL" \
  -e "JWT_SECRET=$JWT_SECRET" \
  -e "JWT_ALGORITHM=$JWT_ALGORITHM" \
  -e "SERVICE_NAME=coverage" \
  jccasav/sibu-coverage:qa

sleep 3
curl -sS -i "http://127.0.0.1:$HOST_PORT/health" || true
curl -sS -i "http://127.0.0.1:$HOST_PORT/docs" || true
