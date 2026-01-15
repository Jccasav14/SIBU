#!/bin/bash
set -eux
dnf update -y
dnf install -y docker git
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

systemctl enable docker
systemctl start docker
usermod -aG docker ec2-user
sleep 10
docker network create sibu-net || true

docker pull jccasav/sibu-audit_log:qa
docker run -d --name sibu-audit --restart always   -p 8006:8006 --network sibu-net jccasav/sibu-audit_log:qa
