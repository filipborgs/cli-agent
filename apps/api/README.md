# API

```bash
uv sync --project apps/api --all-groups
uv run --project apps/api uvicorn clinic_api.main:app --reload
```

O endpoint de saude e `GET /api/health`. Use `uv run --project apps/api pytest -W error -v` para testar.
