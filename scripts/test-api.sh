#!/usr/bin/env bash
set -euo pipefail

root="$(dirname "$(dirname "$(realpath "${BASH_SOURCE[0]}")")")"
project_name="clinic-test-$$-${RANDOM}"
compose=(docker compose --project-name "$project_name" -f "$root/compose.test.yaml")
cleanup() {
  "${compose[@]}" down --volumes --remove-orphans
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

"${compose[@]}" up --wait --wait-timeout 120
container_id="$("${compose[@]}" ps -q db)"
export POSTGRES_DB=clinic_test
export POSTGRES_USER=postgres
export MIGRATOR_PASSWORD=disposable_migrator_password
export RUNTIME_PASSWORD=disposable_runtime_password
bash "$root/scripts/bootstrap-db.sh" "$container_id"
address="$("${compose[@]}" port db 5432)"
export DATABASE_URL="postgresql+psycopg://clinic_runtime:$RUNTIME_PASSWORD@$address/$POSTGRES_DB"
export MIGRATION_DATABASE_URL="postgresql+psycopg://clinic_migrator:$MIGRATOR_PASSWORD@$address/$POSTGRES_DB"

if (( $# == 0 )); then
  set -- "$root/apps/api/tests"
fi
uv run --project "$root/apps/api" pytest -W error -v "$@"
