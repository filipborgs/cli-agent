# Entrada para agentes de IA

Leia primeiro [AGENTS.md](../../AGENTS.md) e as instruções da aplicação que será
alterada: [API](../../apps/api/AGENTS.md) ou [web](../../apps/web/AGENTS.md).
Depois use a tabela para ler somente as referências pertinentes à tarefa.

## Estado e autoridade

- Implementado: fundação React/FastAPI, health HTTP, containers e CI.
- Aprovado: regras de negócio, desenho conceitual do banco e diagramas.
- Planejado: PostgreSQL, schema físico, modelos e serviços de agenda/reposição.
- Execução escolhida: subagentes com revisão independente por task, conforme
  o [handoff do plano](../superpowers/plans/2026-10-09-clinic-database.md#handoff).

O código e as migrations comprovam o que está entregue; specs definem o alvo.
Não declarar uma funcionalidade implementada apenas porque está documentada.
Decisões novas do usuário prevalecem e precisam ser refletidas nas referências.

## Leitura por assunto

| Tarefa | Ler |
| --- | --- |
| Entender produto e conceitos | [Negócio](../business/README.md) |
| Alterar comportamento | [Regras RN](../business/business-rules.md) e [fluxos](../business/workflows.md) afetados |
| Persistência, schema e migração | [Contexto do banco](database-context.md), [dicionário](../database/schema.md) e a task correspondente do plano |
| Organização de classes e serviços | [Mapa de módulos](../architecture/clinic-domain-modules.md) |
| Relações e reposição | [Diagramas](../architecture/clinic-database-diagrams.md) e RN-021 a RN-026 |
| Configuração e operação | [Operação do banco](../database/operations.md), [workflow](../development/workflow.md), Makefile e Compose atuais |
| Limites arquiteturais | [Arquitetura](../architecture/system-overview.md) e [ADRs](../decisions/0001-lightweight-polyglot-monorepo.md) |

## Critério de entrega

1. Identificar os IDs RN, módulo proprietário e referências afetadas.
2. Ler a task completa e suas interfaces antes de editar.
3. Para comportamento, escrever o teste e confirmar a falha antes da implementação.
4. Atualizar documentação funcional/técnica/operacional na mesma entrega.
5. Verificar o escopo e, para mudanças transversais, todos os comandos exigidos
   pelo `AGENTS.md`; relatar evidência e eventuais bloqueios.
6. Registrar o que foi implementado e o que continua planejado.
7. Pedir autorização explícita para cada commit e cada push.

Manter este índice curto. Detalhes e exemplos ficam na fonte canônica; novos
contextos específicos devem apontar para ela em vez de copiar documentos inteiros.
