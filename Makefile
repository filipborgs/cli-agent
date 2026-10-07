.PHONY: dev format check test build smoke

dev:
	docker compose -f compose.yaml -f compose.dev.yaml up --build

format:
	uv run --project apps/api ruff format apps/api
	corepack pnpm --dir apps/web format

check:
	uv run --project apps/api ruff format --check apps/api
	uv run --project apps/api ruff check apps/api
	uv run --project apps/api mypy apps/api/src
	corepack pnpm --dir apps/web format:check
	corepack pnpm --dir apps/web lint
	corepack pnpm --dir apps/web typecheck

test:
	uv run --project apps/api pytest -W error -v
	corepack pnpm --dir apps/web test

build:
	uv build --project apps/api
	corepack pnpm --dir apps/web build
	docker compose build

smoke:
	bash scripts/smoke.sh
