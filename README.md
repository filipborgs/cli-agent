# CLI Agent

Fundacao tecnica para uma aplicacao de clinicas. O produto futuro coordenara atendimentos e agendas de terapeutas e pacientes.

## Escopo atual

SPA React, API FastAPI, containers, qualidade automatizada e CI. Banco, autenticacao e regras clinicas ainda nao estao implementados. O escopo de negocio e o desenho inicial do banco estao documentados e aprovados.

## Documentacao

- [Visao de negocio e escopo do MVP](docs/business/README.md).
- [Regras de negocio](docs/business/business-rules.md).
- [Fluxos operacionais e exemplos](docs/business/workflows.md).
- [Desenho aprovado do banco de dados](docs/superpowers/specs/2026-10-09-clinic-database-design.md).

## Pre-requisitos

- Docker Compose
- Node 24 com Corepack
- Python 3.13 e uv
- Make

## Inicio rapido

```bash
make dev
```

Abra `http://localhost:8080`. O modo de desenvolvimento usa recarga. Para validar as imagens implantaveis, execute `make smoke`.

## Comandos

- `make format`: aplica formatacao.
- `make check`: formatacao, lint e tipos.
- `make test`: testes de API e web.
- `make build`: builds locais e imagens.
- `make smoke`: sobe imagens, valida web e API, e remove o ambiente.

## Estrutura

- `apps/web`: SPA React.
- `apps/api`: API FastAPI.
- `docs/business`: escopo, conceitos, regras e fluxos do negocio.
- `docs/architecture`: visao tecnica.
- `docs/decisions`: ADRs.
- `docs/development`: workflow.

Leia [a arquitetura](docs/architecture/system-overview.md) e [o workflow](docs/development/workflow.md) antes de contribuir.
