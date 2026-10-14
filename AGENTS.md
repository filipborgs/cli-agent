# Agent Instructions

Leia este arquivo antes de editar. `apps/web` consome a API somente por HTTP; a API nunca depende do web.

- Siga as instrucoes locais em `apps/web/AGENTS.md` ou `apps/api/AGENTS.md`.
- Use `docs/agents/README.md` como indice e leia as fontes canonicas da tarefa; evite carregar documentacao inteira sem necessidade.
- Documente toda entrega: regras/fluxos, banco, contratos, arquitetura e operacao afetados. Mantenha IDs de regras, links curtos para agentes e a distincao entre planejado e implementado; siga `docs/development/workflow.md`.
- Nao edite manualmente `pnpm-lock.yaml` ou `apps/api/uv.lock`; regenere-os pela ferramenta correspondente.
- Escreva ou atualize testes antes de mudar comportamento.
- Execute `make check`, `make test`, `make build` e `make smoke` antes de concluir trabalho transversal.
- Crie commits pequenos: cada commit deve conter um unico objetivo testavel e revisavel. Nao agrupe entregas independentes.
