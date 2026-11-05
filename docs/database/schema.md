# Dicionário físico do banco

Status: 26 tabelas de aplicação e modelos ORM implementados; head
Alembic `0010_monthly_agenda_schema`. Serviços clínicos e geração automática continuam planejados.

## Convenções

- IDs UUID fornecidos pelo chamador, sem default SQL. A identidade de pessoas
  é por organização; nomes de pacientes/terapeutas não são chaves únicas.
- Tabelas físicas singulares. Referências clínicas incluem `tenant_id`;
  entidades referenciáveis têm UNIQUE `(tenant_id, id)`.
- Associações usam PK composta. Autores referenciam a participação histórica
  `(tenant_id, user_id)`; FKs usam NO ACTION, sem apagar histórico em cascata.
- `created_at`/`updated_at` têm default `now()`. `updated_at` não tem atualização
  automática: o escritor deve atualizá-lo. Eventos usam `recorded_at`.
- Instantes concretos usam TIMESTAMPTZ e reservas usam intervalos `[)`.
  Janelas recorrentes usam TIME local, dia 0–6 (segunda–domingo) e vigência DATE
  final inclusiva; `daterange(valid_from, valid_until + 1, '[)')` representa
  a mesma vigência para exclusão. Final NULL significa sem limite.
- Duração/frequência são positivas. Nomes normalizados são fornecidos pelo
  escritor após trim/casefold; a unicidade é garantida pelo banco, a
  transformação de texto não é executada pelo schema.
- Estados persistidos usam TEXT com CHECK, detalhado por tabela abaixo.
- RLS e triggers são objetos das migrações, não de `Base.metadata.create_all()`.
  Provisionar sempre com Alembic. O ORM não cria políticas ou funções SQL.

## Segurança e integridade transacional

Todas as tabelas têm RLS ENABLE/FORCE. Runtime possui somente SELECT em `tenant`,
`user` e `user_tenant`, sem DDL, propriedade ou BYPASSRLS. As tabelas de negócio
recebem SELECT/INSERT/UPDATE/DELETE, sujeitos à política `<tabela>_admin`, com
`USING` e `WITH CHECK` em `clinic_has_admin_access(tenant_id)`.

A função é SQL STABLE SECURITY INVOKER, com search_path explícito, EXECUTE
revogado de PUBLIC e concedido a `clinic_runtime`. Ela exige tenant igual a
`app.tenant_id` e uma linha visível em `tenant`. A política `tenant_self` exige
organização ativa, usuário ativo e participação administrativa ativa do
`app.user_id`. `user_self` expõe o próprio usuário; `membership_self` suas
participações. O contexto é local à transação. Autenticar a identidade e
selecionar o contexto autorizado continuam sendo responsabilidades da aplicação.

As revisões `0002_tenant_isolation` e `0004_catalog_integrity` definem as
políticas finais de identidade. A `0003_catalog` criou as seis tabelas iniciais
do catálogo; `0004_catalog_integrity` completa FKs, campos comuns, associações
e políticas. Revisões existentes são preservadas.

A coluna gerada `replacement_due.original_origin` é sempre `routine`. Uma FK
inclui esse discriminador e referencia a identidade da sessão com sua origem;
a sessão não pode se tornar tentativa enquanto for origem de dívida. Essa
proteção declarativa também vale em REPEATABLE READ com snapshot anterior à
criação da dívida. O índice único `uq_appointment_origin_identity` dá suporte
à FK. O escritor não fornece o valor da coluna gerada.

### Triggers

- `appointment_resources` → `validate_appointment_resources()`: em nova reserva
  ou mudança de recursos/intervalo de uma reserva, exige plano/clínica habilitados,
  pessoas e cadastros ativos, participações na clínica e especialidades do
  terapeuta e sala. Obtém locks FOR SHARE nos registros consultados; uma
  inativação concorrente espera a transação da reserva terminar. Não invalida
  histórico ao inativar um cadastro nem revalida recursos numa simples mudança
  entre estados que já reservavam o mesmo intervalo.
- `replacement_origin` → `validate_replacement_origin()`: a origem de uma dívida
  deve ser sessão `routine` do mesmo vínculo; a leitura bloqueia a sessão
  original com FOR SHARE. Contexto runtime sem autorização é negado antes da
  validação de origem.
- `preserve_replacement_origin` → função homônima: impede converter uma sessão
  original referenciada em tentativa de reposição.

Funções de trigger usam PL/pgSQL e search_path explícito. Não sincronizam
estados de dívida/sessão, não criam eventos automaticamente e não consultam
fechamentos/disponibilidade. Essas operações de negócio ainda precisam de
serviços próprios. Exclusões GiST e índices únicos são a defesa final contra
reservas e tentativas concorrentes.

