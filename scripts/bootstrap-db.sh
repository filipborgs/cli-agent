#!/usr/bin/env bash
set -euo pipefail

# Shared bootstrap for a fresh PostgreSQL database. Argument: container ID.
: "${MIGRATOR_PASSWORD:?Set MIGRATOR_PASSWORD}"
: "${RUNTIME_PASSWORD:?Set RUNTIME_PASSWORD}"
docker exec -i "${1:?Pass the PostgreSQL container ID}" psql \
  --username "${POSTGRES_USER:-postgres}" --dbname "${POSTGRES_DB:-clinic}" \
  --set ON_ERROR_STOP=1 \
  --set migrator_password="$MIGRATOR_PASSWORD" \
  --set runtime_password="$RUNTIME_PASSWORD" <<'SQL'
SELECT 'CREATE ROLE clinic_migrator' WHERE NOT EXISTS (
  SELECT FROM pg_roles WHERE rolname = 'clinic_migrator'
) \gexec
SELECT 'CREATE ROLE clinic_runtime' WHERE NOT EXISTS (
  SELECT FROM pg_roles WHERE rolname = 'clinic_runtime'
) \gexec
ALTER ROLE clinic_migrator LOGIN NOSUPERUSER BYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'migrator_password';
ALTER ROLE clinic_runtime LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION PASSWORD :'runtime_password';
SELECT format('GRANT CONNECT, CREATE ON DATABASE %I TO clinic_migrator', current_database()) \gexec
SELECT format('GRANT CONNECT ON DATABASE %I TO clinic_runtime', current_database()) \gexec
ALTER SCHEMA public OWNER TO clinic_migrator;
REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO clinic_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE clinic_migrator IN SCHEMA public
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO clinic_runtime;
ALTER DEFAULT PRIVILEGES FOR ROLE clinic_migrator IN SCHEMA public
  GRANT USAGE, SELECT ON SEQUENCES TO clinic_runtime;
SQL
