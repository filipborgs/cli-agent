# API

```bash
uv sync --project apps/api --all-groups
uv run --project apps/api uvicorn clinic_api.main:app --reload
```

O endpoint de saude e `GET /api/health`, com resposta `{"status":"ok"}`. Ele não
abre conexão com o banco nem exige configuração de persistência.

Na raiz do repositório, use `make test-api` para testar com PostgreSQL 18
descartável (requer Docker/Compose). Para filtrar:
`PYTEST_ARGS='apps/api/tests/test_database.py' make test-api`.
O runner exporta `DATABASE_URL` runtime e `MIGRATION_DATABASE_URL` administrativa,
aplica migrations nas fixtures e sempre remove o volume. Pytest direto requer
essas URLs e um banco descartável provisionado; não há skip silencioso.

Persistência entregue: 26 tabelas com modelos ORM, Alembic até `0010_monthly_agenda_schema` e RLS administrativa: identidade e catálogo, planos e disponibilidades, rotina semanal, sessões e eventos, reposições, calendário, estruturas da agenda mensal.
Demais estruturas e serviços clínicos continuam planejados.
Consulte [operação](../../docs/database/operations.md) e o
[dicionário](../../docs/database/schema.md) para contratos e migrações.
