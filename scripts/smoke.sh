#!/usr/bin/env bash

set -euo pipefail

project_name="cli-agent-smoke-$$"
port="${WEB_PORT:-8080}"

cleanup() {
  docker compose --project-name "$project_name" down --volumes --remove-orphans
}

trap cleanup EXIT

docker compose --project-name "$project_name" up --build --wait --wait-timeout 120

curl --fail --silent "http://localhost:${port}/" | grep -q "Clinic"
test "$(curl --fail --silent "http://localhost:${port}/api/health")" = '{"status":"ok"}'
test "$(curl --silent --output /dev/null --write-out '%{http_code}' "http://localhost:${port}/api/missing")" = "404"
