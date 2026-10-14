# Módulos de persistência e negócio da clínica

Status: estrutura planejada a pedido do responsável pelo projeto. Os pacotes
abaixo ainda serão criados nas tasks do
[plano de implementação](../superpowers/plans/2026-10-09-clinic-database.md).

## Limites por domínio

| Domínio | Modelos em `db/models/` | Serviços/tipos em `domain/` | Responsabilidade |
| --- | --- | --- | --- |
| Identidade e organização | `identity/organization.py`, `access.py` | `identity/context.py` | Tenant, clínica, usuário e contexto autorizado. |
| Cadastros | `catalog/people.py`, `affiliations.py`, `specialties.py`, `facilities.py` | `catalog/clinics.py`, `people.py`, `rooms.py`, `affiliations.py`, `specialties.py`, `lifecycle.py` | Pessoas, unidades, salas e habilitações. |
| Planejamento | `planning/treatment.py`, `availability.py`, `weekly.py` | `planning/treatments.py`, `availability.py`, `weekly.py`, `time.py`, `types.py` | Frequência/duração, janelas, vigência e rotina semanal. |
| Calendário | `calendar/closures.py`, `person_blocks.py` | `calendar/closures.py`, `person_blocks.py`, `queries.py` | Fechamentos, indisponibilidades e consulta de impedimentos. |
| Agenda e reposição | `scheduling/appointments.py`, `replacements.py`, `agendas.py` | `scheduling/appointments.py`, `replacements.py`, `replacement_state.py`, `types.py` | Sessões, histórico, direitos e transições da dívida. |
| Geração | Usa planejamento, calendário e agenda | `scheduling/generation/service.py`, `candidates.py`, `diagnostics.py`, `types.py` | Orquestração, candidatos e diagnóstico de capacidade. |

Infraestrutura compartilhada é mínima: `db/base.py`, `db/session.py`,
`db/models/registry.py` e `domain/shared/errors.py`. Tipos de negócio permanecem
no domínio proprietário, sem arquivos globais crescentes de tipos ou serviços.

## Regras de dependência

- `db/models` descreve dados e integridade; não importa serviços de negócio.
- Todos os modelos usam a mesma `Base`; registro explícito e idempotente no Alembic.
- Imports de classes usam o módulo proprietário; `__init__.py` não agrega todo o domínio.
- FKs e referências de relacionamentos entre modelos evitam imports circulares;
  usar `TYPE_CHECKING` quando a anotação precisar mencionar outro pacote.
- Serviços recebem sessão de tenant autorizada e não iniciam/confirmam uma
  transação própria escondida. Persistência permanece na API, nunca no web.
- Consultas de calendário não chamam comandos de agenda. Ajustes validam essas
  consultas; comandos de fechamento podem aplicar resultados nas sessões.
- Transições de dívida após uma tentativa ficam em `replacement_state.py`,
  compartilhadas entre operações de sessão e reposição, sem ciclo entre serviços.
- A geração é o orquestrador; busca de candidatos e diagnóstico não gravam sessões.

## Contratos e manutenção

Assinaturas, retornos, estados e testes ficam nas interfaces de cada task do
plano; nomes físicos estão no [dicionário](../database/schema.md); regras
funcionais estão nos [IDs RN](../business/business-rules.md). Esta página é o
mapa de responsabilidade, não outra cópia desses contratos.

Toda nova funcionalidade deve indicar seu domínio e módulo proprietário. Se
um módulo crescer com responsabilidades independentes, subdividi-lo dentro do
pacote e atualizar os imports, registro, testes e esta referência na mesma entrega.
Ao implementar interfaces, registrar aqui suas transações e ligações regra/teste,
mantendo detalhes consultáveis por assunto para agentes e revisores.