## Evidências

Testes de banco disponíveis: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py), [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py), [`test_weekly_slot_schema.py`](../../apps/api/tests/test_weekly_slot_schema.py), [`test_appointment_schema.py`](../../apps/api/tests/test_appointment_schema.py), [`test_replacement_schema.py`](../../apps/api/tests/test_replacement_schema.py), [`test_calendar_schema.py`](../../apps/api/tests/test_calendar_schema.py), [`test_agenda_schema.py`](../../apps/api/tests/test_agenda_schema.py).
O registro ORM e o round-trip das migrações são verificados pelos testes
existentes de banco. Auditoria transversal adicional permanece planejada.

## Tabelas, colunas e constraints

Tipos abaixo são PostgreSQL. `NULL` indica campo opcional; `—` indica ausência
de default SQL. PKs e constraints sem nome explícito recebem o nome padrão do
PostgreSQL. `alembic_version` é controle da ferramenta e não recebe acesso runtime.

### `appointment`

ORM: [`Appointment`](../../apps/api/src/clinic_api/db/models/scheduling/appointments.py).
Migração: [`0007_appointments`](../../apps/api/migrations/versions/0007_appointments.py) e `0008_replacement_schema`. Regras relacionadas: RN-011, RN-012, RN-014 a RN-016.
Teste: [`test_appointment_schema.py`](../../apps/api/tests/test_appointment_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `treatment_plan_id` | `UUID` | NOT NULL | `—` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `room_id` | `UUID` | NOT NULL | `—` |
| `patient_id` | `UUID` | NOT NULL | `—` |
| `therapist_id` | `UUID` | NOT NULL | `—` |
| `specialty_id` | `UUID` | NOT NULL | `—` |
| `starts_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `ends_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `duration_minutes` | `INTEGER` | NOT NULL | `—` |
| `origin` | `TEXT` | NOT NULL | `—` |
| `status` | `TEXT` | NOT NULL | `'scheduled'` |
| `weekly_slot_id` | `UUID` | NULL | `—` |
| `occurrence_date` | `DATE` | NULL | `—` |
| `manually_adjusted` | `BOOLEAN` | NOT NULL | `false` |
| `replacement_decision` | `TEXT` | NOT NULL | `'not_applicable'` |
| `replacement_due_id` | `UUID` | NULL | `—` |

- `CONSTRAINT ck_appointment_duration CHECK (duration_minutes > 0)`.
- `CONSTRAINT ck_appointment_interval CHECK (starts_at < ends_at)`.
- `CONSTRAINT ck_appointment_origin CHECK (origin IN ('routine', 'replacement'))`.
- `CONSTRAINT ck_appointment_origin_fields CHECK ((origin = 'routine' AND weekly_slot_id IS NOT NULL AND occurrence_date IS NOT NULL AND replacement_due_id IS NULL) OR (origin = 'replacement' AND weekly_slot_id IS NULL AND occurrence_date IS NULL AND replacement_due_id IS NOT NULL))`.
- `CONSTRAINT ck_appointment_replacement_decision CHECK (replacement_decision IN ('not_applicable', 'awaiting_decision', 'granted', 'denied'))`.
- `CONSTRAINT ck_appointment_status CHECK (status IN ('scheduled', 'completed', 'cancelled', 'patient_absent', 'therapist_absent', 'dispensed'))`.
- `CONSTRAINT ex_appointment_patient EXCLUDE USING gist (tenant_id WITH =, patient_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&) WHERE (status IN ('scheduled', 'completed'))`.
- `CONSTRAINT ex_appointment_room EXCLUDE USING gist (tenant_id WITH =, room_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&) WHERE (status IN ('scheduled', 'completed'))`.
- `CONSTRAINT ex_appointment_therapist EXCLUDE USING gist (tenant_id WITH =, therapist_id WITH =, tstzrange(starts_at, ends_at, '[)') WITH &&) WHERE (status IN ('scheduled', 'completed'))`.
- `CONSTRAINT fk_appointment_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_appointment_patient FOREIGN KEY(tenant_id, patient_id) REFERENCES patient (tenant_id, id)`.
- `CONSTRAINT fk_appointment_plan_identity FOREIGN KEY(tenant_id, treatment_plan_id, patient_id, therapist_id, specialty_id) REFERENCES treatment_plan (tenant_id, id, patient_id, therapist_id, specialty_id)`.
- `CONSTRAINT fk_appointment_replacement FOREIGN KEY(tenant_id, replacement_due_id, treatment_plan_id) REFERENCES replacement_due (tenant_id, id, treatment_plan_id)`.
- `CONSTRAINT fk_appointment_room FOREIGN KEY(tenant_id, room_id) REFERENCES room (tenant_id, id)`.
- `CONSTRAINT fk_appointment_room_clinic FOREIGN KEY(tenant_id, clinic_id, room_id) REFERENCES room (tenant_id, clinic_id, id)`.
- `CONSTRAINT fk_appointment_slot_plan FOREIGN KEY(tenant_id, weekly_slot_id, treatment_plan_id) REFERENCES weekly_slot (tenant_id, id, treatment_plan_id)`.
- `CONSTRAINT fk_appointment_specialty FOREIGN KEY(tenant_id, specialty_id) REFERENCES specialty (tenant_id, id)`.
- `CONSTRAINT fk_appointment_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_appointment_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `CONSTRAINT fk_appointment_treatment_plan FOREIGN KEY(tenant_id, treatment_plan_id) REFERENCES treatment_plan (tenant_id, id)`.
- `CONSTRAINT fk_appointment_treatment_plan_clinic FOREIGN KEY(tenant_id, treatment_plan_id, clinic_id) REFERENCES treatment_plan_clinic (tenant_id, treatment_plan_id, clinic_id)`.
- `CONSTRAINT fk_appointment_weekly_slot FOREIGN KEY(tenant_id, weekly_slot_id) REFERENCES weekly_slot (tenant_id, id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_appointment_origin_identity UNIQUE (tenant_id, id, treatment_plan_id, origin)`.
- `CONSTRAINT uq_appointment_tenant_id_id UNIQUE (tenant_id, id)`.
- `CONSTRAINT uq_appointment_tenant_id_id_treatment_plan_id UNIQUE (tenant_id, id, treatment_plan_id)`.
- `CREATE UNIQUE INDEX uq_appointment_due_completed ON appointment (tenant_id, replacement_due_id) WHERE origin = 'replacement' AND status = 'completed'`.
- `CREATE UNIQUE INDEX uq_appointment_due_scheduled ON appointment (tenant_id, replacement_due_id) WHERE origin = 'replacement' AND status = 'scheduled'`.
- `CREATE UNIQUE INDEX uq_appointment_occurrence ON appointment (tenant_id, weekly_slot_id, occurrence_date) WHERE weekly_slot_id IS NOT NULL`.

### `appointment_event`

ORM: [`AppointmentEvent`](../../apps/api/src/clinic_api/db/models/scheduling/appointments.py).
Migração: [`0007_appointments`](../../apps/api/migrations/versions/0007_appointments.py). Regras relacionadas: RN-011, RN-012, RN-014 a RN-016.
Teste: [`test_appointment_schema.py`](../../apps/api/tests/test_appointment_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `appointment_id` | `UUID` | NOT NULL | `—` |
| `actor_id` | `UUID` | NULL | `—` |
| `recorded_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `kind` | `TEXT` | NOT NULL | `—` |
| `reason` | `TEXT` | NULL | `—` |
| `before` | `JSONB` | NOT NULL | `'{}'::jsonb` |
| `after` | `JSONB` | NOT NULL | `'{}'::jsonb` |

- `CONSTRAINT fk_appointment_event_appointment FOREIGN KEY(tenant_id, appointment_id) REFERENCES appointment (tenant_id, id)`.
- `CONSTRAINT fk_appointment_event_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_appointment_event_user_tenant FOREIGN KEY(tenant_id, actor_id) REFERENCES user_tenant (tenant_id, user_id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_appointment_event_tenant_id_id UNIQUE (tenant_id, id)`.

### `clinic`

ORM: [`Clinic`](../../apps/api/src/clinic_api/db/models/catalog/facilities.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `name` | `TEXT` | NOT NULL | `—` |
| `timezone` | `TEXT` | NOT NULL | `—` |
| `default_duration_minutes` | `INTEGER` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `CONSTRAINT ck_clinic_duration CHECK (default_duration_minutes > 0)`.
- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_clinic_tenant_id UNIQUE (tenant_id, id)`.

### `clinic_closure`

ORM: [`ClinicClosure`](../../apps/api/src/clinic_api/db/models/calendar/closures.py).
Migração: [`0009_calendar_schema`](../../apps/api/migrations/versions/0009_calendar_schema.py). Regras relacionadas: RN-017 a RN-020.
Teste: [`test_calendar_schema.py`](../../apps/api/tests/test_calendar_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `starts_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `ends_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `reason` | `TEXT` | NOT NULL | `—` |
| `created_by` | `UUID` | NOT NULL | `—` |

- `CONSTRAINT ck_clinic_closure_interval CHECK (starts_at < ends_at)`.
- `CONSTRAINT fk_clinic_closure_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_clinic_closure_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_clinic_closure_user_tenant FOREIGN KEY(tenant_id, created_by) REFERENCES user_tenant (tenant_id, user_id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_clinic_closure_tenant_id_id UNIQUE (tenant_id, id)`.
- `CREATE INDEX ix_clinic_closure_interval ON clinic_closure USING gist (tenant_id, tstzrange(starts_at, ends_at, '[)'))`.

### `clinic_hours`

ORM: [`ClinicHours`](../../apps/api/src/clinic_api/db/models/planning/availability.py).
Migração: [`0005_treatment_planning`](../../apps/api/migrations/versions/0005_treatment_planning.py). Regras relacionadas: RN-008.
Teste: [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `weekday` | `SMALLINT` | NOT NULL | `—` |
| `start_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `end_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `valid_from` | `DATE` | NOT NULL | `—` |
| `valid_until` | `DATE` | NULL | `—` |

- `CONSTRAINT ck_clinic_hours_validity CHECK (valid_until IS NULL OR valid_until >= valid_from)`.
- `CONSTRAINT ck_clinic_hours_weekday CHECK (weekday BETWEEN 0 AND 6)`.
- `CONSTRAINT ck_clinic_hours_window CHECK (start_time < end_time)`.
- `CONSTRAINT fk_clinic_hours_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_clinic_hours_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_clinic_hours_tenant_id_id UNIQUE (tenant_id, id)`.

### `generation_deficit`

ORM: [`GenerationDeficit`](../../apps/api/src/clinic_api/db/models/scheduling/agendas.py).
Migração: [`0010_monthly_agenda_schema`](../../apps/api/migrations/versions/0010_monthly_agenda_schema.py). Regras relacionadas: RN-013, RN-014.
Teste: [`test_agenda_schema.py`](../../apps/api/tests/test_agenda_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `generation_run_id` | `UUID` | NOT NULL | `—` |
| `treatment_plan_id` | `UUID` | NOT NULL | `—` |
| `week_start` | `DATE` | NOT NULL | `—` |
| `missing_count` | `INTEGER` | NOT NULL | `—` |
| `reason_code` | `TEXT` | NOT NULL | `—` |
| `details` | `JSONB` | NOT NULL | `'{}'::jsonb` |

- `CONSTRAINT ck_generation_deficit_missing CHECK (missing_count > 0)`.
- `CONSTRAINT ck_generation_deficit_reason_code CHECK (reason_code IN ('no_common_availability', 'no_compatible_room', 'resource_conflict'))`.
- `CONSTRAINT ck_generation_deficit_week CHECK (EXTRACT(ISODOW FROM week_start) = 1)`.
- `CONSTRAINT fk_generation_deficit_generation_run FOREIGN KEY(tenant_id, generation_run_id) REFERENCES generation_run (tenant_id, id)`.
- `CONSTRAINT fk_generation_deficit_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_generation_deficit_treatment_plan FOREIGN KEY(tenant_id, treatment_plan_id) REFERENCES treatment_plan (tenant_id, id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_generation_deficit_tenant_id_id UNIQUE (tenant_id, id)`.

### `generation_run`

ORM: [`GenerationRun`](../../apps/api/src/clinic_api/db/models/scheduling/agendas.py).
Migração: [`0010_monthly_agenda_schema`](../../apps/api/migrations/versions/0010_monthly_agenda_schema.py). Regras relacionadas: RN-013, RN-014.
Teste: [`test_agenda_schema.py`](../../apps/api/tests/test_agenda_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `monthly_agenda_id` | `UUID` | NOT NULL | `—` |
| `started_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `completed_at` | `TIMESTAMP WITH TIME ZONE` | NULL | `—` |
| `status` | `TEXT` | NOT NULL | `'running'` |
| `parameters` | `JSONB` | NOT NULL | `'{}'::jsonb` |

- `CONSTRAINT ck_generation_run_status CHECK (status IN ('running', 'completed', 'partial', 'failed'))`.
- `CONSTRAINT ck_generation_run_times CHECK (completed_at IS NULL OR completed_at >= started_at)`.
- `CONSTRAINT fk_generation_run_monthly_agenda FOREIGN KEY(tenant_id, monthly_agenda_id) REFERENCES monthly_agenda (tenant_id, id)`.
- `CONSTRAINT fk_generation_run_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_generation_run_tenant_id_id UNIQUE (tenant_id, id)`.

### `monthly_agenda`

ORM: [`MonthlyAgenda`](../../apps/api/src/clinic_api/db/models/scheduling/agendas.py).
Migração: [`0010_monthly_agenda_schema`](../../apps/api/migrations/versions/0010_monthly_agenda_schema.py). Regras relacionadas: RN-013, RN-014.
Teste: [`test_agenda_schema.py`](../../apps/api/tests/test_agenda_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `month` | `DATE` | NOT NULL | `—` |

- `CONSTRAINT ck_monthly_agenda_month CHECK (EXTRACT(DAY FROM month) = 1)`.
- `CONSTRAINT fk_monthly_agenda_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_monthly_agenda_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_monthly_agenda_tenant_id_clinic_id_month UNIQUE (tenant_id, clinic_id, month)`.
- `CONSTRAINT uq_monthly_agenda_tenant_id_id UNIQUE (tenant_id, id)`.

### `patient`

ORM: [`Patient`](../../apps/api/src/clinic_api/db/models/catalog/people.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_patient_tenant_id UNIQUE (tenant_id, id)`.

### `patient_availability`

ORM: [`PatientAvailability`](../../apps/api/src/clinic_api/db/models/planning/availability.py).
Migração: [`0005_treatment_planning`](../../apps/api/migrations/versions/0005_treatment_planning.py). Regras relacionadas: RN-008.
Teste: [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `patient_id` | `UUID` | NOT NULL | `—` |
| `weekday` | `SMALLINT` | NOT NULL | `—` |
| `start_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `end_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `valid_from` | `DATE` | NOT NULL | `—` |
| `valid_until` | `DATE` | NULL | `—` |

- `CONSTRAINT ck_patient_availability_validity CHECK (valid_until IS NULL OR valid_until >= valid_from)`.
- `CONSTRAINT ck_patient_availability_weekday CHECK (weekday BETWEEN 0 AND 6)`.
- `CONSTRAINT ck_patient_availability_window CHECK (start_time < end_time)`.
- `CONSTRAINT fk_patient_availability_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_patient_availability_patient FOREIGN KEY(tenant_id, patient_id) REFERENCES patient (tenant_id, id)`.
- `CONSTRAINT fk_patient_availability_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_patient_availability_tenant_id_id UNIQUE (tenant_id, id)`.

### `patient_clinic`

ORM: [`PatientClinic`](../../apps/api/src/clinic_api/db/models/catalog/affiliations.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `patient_id` | `UUID` | NOT NULL | `—` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_patient_clinic_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_patient_clinic_patient FOREIGN KEY(tenant_id, patient_id) REFERENCES patient (tenant_id, id)`.
- `PRIMARY KEY (tenant_id, patient_id, clinic_id)`.

### `person_block`

ORM: [`PersonBlock`](../../apps/api/src/clinic_api/db/models/calendar/person_blocks.py).
Migração: [`0009_calendar_schema`](../../apps/api/migrations/versions/0009_calendar_schema.py). Regras relacionadas: RN-017 a RN-020.
Teste: [`test_calendar_schema.py`](../../apps/api/tests/test_calendar_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `patient_id` | `UUID` | NULL | `—` |
| `therapist_id` | `UUID` | NULL | `—` |
| `starts_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `ends_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `—` |
| `reason` | `TEXT` | NOT NULL | `—` |
| `created_by` | `UUID` | NOT NULL | `—` |

- `CONSTRAINT ck_person_block_interval CHECK (starts_at < ends_at)`.
- `CONSTRAINT ck_person_block_one_person CHECK ((patient_id IS NOT NULL) <> (therapist_id IS NOT NULL))`.
- `CONSTRAINT fk_person_block_patient FOREIGN KEY(tenant_id, patient_id) REFERENCES patient (tenant_id, id)`.
- `CONSTRAINT fk_person_block_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_person_block_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `CONSTRAINT fk_person_block_user_tenant FOREIGN KEY(tenant_id, created_by) REFERENCES user_tenant (tenant_id, user_id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_person_block_tenant_id_id UNIQUE (tenant_id, id)`.
- `CREATE INDEX ix_person_block_interval ON person_block USING gist (tenant_id, tstzrange(starts_at, ends_at, '[)'))`.

### `replacement_due`

ORM: [`ReplacementDue`](../../apps/api/src/clinic_api/db/models/scheduling/replacements.py).
Migração: [`0008_replacement_schema`](../../apps/api/migrations/versions/0008_replacement_schema.py). Regras relacionadas: RN-021 a RN-026.
Teste: [`test_replacement_schema.py`](../../apps/api/tests/test_replacement_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `original_origin` | `TEXT` | NOT NULL | `GENERATED ALWAYS AS ('routine') STORED` |
| `original_appointment_id` | `UUID` | NOT NULL | `—` |
| `treatment_plan_id` | `UUID` | NOT NULL | `—` |
| `reason` | `TEXT` | NOT NULL | `—` |
| `status` | `TEXT` | NOT NULL | `'pending'` |
| `decided_by` | `UUID` | NULL | `—` |
| `decided_at` | `TIMESTAMP WITH TIME ZONE` | NULL | `—` |
| `closed_reason` | `TEXT` | NULL | `—` |

- `CONSTRAINT ck_replacement_due_closure CHECK (status <> 'closed' OR (closed_reason IS NOT NULL AND length(trim(closed_reason)) > 0 AND decided_by IS NOT NULL))`.
- `CONSTRAINT ck_replacement_due_decision CHECK ((decided_by IS NULL) = (decided_at IS NULL))`.
- `CONSTRAINT ck_replacement_due_status CHECK (status IN ('pending', 'scheduled', 'completed', 'closed'))`.
- `CONSTRAINT fk_replacement_due_appointment FOREIGN KEY(tenant_id, original_appointment_id) REFERENCES appointment (tenant_id, id)`.
- `CONSTRAINT fk_replacement_due_original_plan FOREIGN KEY(tenant_id, original_appointment_id, treatment_plan_id, original_origin) REFERENCES appointment (tenant_id, id, treatment_plan_id, origin)`.
- `CONSTRAINT fk_replacement_due_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_replacement_due_treatment_plan FOREIGN KEY(tenant_id, treatment_plan_id) REFERENCES treatment_plan (tenant_id, id)`.
- `CONSTRAINT fk_replacement_due_user_tenant FOREIGN KEY(tenant_id, decided_by) REFERENCES user_tenant (tenant_id, user_id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_replacement_due_tenant_id_id UNIQUE (tenant_id, id)`.
- `CONSTRAINT uq_replacement_due_tenant_id_id_treatment_plan_id UNIQUE (tenant_id, id, treatment_plan_id)`.
- `CONSTRAINT uq_replacement_due_tenant_id_original_appointment_id UNIQUE (tenant_id, original_appointment_id)`.

### `room`

ORM: [`Room`](../../apps/api/src/clinic_api/db/models/catalog/facilities.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `name` | `TEXT` | NOT NULL | `—` |
| `normalized_name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_room_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_room_clinic_id UNIQUE (tenant_id, clinic_id, id)`.
- `CONSTRAINT uq_room_name UNIQUE (tenant_id, clinic_id, normalized_name)`.
- `CONSTRAINT uq_room_tenant_id UNIQUE (tenant_id, id)`.

### `room_specialty`

ORM: [`RoomSpecialty`](../../apps/api/src/clinic_api/db/models/catalog/specialties.py).
Migração: [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `room_id` | `UUID` | NOT NULL | `—` |
| `specialty_id` | `UUID` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_room_specialty_room FOREIGN KEY(tenant_id, room_id) REFERENCES room (tenant_id, id)`.
- `CONSTRAINT fk_room_specialty_specialty FOREIGN KEY(tenant_id, specialty_id) REFERENCES specialty (tenant_id, id)`.
- `PRIMARY KEY (tenant_id, room_id, specialty_id)`.

### `specialty`

ORM: [`Specialty`](../../apps/api/src/clinic_api/db/models/catalog/specialties.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `name` | `TEXT` | NOT NULL | `—` |
| `normalized_name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_specialty_name UNIQUE (tenant_id, normalized_name)`.
- `CONSTRAINT uq_specialty_tenant_id UNIQUE (tenant_id, id)`.

### `tenant`

ORM: [`Tenant`](../../apps/api/src/clinic_api/db/models/identity/organization.py).
Migração: [`0001_identity`](../../apps/api/migrations/versions/0001_identity.py). Regras relacionadas: RN-001, RN-003.
Teste: [`test_database.py`](../../apps/api/tests/test_database.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `PRIMARY KEY (id)`.

### `therapist`

ORM: [`Therapist`](../../apps/api/src/clinic_api/db/models/catalog/people.py).
Migração: `0003_catalog` → [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_therapist_tenant_id UNIQUE (tenant_id, id)`.

### `therapist_availability`

ORM: [`TherapistAvailability`](../../apps/api/src/clinic_api/db/models/planning/availability.py).
Migração: [`0005_treatment_planning`](../../apps/api/migrations/versions/0005_treatment_planning.py). Regras relacionadas: RN-008.
Teste: [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `therapist_id` | `UUID` | NOT NULL | `—` |
| `weekday` | `SMALLINT` | NOT NULL | `—` |
| `start_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `end_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `valid_from` | `DATE` | NOT NULL | `—` |
| `valid_until` | `DATE` | NULL | `—` |

- `CONSTRAINT ck_therapist_availability_validity CHECK (valid_until IS NULL OR valid_until >= valid_from)`.
- `CONSTRAINT ck_therapist_availability_weekday CHECK (weekday BETWEEN 0 AND 6)`.
- `CONSTRAINT ck_therapist_availability_window CHECK (start_time < end_time)`.
- `CONSTRAINT fk_therapist_availability_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_therapist_availability_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_therapist_availability_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_therapist_availability_tenant_id_id UNIQUE (tenant_id, id)`.

### `therapist_clinic`

ORM: [`TherapistClinic`](../../apps/api/src/clinic_api/db/models/catalog/affiliations.py).
Migração: [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `therapist_id` | `UUID` | NOT NULL | `—` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_therapist_clinic_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_therapist_clinic_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `PRIMARY KEY (tenant_id, therapist_id, clinic_id)`.

### `therapist_specialty`

ORM: [`TherapistSpecialty`](../../apps/api/src/clinic_api/db/models/catalog/specialties.py).
Migração: [`0004_catalog_integrity`](../../apps/api/migrations/versions/0004_catalog_integrity.py). Regras relacionadas: RN-001 a RN-004, RN-026.
Teste: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `therapist_id` | `UUID` | NOT NULL | `—` |
| `specialty_id` | `UUID` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_therapist_specialty_specialty FOREIGN KEY(tenant_id, specialty_id) REFERENCES specialty (tenant_id, id)`.
- `CONSTRAINT fk_therapist_specialty_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `PRIMARY KEY (tenant_id, therapist_id, specialty_id)`.

### `treatment_plan`

ORM: [`TreatmentPlan`](../../apps/api/src/clinic_api/db/models/planning/treatment.py).
Migração: [`0005_treatment_planning`](../../apps/api/migrations/versions/0005_treatment_planning.py). Regras relacionadas: RN-005 a RN-007.
Teste: [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `patient_id` | `UUID` | NOT NULL | `—` |
| `therapist_id` | `UUID` | NOT NULL | `—` |
| `specialty_id` | `UUID` | NOT NULL | `—` |
| `sessions_per_week` | `INTEGER` | NOT NULL | `—` |
| `duration_minutes` | `INTEGER` | NULL | `—` |
| `valid_from` | `DATE` | NOT NULL | `—` |
| `valid_until` | `DATE` | NULL | `—` |

- `CONSTRAINT ck_treatment_plan_duration CHECK (duration_minutes IS NULL OR duration_minutes > 0)`.
- `CONSTRAINT ck_treatment_plan_frequency CHECK (sessions_per_week > 0)`.
- `CONSTRAINT ck_treatment_plan_validity CHECK (valid_until IS NULL OR valid_until >= valid_from)`.
- `CONSTRAINT ex_treatment_plan_validity EXCLUDE USING gist (tenant_id WITH =, patient_id WITH =, therapist_id WITH =, specialty_id WITH =, daterange(valid_from, valid_until + 1, '[)') WITH &&)`.
- `CONSTRAINT fk_treatment_plan_patient FOREIGN KEY(tenant_id, patient_id) REFERENCES patient (tenant_id, id)`.
- `CONSTRAINT fk_treatment_plan_specialty FOREIGN KEY(tenant_id, specialty_id) REFERENCES specialty (tenant_id, id)`.
- `CONSTRAINT fk_treatment_plan_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_treatment_plan_therapist FOREIGN KEY(tenant_id, therapist_id) REFERENCES therapist (tenant_id, id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_treatment_plan_identity UNIQUE (tenant_id, id, patient_id, therapist_id, specialty_id)`.
- `CONSTRAINT uq_treatment_plan_tenant_id_id UNIQUE (tenant_id, id)`.

### `treatment_plan_clinic`

ORM: [`TreatmentPlanClinic`](../../apps/api/src/clinic_api/db/models/planning/treatment.py).
Migração: [`0005_treatment_planning`](../../apps/api/migrations/versions/0005_treatment_planning.py). Regras relacionadas: RN-005 a RN-007.
Teste: [`test_planning_schema.py`](../../apps/api/tests/test_planning_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `treatment_plan_id` | `UUID` | NOT NULL | `—` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `CONSTRAINT fk_treatment_plan_clinic_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_treatment_plan_clinic_treatment_plan FOREIGN KEY(tenant_id, treatment_plan_id) REFERENCES treatment_plan (tenant_id, id)`.
- `PRIMARY KEY (tenant_id, treatment_plan_id, clinic_id)`.

### `user`

ORM: [`User`](../../apps/api/src/clinic_api/db/models/identity/access.py).
Migração: [`0001_identity`](../../apps/api/migrations/versions/0001_identity.py). Regras relacionadas: RN-001, RN-003.
Teste: [`test_database.py`](../../apps/api/tests/test_database.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `name` | `TEXT` | NOT NULL | `—` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `PRIMARY KEY (id)`.

### `user_tenant`

ORM: [`UserTenant`](../../apps/api/src/clinic_api/db/models/identity/access.py).
Migração: [`0001_identity`](../../apps/api/migrations/versions/0001_identity.py). Regras relacionadas: RN-001, RN-003.
Teste: [`test_database.py`](../../apps/api/tests/test_database.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `user_id` | `UUID` | NOT NULL | `—` |
| `role` | `TEXT` | NOT NULL | `'admin'` |
| `active` | `BOOLEAN` | NOT NULL | `true` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |

- `CONSTRAINT ck_user_tenants_admin_role CHECK (role = 'admin')`.
- `FOREIGN KEY(user_id) REFERENCES "user" (id)`.
- `FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `PRIMARY KEY (tenant_id, user_id)`.

### `weekly_slot`

ORM: [`WeeklySlot`](../../apps/api/src/clinic_api/db/models/planning/weekly.py).
Migração: [`0006_weekly_slots`](../../apps/api/migrations/versions/0006_weekly_slots.py). Regras relacionadas: RN-009, RN-010, RN-014.
Teste: [`test_weekly_slot_schema.py`](../../apps/api/tests/test_weekly_slot_schema.py).

| Coluna | Tipo | Nulabilidade | Default SQL |
| --- | --- | --- | --- |
| `id` | `UUID` | NOT NULL | `—` |
| `tenant_id` | `UUID` | NOT NULL | `—` |
| `created_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `updated_at` | `TIMESTAMP WITH TIME ZONE` | NOT NULL | `now()` |
| `treatment_plan_id` | `UUID` | NOT NULL | `—` |
| `clinic_id` | `UUID` | NOT NULL | `—` |
| `room_id` | `UUID` | NOT NULL | `—` |
| `weekday` | `SMALLINT` | NOT NULL | `—` |
| `start_time` | `TIME WITHOUT TIME ZONE` | NOT NULL | `—` |
| `duration_minutes` | `INTEGER` | NOT NULL | `—` |
| `valid_from` | `DATE` | NOT NULL | `—` |
| `valid_until` | `DATE` | NULL | `—` |

- `CONSTRAINT ck_weekly_slot_duration CHECK (duration_minutes > 0)`.
- `CONSTRAINT ck_weekly_slot_validity CHECK (valid_until IS NULL OR valid_until >= valid_from)`.
- `CONSTRAINT ck_weekly_slot_weekday CHECK (weekday BETWEEN 0 AND 6)`.
- `CONSTRAINT fk_weekly_slot_clinic FOREIGN KEY(tenant_id, clinic_id) REFERENCES clinic (tenant_id, id)`.
- `CONSTRAINT fk_weekly_slot_room FOREIGN KEY(tenant_id, room_id) REFERENCES room (tenant_id, id)`.
- `CONSTRAINT fk_weekly_slot_room_clinic FOREIGN KEY(tenant_id, clinic_id, room_id) REFERENCES room (tenant_id, clinic_id, id)`.
- `CONSTRAINT fk_weekly_slot_tenant FOREIGN KEY(tenant_id) REFERENCES tenant (id)`.
- `CONSTRAINT fk_weekly_slot_treatment_plan FOREIGN KEY(tenant_id, treatment_plan_id) REFERENCES treatment_plan (tenant_id, id)`.
- `CONSTRAINT fk_weekly_slot_treatment_plan_clinic FOREIGN KEY(tenant_id, treatment_plan_id, clinic_id) REFERENCES treatment_plan_clinic (tenant_id, treatment_plan_id, clinic_id)`.
- `PRIMARY KEY (id)`.
- `CONSTRAINT uq_weekly_slot_tenant_id_id UNIQUE (tenant_id, id)`.
- `CONSTRAINT uq_weekly_slot_tenant_id_id_treatment_plan_id UNIQUE (tenant_id, id, treatment_plan_id)`.

## Manutenção

Atualizar modelos, migrações e testes junto do dicionário.
As demais estruturas do desenho permanecem planejadas até sua migração.
