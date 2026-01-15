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

# Allow ec2-user to use docker without sudo (optional but helps debugging)
usermod -aG docker ec2-user || true
chmod 666 /var/run/docker.sock || true

sleep 5
docker network create sibu-net || true

DATA_IP="$(hostname -I | awk '{print $1}')"
echo "DATA_IP=$DATA_IP"

# -----------------------------
# Postgres
# -----------------------------
docker pull postgres:16
docker rm -f sibu-postgres || true
docker volume create pgdata || true

docker run -d --name sibu-postgres --restart always \
  --network sibu-net \
  -p 5432:5432 \
  -e POSTGRES_USER=sibu \
  -e POSTGRES_PASSWORD=sibu \
  -e POSTGRES_DB=sibu \
  -v pgdata:/var/lib/postgresql/data \
  postgres:16

# Wait Postgres
for i in {1..90}; do
  if docker exec sibu-postgres pg_isready -U sibu -d sibu >/dev/null 2>&1; then
    echo "Postgres ready"
    break
  fi
  echo "Postgres not ready yet ($i)..."
  sleep 2
done

# -----------------------------
# Zookeeper
# -----------------------------
docker pull confluentinc/cp-zookeeper:7.6.1
docker rm -f sibu-zookeeper || true

docker run -d --name sibu-zookeeper --restart always \
  --network sibu-net \
  -p 2181:2181 \
  -e ZOOKEEPER_CLIENT_PORT=2181 \
  -e ZOOKEEPER_TICK_TIME=2000 \
  confluentinc/cp-zookeeper:7.6.1

# Wait ZK
for i in {1..60}; do
  if nc -z 127.0.0.1 2181 >/dev/null 2>&1; then
    echo "Zookeeper ready"
    break
  fi
  echo "Zookeeper not ready yet ($i)..."
  sleep 2
done

# -----------------------------
# Kafka (EXTERNAL ONLY)
# IMPORTANT: We advertise ONLY the DATA private IP to avoid clients receiving "kafka:9092".
# -----------------------------
docker pull confluentinc/cp-kafka:7.6.1
docker rm -f kafka || true

docker run -d --name kafka --restart always \
  --network sibu-net \
  -p 29092:29092 \
  -e KAFKA_BROKER_ID=1 \
  -e KAFKA_ZOOKEEPER_CONNECT="sibu-zookeeper:2181" \
  -e KAFKA_LISTENERS="PLAINTEXT://0.0.0.0:29092" \
  -e KAFKA_ADVERTISED_LISTENERS="PLAINTEXT://$DATA_IP:29092" \
  -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP="PLAINTEXT:PLAINTEXT" \
  -e KAFKA_INTER_BROKER_LISTENER_NAME="PLAINTEXT" \
  -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
  -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
  -e KAFKA_AUTO_CREATE_TOPICS_ENABLE=false \
  -e KAFKA_LOG_CLEANER_ENABLE=false \
  -e KAFKA_HEAP_OPTS="-Xms384m -Xmx384m" \
  --memory="900m" --memory-swap="1400m" \
  confluentinc/cp-kafka:7.6.1

# Wait Kafka port
for i in {1..90}; do
  if nc -z 127.0.0.1 29092 >/dev/null 2>&1; then
    echo "Kafka port open"
    break
  fi
  echo "Kafka not ready yet ($i)..."
  sleep 2
done

# Wait metadata ready (avoid GroupCoordinatorNotAvailable at boot)
for i in {1..90}; do
  if docker exec kafka kafka-topics --bootstrap-server 127.0.0.1:29092 --list >/dev/null 2>&1; then
    echo "Kafka metadata ready"
    break
  fi
  echo "Kafka metadata not ready yet ($i)..."
  sleep 2
done

# Create required topics
docker exec kafka kafka-topics --bootstrap-server 127.0.0.1:29092 \
  --create --if-not-exists --topic sibu.user.events --partitions 1 --replication-factor 1 || true

docker exec kafka kafka-topics --bootstrap-server 127.0.0.1:29092 --list || true
