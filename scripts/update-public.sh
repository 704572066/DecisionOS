#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
git pull --ff-only
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
docker image prune -f
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
