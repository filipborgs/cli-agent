# Entrada para agentes de IA

Leia primeiro [AGENTS.md](../../AGENTS.md) e as instruções da aplicação que será
alterada: [API](../../apps/api/AGENTS.md) ou [web](../../apps/web/AGENTS.md).
Depois use a tabela para ler somente as referências pertinentes à tarefa.

## Escopo e fontes

A aplicação usa React/FastAPI, containers e CI. A persistência oferece
PostgreSQL 18, Alembic até `0010_monthly_agenda_schema`, 26 tabelas e modelos
SQLAlchemy, FKs compostas, RLS administrativa e exclusões de reservas.
Os testes usam banco descartável. Autenticação, serviços clínicos, geração de
agenda e integração persistente no startup continuam planejados.

Código e migrations descrevem o comportamento disponível; regras de negócio e
desenho conceitual definem os contratos do produto. O dicionário e o mapa de
módulos identificam explicitamente os elementos ainda propostos.
Decisões novas do usuário devem ser refletidas nas referências pertinentes.

## Leitura por assunto

| Assunto | Ler |
| --- | --- |
| Entender produto e conceitos | [Negócio](../business/README.md) |
| Alterar comportamento | [Regras RN](../business/business-rules.md) e [fluxos](../business/workflows.md) afetados |
| Persistência, schema e migração | [Contexto do banco](database-context.md), [dicionário](../database/schema.md) e migrations correspondentes |
| Organização de classes e serviços | [Mapa de módulos](../architecture/clinic-domain-modules.md) |
| Relações e reposição | [Diagramas](../architecture/clinic-database-diagrams.md), [ER físico](../architecture/clinic-database-er.md) e RN-021 a RN-026 |
| Configuração e operação | [Operação do banco](../database/operations.md), [workflow](../development/workflow.md), Makefile e Compose atuais |
| Limites arquiteturais | [Arquitetura](../architecture/system-overview.md) e [ADRs](../decisions/0001-lightweight-polyglot-monorepo.md) |

## Critério de entrega

1. Identificar os IDs RN, módulo proprietário e referências afetadas.
2. Ler os contratos, interfaces e restrições do assunto antes de editar.
3. Para comportamento, escrever o teste e confirmar a falha antes da implementação.
4. Atualizar documentação funcional/técnica/operacional na mesma entrega.
5. Verificar o escopo e, para mudanças transversais, todos os comandos exigidos
   pelo `AGENTS.md`; relatar evidência e eventuais bloqueios.
6. Registrar o que foi implementado e o que continua planejado.
7. Pedir autorização explícita para cada commit e cada push.

Manter este índice curto. Detalhes e exemplos ficam na fonte canônica; novos
contextos específicos devem apontar para ela em vez de copiar documentos inteiros.
Não incluir identificadores de trabalho, histórico de execução ou acompanhamento
de progresso nas referências do projeto.
