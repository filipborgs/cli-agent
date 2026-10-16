# Agent Instructions

Leia este arquivo antes de editar. `apps/web` consome a API somente por HTTP; a API nunca depende do web.

- Siga as instrucoes locais em `apps/web/AGENTS.md` ou `apps/api/AGENTS.md`.
- Use `docs/agents/README.md` como indice e leia as fontes canonicas da tarefa; evite carregar documentacao inteira sem necessidade.
- Documente toda entrega: regras/fluxos, banco, contratos, arquitetura e operacao afetados. Mantenha IDs de regras, links curtos para agentes e a distincao entre planejado e implementado; siga `docs/development/workflow.md`.
- Documentacao de referencia guia humanos e agentes por assunto e contrato, sem referencias a tasks, numeracao de trabalho ou tracking de progresso. Acompanhamento de execucao fica apenas nos planos e registros de trabalho.
- Nao edite manualmente `pnpm-lock.yaml` ou `apps/api/uv.lock`; regenere-os pela ferramenta correspondente.
- Escreva ou atualize testes antes de mudar comportamento.
- Execute `make check`, `make test`, `make build` e `make smoke` antes de concluir trabalho transversal.
- Crie commits pequenos e incrementais: cada commit deve conter um unico objetivo testavel e revisavel, mesmo quando a feature ainda nao terminou. Inclua migracao, modelos, testes e documentacao que formam aquele incremento; nao aguarde a feature inteira nem agrupe entregas independentes.
