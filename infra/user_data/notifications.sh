#!/bin/bash
set -euxo pipefail

dnf update -y
dnf install -y docker nmap-ncat curl

groupadd -f docker || true
systemctl enable --now docker
usermod -aG docker ec2-user || true
chmod 666 /var/run/docker.sock || true
sleep 3

docker network create sibu-net || true

# Terraform vars -> Bash vars
DATA_IP="${data_ip}"
HOST_PORT="${host_port}"
CONTAINER_PORT="${container_port}"

# Wait for DATA dependencies (best-effort)
for i in {1..90}; do nc -z "$DATA_IP" 5432 && break || true; sleep 2; done
for i in {1..90}; do nc -z "$DATA_IP" 6379 && break || true; sleep 2; done
for i in {1..90}; do nc -z "$DATA_IP" 5672 && break || true; sleep 2; done
for i in {1..90}; do nc -z "$DATA_IP" 29092 && break || true; sleep 2; done

# Common envs (covers different services naming)
DATABASE_URL="postgresql+asyncpg://sibu:sibu@$DATA_IP:5432/sibu"
POSTGRES_DSN="$DATABASE_URL"

docker pull jccasav/sibu-notifications:qa
docker rm -f sibu-notifications || true

docker run -d --name sibu-notifications --restart always \
  -p "$HOST_PORT:$CONTAINER_PORT" \
  --add-host postgres:$DATA_IP \
  --add-host db:$DATA_IP \
  --add-host sibu-postgres:$DATA_IP \
  --add-host redis:$DATA_IP \
  --add-host rabbitmq:$DATA_IP \
  --add-host sibu-rabbit:$DATA_IP \
  --add-host kafka:$DATA_IP \
  -e DATABASE_URL="$DATABASE_URL" \
  -e POSTGRES_DSN="$POSTGRES_DSN" \
  -e DB_HOST="$DATA_IP" \
  -e DB_PORT="5432" \
  -e DB_USER="sibu" \
  -e DB_PASSWORD="sibu" \
  -e DB_NAME="sibu" \
  -e JWT_SECRET="SIBU_SUPER_SECRET_CAMBIAME" \
  -e JWT_ALGORITHM="HS256" \
  -e REDIS_URL="redis://$DATA_IP:6379/0" \
  -e RABBITMQ_HOST="$DATA_IP" \
  -e RABBITMQ_PORT="5672" \
  -e AMQP_URL="amqp://guest:guest@$DATA_IP:5672/" \
  -e RABBITMQ_URL="amqp://guest:guest@$DATA_IP:5672/" \
  -e KAFKA_BOOTSTRAP_SERVERS="$DATA_IP:29092" \
  -e KAFKA_BOOTSTRAP="$DATA_IP:29092" \
  -e KAFKA_BROKER="$DATA_IP:29092" \
  -e KAFKA_URL="$DATA_IP:29092" \

  jccasav/sibu-notifications:qa

sleep 3
curl -sS -i "http://127.0.0.1:$HOST_PORT/health" || true
curl -sS -i "http://127.0.0.1:$HOST_PORT/docs" || true
