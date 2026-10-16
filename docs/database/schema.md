# Dicionário físico do banco

Status: `tenants`, `users` e `user_tenants` implementadas pela migração
`0001_identity`; demais tabelas e modelos ORM continuam planejados. A origem é o
[desenho conceitual aprovado](../superpowers/specs/2026-10-09-clinic-database-design.md).

Esta é a referência canônica dos nomes e restrições físicos da persistência.
Após implementar cada migração, acrescentar aqui a identificação da migração,
o módulo proprietário, regras RN e testes de evidência das tabelas entregues.

## Convenções

- IDs UUID gerados pela aplicação com `uuid4()`; não dependem de extensão.
- `tenant_id UUID NOT NULL` em tabelas de negócio, exceto `tenants` e `users`.
- Tabelas referenciáveis têm `PRIMARY KEY(id)` e `UNIQUE(tenant_id, id)`.
- Toda FK de negócio inclui `tenant_id`; referências à clínica incluem o tenant.
- Autores de eventos/decisões referenciam `(tenant_id, user_id)` em `user_tenants`,
  preservando a participação histórica mesmo se o acesso for inativado.
- Associação sem identidade própria usa PK composta por tenant e seus dois IDs.
- `created_at`/`updated_at TIMESTAMPTZ` nas entidades mutáveis; eventos históricos
  têm `recorded_at TIMESTAMPTZ`. Timestamps de alteração são atualizados no serviço.
- `active BOOLEAN NOT NULL DEFAULT true` nos cadastros; histórico não usa cascade delete.
- Durações e frequência são inteiros positivos; duração em minutos.
- Vigência é `valid_from DATE NOT NULL`, `valid_until DATE NULL`, final inclusivo.
  Para exclusão de sobreposição, converter para `daterange` semiaberto equivalente.
- Janelas semanais: `weekday SMALLINT` de 0 (segunda) a 6 (domingo),
  `start_time TIME`, `end_time TIME`, início menor que fim. Janelas atravessando
  meia-noite são divididas em dois dias.
- Instantes concretos usam `starts_at`/`ends_at TIMESTAMPTZ` e intervalos `[)`.
- Estados são `TEXT` com `CHECK`, para permitir evolução por migração explícita.
- Referências a registros inativos continuam válidas historicamente; atividade,
  vigência e habilitação são verificadas para novos agendamentos.

## Tabelas e campos específicos

Os campos comuns acima são implícitos. Toda referência abaixo é uma FK.
A lista contém 26 tabelas; cada uma será detalhada e verificada na sua entrega.

| Tabela | Campos/associações específicos |
| --- | --- |
| `tenants` | `id`, `name`, `active` |
| `users` | `id`, `name`, `active`; sem senha nesta entrega |
| `user_tenants` | `user_id`, `tenant_id`, `role='admin'`, `active` |
| `clinics` | `name`, `timezone`, `default_duration_minutes` |
| `patients`, `therapists` | `name` |
| `specialties` | `name`, `normalized_name`; normalizado único por tenant |
| `patient_clinics` | `patient_id`, `clinic_id`, `active` |
| `therapist_clinics` | `therapist_id`, `clinic_id`, `active` |
| `therapist_specialties` | `therapist_id`, `specialty_id`, `active` |
| `rooms` | `clinic_id`, `name`, `normalized_name`; normalizado único por clínica |
| `room_specialties` | `room_id`, `specialty_id`, `active` |
| `treatment_plans` | `patient_id`, `therapist_id`, `specialty_id`, `sessions_per_week`, `duration_minutes NULL`, vigência |
| `treatment_plan_clinics` | `treatment_plan_id`, `clinic_id`, `active` |
| `patient_availabilities` | `patient_id`, `clinic_id`, janela semanal, vigência |
| `therapist_availabilities` | `therapist_id`, `clinic_id`, janela semanal, vigência |
| `clinic_hours` | `clinic_id`, janela semanal, vigência |
| `weekly_slots` | `treatment_plan_id`, `clinic_id`, `room_id`, `weekday`, `start_time`, `duration_minutes`, vigência |
| `clinic_closures` | `clinic_id`, intervalo concreto, `reason`, `created_by` |
| `person_blocks` | `patient_id NULL`, `therapist_id NULL`, intervalo concreto, `reason`, `created_by`; exatamente uma pessoa |
| `monthly_agendas` | `clinic_id`, `month DATE` sempre dia 1; único por tenant/clínica/mês |
| `generation_runs` | `monthly_agenda_id`, `started_at`, `completed_at NULL`, `status`, `parameters JSONB` |
| `appointments` | `treatment_plan_id`, `clinic_id`, `room_id`, `patient_id`, `therapist_id`, `specialty_id`, intervalo concreto, `duration_minutes`, `origin`, `status`, `weekly_slot_id NULL`, `occurrence_date NULL`, `replacement_due_id NULL`, `manually_adjusted`, `replacement_decision` |
| `appointment_events` | `appointment_id`, `actor_id NULL`, `recorded_at`, `kind`, `reason`, `before JSONB`, `after JSONB` |
| `generation_deficits` | `generation_run_id`, `treatment_plan_id`, `week_start DATE`, `missing_count`, `reason_code`, `details JSONB` |
| `replacement_dues` | `original_appointment_id`, `treatment_plan_id`, `reason`, `status`, `decided_by NULL`, `decided_at NULL`, `closed_reason NULL` |

