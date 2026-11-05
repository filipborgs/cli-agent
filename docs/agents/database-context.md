# Contexto para agentes: banco e agenda

## Escopo e limites

Persistência disponível: 21 tabelas com modelos ORM, Alembic até `0008_replacement_schema` e RLS administrativa: identidade e catálogo, planos e disponibilidades, rotina semanal, sessões e eventos, reposições.
Consulte o [dicionário](../database/schema.md) para tabelas e migrações
entregues. Demais estruturas e serviços clínicos continuam planejados.

## Fontes por decisão

| Decisão | Fonte canônica |
| --- | --- |
| Regra funcional | [RN-001 a RN-026](../business/business-rules.md) |
| Exemplo da clínica | [Fluxos](../business/workflows.md) |
| Entidade/cardinalidade | [Desenho](../superpowers/specs/2026-10-09-clinic-database-design.md#4-modelo-de-dados-aprovado) e [diagramas](../architecture/clinic-database-diagrams.md) |
| Nome físico, coluna e constraint | [Schema](../database/schema.md) |
| Dono de módulo e imports | [Mapa](../architecture/clinic-domain-modules.md) |
| Interface e limite transacional | [Contratos dos módulos](../architecture/clinic-domain-modules.md#contratos-e-manutenção) e código proprietário |
| Papéis, migrações e comando | [Operação](../database/operations.md), depois conferir arquivos implementados |
| Acesso ao ambiente Python | [Contrato centralizado](../database/operations.md#acesso-centralizado-ao-ambiente-python); importar `EnvironmentVariable` de `clinic_api.environment` e usar `.required()`/`.optional()` em Settings, Alembic e fixtures; conversão tipada para `str`, `int` e `bool`. |

## Mapa de invariantes

| Tema | Regras | Comportamento a verificar |
| --- | --- | --- |
| Tenant e autorização | RN-001, RN-003 | Contexto autorizado e ausência de vazamento entre organizações. |
| Cadastros e salas | RN-002, RN-004 | Participação na unidade e compatibilidade de especialidade. |
| Frequência, duração e disponibilidade | RN-005 a RN-010 | Frequência única por vínculo, janelas vigentes e rotina estável. |
| Ajustes e concorrência | RN-011, RN-012, RN-014 a RN-016 | Sem dupla reserva; identidade da ocorrência e histórico preservados. |
| Fechamentos e ausências antecipadas | RN-017 a RN-020 | Atendimento devido corretamente identificado; feriados não criam sessões. |
| Dívida e tentativas | RN-021 a RN-026 | Mesmo direito/origem ao reagendar; sem pendência filha. |
| Geração parcial e repetição | RN-013, RN-014 | Motivos de déficit e ausência de duplicação. |
| Metadata e deploy | Integridade técnica | Schema, privilégios, migrations e startup coerentes. |

Esses invariantes orientam a implementação do modelo clínico. A persistência é verificada por testes `test_*_schema.py`,
`test_model_registry.py` e `test_database.py`;
usar `make test-api`, conforme
[operação](../database/operations.md). Bootstrap compartilhado:
`scripts/bootstrap-db.sh`; fixtures `admin_engine`, `runtime_engine` e
`factory: ClinicFactory` usam banco descartável, com limpeza pelo migrator.

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

## Manutenção da referência

Atualizar a referência afetada e indicar RN, módulo, migração e teste. Conferir
que exemplos e diagramas continuam válidos e que o estado entregue foi atualizado
sem antecipar funcionalidades futuras. Ler a política documental no
[workflow](../development/workflow.md#documentação-como-parte-da-entrega).
