#!/usr/bin/env bash
set -euo pipefail
cd /mnt/c/Users/someb/Desktop/printverse
echo '=== compose ps ==='
docker compose ps
echo '=== postgres ==='
docker exec printverse-postgres-1 psql -U printverse -d printverse -tAc "select 'users='||count(*) from users"
docker exec printverse-postgres-1 psql -U printverse -d printverse -tAc "select 'image3d_jobs='||count(*) from image3d_jobs"
echo '=== web ==='
curl -sS -o /dev/null -w 'web=%{http_code}\n' http://127.0.0.1:8080/
curl -sS -o /dev/null -w 'health=%{http_code}\n' http://127.0.0.1:8080/api/health
echo '=== worker logs ==='
docker compose logs --tail=8 worker
