#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

if [ ! -f .env.prod ]; then
  echo "缺少 .env.prod，请先执行：cp .env.prod.example .env.prod"
  exit 1
fi

docker compose --env-file .env.prod -f docker-compose.prod.yml config >/dev/null
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
curl -fsS http://127.0.0.1:${HTTP_PORT:-80}/health || true
echo
