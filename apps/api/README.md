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

Fundação entregue: settings, engine síncrono, Base compartilhada, Alembic e
`0001_identity` com RLS fail-closed. ORM, autorização e serviços clínicos ainda
não estão disponíveis. Consulte [operação do banco](../../docs/database/operations.md)
para bootstrap compartilhado, configuração e comandos Alembic.
