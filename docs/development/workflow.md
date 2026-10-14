# Development Workflow

1. Escreva o teste que demonstra o comportamento e confirme a falha.
2. Implemente o minimo para torna-lo verde.
3. Rode verificacoes do escopo; antes de integrar, rode `make check`, `make test`, `make build` e `make smoke`.
4. Atualize lockfiles somente por `corepack pnpm install` ou `uv lock`.
5. Documente toda entrega e atualize as referencias afetadas antes de concluir a tarefa.
6. Mantenha um objetivo testavel por commit.

Quando o remote GitHub existir, configure a protecao de `main` para exigir os checks `web`, `api` e `containers`. Essa configuracao e operacional e deve ser aplicada no GitHub; ela nao e representada apenas pelos arquivos do repositorio.

## Documentação como parte da entrega

Toda entrega inclui documentação proporcional ao que mudou, no mesmo objetivo
revisável do código. Consulte o [índice para agentes](../agents/README.md) e
atualize a fonte canônica pertinente:

| Mudança | Documentação |
| --- | --- |
| Regra, conceito ou fluxo | `docs/business`, preservando os IDs RN e exemplos válidos |
| Tabela, campo, estado, relacionamento ou integridade | `docs/database/schema.md` e diagramas afetados |
| Serviço, módulo, interface ou transação | `docs/architecture/clinic-domain-modules.md` e contexto do agente |
| Comando, configuração, migração ou operação | `docs/database/operations.md`, README da aplicação e este workflow |
| Decisão arquitetural relevante | ADR em `docs/decisions`, ligado à entrega |

Regras ficam no documento funcional; campos e constraints no dicionário; sequência
de entrega no plano. Evite definições repetidas que possam divergir. Novas fontes
devem ter título claro, estado de implementação, proprietário/responsabilidade,
contratos e links para regra, código, migração e teste quando aplicáveis.

### Critério documental de conclusão

- Todo comportamento entregue aponta para uma regra/contrato e sua evidência de teste.
- Alteração de banco identifica migração, módulo, integridade e regras RN afetadas.
- Comandos documentados correspondem ao que existe e têm resultado esperado.
- Índices para agentes permanecem curtos, com leitura por assunto e IDs estáveis.
- Exemplos, diagramas e links locais continuam consistentes.
- O estado distingue aprovado/planejado de implementado/verificado; não antecipar entrega.

Documentação pura exige revisão de conteúdo, referências e `git diff --check`;
os testes de comportamento e checks transversais são exigidos quando a entrega
alterar código/infraestrutura. Se a implementação já valida schema por testes,
usar essa evidência para conferir o dicionário, sem recriar o algoritmo no texto.
