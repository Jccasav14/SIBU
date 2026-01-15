#!/bin/bash
set -eux

dnf update -y
dnf install -y docker git nmap-ncat

# -----------------------------
# Swap (prevents OOM lockups on small instances)
# -----------------------------
if ! swapon --show | grep -q "^/swapfile"; then
  (fallocate -l 1G /swapfile || dd if=/dev/zero of=/swapfile bs=1M count=1024) >/dev/null 2>&1 || true
  chmod 600 /swapfile || true
  mkswap /swapfile >/dev/null 2>&1 || true
  swapon /swapfile || true
  grep -q "^/swapfile " /etc/fstab 2>/dev/null || echo "/swapfile swap swap defaults 0 0" >> /etc/fstab
fi

groupadd -f docker || true
systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user || true
chmod 666 /var/run/docker.sock || true
sleep 5

docker network create sibu-net || true

# --- DATA endpoints (DATA instance private IP) ---
DATA_IP="<DATA_PRIVATE_IP>"

DATABASE_URL="postgresql+asyncpg://sibu:sibu@$DATA_IP:5432/sibu"
DB_HOST="$DATA_IP"
DB_PORT="5432"
DB_USER="sibu"
DB_PASSWORD="sibu"
DB_NAME="sibu"

# --- Wait for Postgres ---
echo "Waiting for Postgres at $DATA_IP:5432 ..."
for i in {1..90}; do
  if nc -z "$DATA_IP" 5432 >/dev/null 2>&1; then
    echo "Postgres reachable"
    break
  fi
  echo "Postgres not ready yet ($i)..."
  sleep 2
done

# --- Wait for Kafka metadata ---
echo "Waiting for Kafka at $DATA_IP:29092 ..."
for i in {1..90}; do
  if nc -z "$DATA_IP" 29092 >/dev/null 2>&1; then
    echo "Kafka port reachable"
    break
  fi
  echo "Kafka not ready yet ($i)..."
  sleep 2
done
sleep 10

docker pull jccasav/sibu-cases:qa
docker rm -f sibu-cases || true

docker run -d --name sibu-cases --restart always \
  -p 8002:8003 \
  --network sibu-net \
  --add-host postgres:$DATA_IP \
  --add-host db:$DATA_IP \
  --add-host sibu-postgres:$DATA_IP \
  --add-host kafka:$DATA_IP \
  -e DATABASE_URL="$DATABASE_URL" \
  -e DB_HOST="$DB_HOST" \
  -e DB_PORT="$DB_PORT" \
  -e DB_USER="$DB_USER" \
  -e DB_PASSWORD="$DB_PASSWORD" \
  -e DB_NAME="$DB_NAME" \
  -e KAFKA_BOOTSTRAP_SERVERS="$DATA_IP:29092" \
  -e KAFKA_BOOTSTRAP="$DATA_IP:29092" \
  -e KAFKA_BROKER="$DATA_IP:29092" \
  -e KAFKA_URL="$DATA_IP:29092" \
  jccasav/sibu-cases:qa

# Quick local check
sleep 3
curl -sS http://127.0.0.1:8002/health || true
