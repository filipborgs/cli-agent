# Banco de dados da agenda clínica

Status: modelo conceitual aprovado; contrato físico planejado. PostgreSQL,
modelos ORM e migrações ainda não foram implementados.

## Referências canônicas

- [Negócio](../business/README.md) e [regras RN-001 a RN-026](../business/business-rules.md): finalidade e comportamento esperado.
- [Desenho aprovado](../superpowers/specs/2026-10-09-clinic-database-design.md): entidades, relações, integridade e decisões aprovadas.
- [Diagramas](../architecture/clinic-database-diagrams.md): cardinalidades e ciclo da reposição.
- [Dicionário físico planejado](schema.md): nomes de tabelas, campos, estados e constraints.
- [Operação](operations.md): situação atual e procedimentos a documentar na implementação.
- [Módulos de persistência e domínio](../architecture/clinic-domain-modules.md): proprietários das entidades e serviços.
- [Plano de implementação](../superpowers/plans/2026-10-09-clinic-database.md): tarefas, interfaces e testes que entregarão o banco.
- [Contexto para agentes](../agents/database-context.md): navegação por assunto e critérios de revisão.

## Organização dos dados

| Área | Conteúdo |
| --- | --- |
| Organização e acesso | Tenant, clínicas, usuários e participação administrativa. |
| Cadastros | Pacientes, terapeutas, especialidades, salas e habilitações. |
| Planejamento | Vínculos de atendimento, disponibilidade e horários fixos semanais. |
| Calendário | Fechamentos da clínica e bloqueios individuais. |
| Agenda | Sessões, histórico, geração mensal e seus déficits. |
| Reposição | Atendimento original, pendência e sessões de tentativa. |

Paciente e terapeuta são únicos por tenant; sala e agenda pertencem à clínica.
Frequência é do vínculo paciente–terapeuta–especialidade, não de cada unidade.
Rotina semanal, sessão concreta e pendência de reposição são conceitos distintos.

## Invariantes para preservar

- Nunca relacionar dados de organizações diferentes (RN-001).
- Verificar paciente e terapeuta entre todas as clínicas ao impedir reservas
  simultâneas; sala é específica da unidade (RN-012).
- Não transformar déficit de geração em dívida de reposição (RN-013).
- Não recriar a ocorrência original de uma sessão ajustada ou resolvida (RN-014).
- Não criar sessões em fechamento conhecido da clínica (RN-017).
- Manter origem e terapeuta original da reposição, sem dívida filha por nova
  tentativa frustrada (RN-021 a RN-025).
- Preservar histórico e pendências ao encerrar/inativar cadastros (RN-016, RN-026).

## Manutenção da referência

Cada migração deve atualizar o dicionário e os diagramas quando alterar o modelo.
Vincular tabela/constraint à regra RN, módulo proprietário, migração e teste.
Quando uma parte for implementada, registrar sua evidência e seu estado; não
considerar uma tabela existente apenas porque aparece neste planejamento.

O dicionário é a referência física; o desenho é a referência conceitual; o plano
é a sequência de entrega. Evitar três cópias independentes da mesma definição.
