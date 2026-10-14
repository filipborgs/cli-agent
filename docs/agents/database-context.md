# Contexto para agentes: banco e agenda

## Escopo e estado

Banco ainda não implementado. O [desenho conceitual](../superpowers/specs/2026-10-09-clinic-database-design.md)
está aprovado; o [dicionário físico](../database/schema.md) é o contrato planejado.
As interfaces, paths, testes e sequência estão no
[plano](../superpowers/plans/2026-10-09-clinic-database.md).
Não iniciar implementação só por ler este contexto; seguir a tarefa autorizada.

## Fontes por decisão

| Decisão | Fonte canônica |
| --- | --- |
| Regra funcional | [RN-001 a RN-026](../business/business-rules.md) |
| Exemplo da clínica | [Fluxos](../business/workflows.md) |
| Entidade/cardinalidade | [Desenho](../superpowers/specs/2026-10-09-clinic-database-design.md#4-modelo-de-dados-aprovado) e [diagramas](../architecture/clinic-database-diagrams.md) |
| Nome físico, coluna e constraint | [Schema](../database/schema.md) |
| Dono de módulo e imports | [Mapa](../architecture/clinic-domain-modules.md) |
| Assinatura e teste da entrega | Task correspondente do [plano](../superpowers/plans/2026-10-09-clinic-database.md) |
| Papéis, migrações e comando | [Operação](../database/operations.md), depois conferir arquivos implementados |

## Mapa de risco e evidência planejada

| Tema | Regras | Task / testes planejados |
| --- | --- | --- |
| Tenant e autorização | RN-001, RN-003 | 2 / `test_tenant_isolation.py` |
| Cadastros e salas | RN-002, RN-004 | 3, 6 / `test_catalog.py`, `test_appointments.py` |
| Frequência, duração e disponibilidade | RN-005 a RN-010 | 4, 5 / `test_planning.py`, `test_weekly_slots.py` |
| Ajustes e concorrência | RN-011, RN-012, RN-014 a RN-016 | 6 / `test_appointments.py`, `test_scheduling_concurrency.py` |
| Fechamentos e ausências antecipadas | RN-017 a RN-020 | 8 / `test_calendar.py` |
| Dívida e tentativas | RN-021 a RN-026 | 7, 8 / `test_replacements.py`, `test_calendar.py` |
| Geração parcial e repetição | RN-013, RN-014 | 9 / `test_generation.py` |
| Metadata e deploy | Integridade técnica | 2, 10 / `test_model_registry.py`, `test_migrations.py`, smoke |

Os testes acima são alvos do plano, não arquivos já presentes.

## Invariantes de revisão

- Cadastro de pessoa é por tenant, agenda/sala por clínica. Conflito de pessoa
  atravessa clínicas da mesma organização; referência nunca atravessa tenant.
- Frequência pertence ao vínculo paciente–terapeuta–especialidade e não é
  multiplicada por clínica. Reposição não reduz a rotina da semana do encaixe.
- A ocorrência original é diferente da data atual da sessão: preservar a primeira
  ao mover a segunda. Geração repetida não recria sessões resolvidas/ajustadas.
- Déficit de geração não é dívida de reposição. Tentativa frustrada não é origem
  de outra dívida; reabre ou encerra a dívida existente conforme a regra.
- Feriado conhecido não produz sessão habitual. Fechamento que atinge tentativa
  já marcada preserva o direito anterior sem criar direito novo.
- Fora da disponibilidade só por ajuste manual registrado; conflitos, bloqueios,
  funcionamento e sala compatível continuam obrigatórios.
- Papel runtime não é dono do schema nem possui BYPASSRLS. Contexto é autorizado
  por transação e não pode vazar no pool após erro.
- Todos os modelos usam uma metadata e registro explícito. Serviços fazem flush;
  a transação externa confirma ou desfaz sessão, histórico e dívida juntos.

## Ao concluir uma task

Atualizar a referência afetada e indicar RN, módulo, migração e teste. Conferir
que exemplos e diagramas continuam válidos e que o estado entregue foi atualizado
sem antecipar funcionalidades futuras. Ler a política documental no
[workflow](../development/workflow.md#documentação-como-parte-da-entrega).
