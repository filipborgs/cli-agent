# Dicionário físico do banco

Status: 12 tabelas de aplicação e modelos ORM implementados; head
Alembic `0004_catalog_integrity`. Serviços clínicos e geração automática continuam planejados.

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

## Evidências

Testes de banco disponíveis: [`test_catalog_schema.py`](../../apps/api/tests/test_catalog_schema.py).
O registro ORM e o round-trip das migrações são verificados pelos testes
existentes de banco. Auditoria transversal adicional permanece planejada.

## Tabelas, colunas e constraints

Tipos abaixo são PostgreSQL. `NULL` indica campo opcional; `—` indica ausência
de default SQL. PKs e constraints sem nome explícito recebem o nome padrão do
PostgreSQL. `alembic_version` é controle da ferramenta e não recebe acesso runtime.

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


## Manutenção

Atualizar modelos, migrações e testes junto do dicionário.
As demais estruturas do desenho permanecem planejadas até sua migração.
