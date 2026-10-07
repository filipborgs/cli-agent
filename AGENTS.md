# Agent Instructions

Leia este arquivo antes de editar. `apps/web` consome a API somente por HTTP; a API nunca depende do web.

- Siga as instrucoes locais em `apps/web/AGENTS.md` ou `apps/api/AGENTS.md`.
- Nao edite manualmente `pnpm-lock.yaml` ou `apps/api/uv.lock`; regenere-os pela ferramenta correspondente.
- Escreva ou atualize testes antes de mudar comportamento.
- Execute `make check`, `make test`, `make build` e `make smoke` antes de concluir trabalho transversal.
- Crie commits pequenos: cada commit deve conter um unico objetivo testavel e revisavel. Nao agrupe entregas independentes.