## Identidade entregue — `0001_identity`

Definição física: infraestrutura de persistência da API, em
[`0001_identity.py`](../../apps/api/migrations/versions/0001_identity.py).
Os modelos de identidade e o registro ORM ainda não existem; a `Base.metadata`
compartilhada existe, mas ainda não contém entidades.

| Tabela | Colunas (tipo PostgreSQL, todas NOT NULL) |
| --- | --- |
| `tenants`, `users` | `id UUID` sem default SQL; `name TEXT`; `active BOOLEAN DEFAULT true`; `created_at TIMESTAMPTZ DEFAULT now()`; `updated_at TIMESTAMPTZ DEFAULT now()` |
| `user_tenants` | `tenant_id UUID`; `user_id UUID`; `role TEXT DEFAULT 'admin'`; `active BOOLEAN DEFAULT true`; `created_at TIMESTAMPTZ DEFAULT now()`; `updated_at TIMESTAMPTZ DEFAULT now()` |

- PKs/índices: `pk_tenants(id)`, `pk_users(id)` e
  `pk_user_tenants(tenant_id, user_id)`. A PK composta também atende às futuras
  referências de autores por `(tenant_id, user_id)`; não há índices adicionais.
- FKs: `fk_user_tenants_tenant_id` → `tenants(id)` e
  `fk_user_tenants_user_id` → `users(id)`, ambas com `NO ACTION`, sem cascade.
- `ck_user_tenants_admin_role`: `role = 'admin'` (RN-003).
- IDs são fornecidos pela aplicação. `updated_at` não possui trigger; futuras
  alterações de serviço devem atualizá-lo explicitamente.
- `btree_gist` é instalado para as exclusões futuras; não há exclusões nesta revisão.
- Todas as três tabelas pertencem a `clinic_migrator`, têm RLS habilitada e
  forçada, **sem políticas permissivas**. O runtime possui grants de DML, mas
  não vê/altera linhas e não consegue inserir. Isso é a fundação fail-closed de
   RN-001/RN-003. A autorização por tenant ainda não está implementada.
- `alembic_version` é bookkeeping, sem acesso runtime. Downgrade para `base`
  remove as três tabelas e `btree_gist`; não remove os papéis/esquema bootstrap.
- Evidência: [`test_database.py`](../../apps/api/tests/test_database.py), incluindo
  upgrade/downgrade/upgrade, separação de credenciais e negação real de DML runtime.

## Estados e categorias

| Campo/conceito | Valores |
| --- | --- |
| Origem da sessão | `routine`, `replacement` |
| Estado da sessão | `scheduled`, `completed`, `cancelled`, `patient_absent`, `therapist_absent`, `dispensed` |
| Decisão de reposição | `not_applicable`, `awaiting_decision`, `granted`, `denied` |
| Estado da dívida | `pending`, `scheduled`, `completed`, `closed` |
| Execução de geração | `running`, `completed`, `partial`, `failed` |
| Motivo de déficit | `no_common_availability`, `no_compatible_room`, `resource_conflict` |

Os IDs duplicados em `appointments` permitem exclusões por recurso; uma FK
composta para o plano garante que paciente, terapeuta e especialidade correspondam
ao vínculo. Uma FK composta `(tenant_id, clinic_id, room_id)` garante a unidade
da sala. Uma tentativa também referencia dívida do mesmo vínculo.

## Constraints obrigatórias

- `btree_gist`; exclusão de vigências sobrepostas por combinação
  paciente–terapeuta–especialidade em `treatment_plans` (RN-005).
- Exclusões de intervalos para `appointments` por `(tenant_id, patient_id)`,
  `(tenant_id, therapist_id)` e `(tenant_id, room_id)` (RN-012).
- Reservam recursos apenas `scheduled` e `completed`. Faltas, cancelamentos e
  dispensas preservam histórico sem impedir reutilização do horário (RN-016).
- Unicidade `(tenant_id, weekly_slot_id, occurrence_date)` quando há rotina de
  origem, independentemente do novo horário ou estado da sessão (RN-014).
- Uma dívida por sessão original; índice único parcial de tentativa `scheduled`
  e outro de tentativa `completed` por dívida (RN-024).
- Tentativa tem `replacement_due_id`; rotina não tem. Ocorrência de rotina possui
  `weekly_slot_id` e `occurrence_date`. Uma tentativa não cria nova dívida.
- `replacement_dues` só referencia sessão original de rotina, validado por trigger.
- Triggers de integridade para especialidade do terapeuta, clínica habilitada e
  sala compatível em novos agendamentos; não revalidar atividade de todo o histórico
  quando um cadastro for inativado (RN-002, RN-004, RN-026).
- Operações de serviço bloqueiam registros do plano, participantes, sala e dívida
  em ordem determinística; mudanças nas respectivas habilitações usam os mesmos
  locks. Exclusões e índices únicos são a defesa final contra concorrência.
- RLS e FKs compostas isolam organizações; a identidade autorizada determina
  o contexto por transação. O papel runtime não possui BYPASSRLS (RN-001, RN-003).

## Critério de atualização

O detalhamento final por tabela deve informar: tipo e nulabilidade de cada
coluna, valor padrão, chaves, índices, checks, exclusões, políticas RLS,
migração e arquivo proprietário, regras RN, testes e estado de implementação.
Conferir com `Base.metadata` e migrations; não inferir entrega pela presença
do nome neste dicionário planejado.
