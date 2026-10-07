FROM ghcr.io/astral-sh/uv:0.6.3-python3.13-bookworm AS base
WORKDIR /app

FROM base AS development
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --all-groups
CMD ["uv", "run", "uvicorn", "clinic_api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS runtime
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
CMD ["uv", "run", "--no-sync", "uvicorn", "clinic_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
