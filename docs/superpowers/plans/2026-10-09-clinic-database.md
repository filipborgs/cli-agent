# Clinic Database Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementar a persistência multi-tenant e os serviços de negócio que sustentam a agenda mensal, seus ajustes e suas reposições.

**Architecture:** PostgreSQL garante isolamento e integridade, incluindo reservas concorrentes. A API usa SQLAlchemy síncrono e transações por operação, com migrações Alembic executadas separadamente do servidor. Serviços Python mantêm cadastro, rotina, calendário, sessões e reposições; endpoints clínicos e interfaces web dependem de entregas posteriores de autenticação e produto.

**Tech Stack:** Python 3.13, FastAPI, PostgreSQL 18, SQLAlchemy 2, Alembic 1, Psycopg 3, uv, pytest, Ruff, mypy, Docker Compose e GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-09-clinic-database-design.md`; ler também `docs/business/business-rules.md` e `docs/architecture/clinic-database-diagrams.md`.

## Global Constraints

- O web consome a API somente por HTTP; a API nunca depende do web.
- Um tenant representa uma organização com uma ou mais clínicas.
- Pacientes e terapeutas têm cadastro único por organização.
- No MVP, apenas a equipe administrativa acessa a aplicação.
- A reposição é realizada apenas pelo terapeuta original.
- A geração não cria sessões em feriados ou recessos.
- Gerar novamente um mês preserva os ajustes manuais e as sessões realizadas.
- Semana de segunda a domingo; a geração mensal materializa somente as datas do mês, sem proporcionalizar a frequência em semanas parciais.
- Uma sessão tem um paciente, um terapeuta e uma sala.
- Reposição é extra em relação à rotina da semana em que for realizada.
- Usar `uv`, Ruff, mypy estrito e pytest; testes antes de mudar comportamento.
- Não editar manualmente `apps/api/uv.lock` ou `pnpm-lock.yaml`.
- Executar `make check`, `make test`, `make build` e `make smoke` antes de concluir a implementação transversal.
- Um commit por objetivo testável. Só executar commits quando autorizados na sessão de implementação.
- Organizar `db/models` em pacotes por domínio, com arquivos pequenos de entidades relacionadas; não concentrar cada domínio em um único arquivo crescente.
- Organizar também `domain` por domínio, com tipos e serviços próximos das regras que possuem; código compartilhado contém apenas conceitos realmente transversais.
- Toda entrega deve atualizar sua documentação de negócio, banco, arquitetura, interfaces e operação conforme o que mudar; incluir referências curtas para agentes de IA.
- Documentação de referência deve orientar por assunto e contrato, sem referências a números de tasks, handoffs ou tracking; registrar progresso somente no plano e nos registros de execução.

## Review Focus

- Conexão reutilizada após erro: tenant anterior não pode vazar para outra operação; teste na Task 2.
- Mesma pessoa em clínicas diferentes e gravações simultâneas: somente uma reserva conflitante pode ser confirmada; teste na Task 6.
- Rotina na fronteira do mês e mudança de fuso: nenhuma ocorrência duplicada ou deslocada silenciosamente; testes nas Tasks 4 e 9.
- Falta antecipada antes de gerar o mês e coincidente com feriado: preservar o direito apenas quando havia atendimento devido; teste na Task 8.
- Reposição cancelada por fechamento ou nova falta: reabrir a mesma pendência, sem criar uma dívida filha; testes nas Tasks 7 e 8.

---

## Escopo e ordem de entrega

Este plano entrega banco, migrações e serviços Python testáveis. Não publica
endpoints clínicos sem autenticação. `GET /api/health` continua com seu contrato
atual. Autenticação, DTOs HTTP e telas exigem planos próprios; não são pré-requisito
para testar os serviços com identidades administrativas semeadas nos testes.

Task 0 registra a documentação inicial de negócio, banco e contexto para agentes,
já iniciada nesta etapa de planejamento. Tasks 1–5 entregam a base de dados e o
planejamento semanal. Tasks 6–9 entregam as operações transacionais da agenda.
Task 10 fecha a integração implantável; Task 11 consolida a documentação do que
foi efetivamente implementado. Documentar cada task é parte de sua entrega,
não uma atividade adiada integralmente para a Task 11.
Todas as regras RN-001 a RN-026 têm cobertura neste plano.

## Estrutura de arquivos

Novos módulos dentro de `apps/api/src/clinic_api/`:

| Arquivo | Responsabilidade |
| --- | --- |
| `settings.py` | Ler URLs de banco e configuração do processo, sem abrir conexões no import. |
| `db/base.py`, `db/session.py` | Metadata, engine, transações e contexto autorizado de tenant. |
| `db/models/identity/organization.py` | Tenant e clínica: estrutura da organização. |
| `db/models/identity/access.py` | Usuário e participação administrativa no tenant. |
| `db/models/catalog/people.py` | Paciente e terapeuta: cadastros únicos no tenant. |
| `db/models/catalog/affiliations.py` | Participações de pacientes e terapeutas nas clínicas. |
| `db/models/catalog/specialties.py` | Especialidade e habilitação do terapeuta. |
| `db/models/catalog/facilities.py` | Sala e suas especialidades permitidas. |
| `db/models/planning/treatment.py` | Plano de atendimento e clínicas habilitadas para o vínculo. |
| `db/models/planning/availability.py` | Disponibilidades do paciente/terapeuta e funcionamento da clínica. |
| `db/models/planning/weekly.py` | Horários semanais planejados e suas vigências. |
| `db/models/calendar/closures.py` | Fechamentos por feriado ou recesso. |
| `db/models/calendar/person_blocks.py` | Indisponibilidades individuais. |
| `db/models/scheduling/agendas.py` | Agenda mensal, execuções de geração e déficits de encaixe. |
| `db/models/scheduling/appointments.py` | Sessão e eventos do seu histórico. |
| `db/models/scheduling/replacements.py` | Pendência de reposição; tentativas continuam sendo sessões. |
| `db/models/registry.py` | Registro explícito e idempotente dos modelos na metadata. |
| `domain/shared/errors.py` | Hierarquia mínima de erros realmente transversais. |
| `domain/identity/context.py` | Contexto administrativo de organização e usuário. |
| `domain/catalog/clinics.py`, `people.py`, `rooms.py` | Cadastro de clínicas, pessoas e salas, cada qual em seu módulo. |
| `domain/catalog/affiliations.py`, `specialties.py`, `lifecycle.py` | Participações, habilitações e inativação de cadastros. |
| `domain/planning/treatments.py`, `availability.py`, `weekly.py` | Vínculos, janelas de disponibilidade e rotina semanal. |
| `domain/planning/time.py`, `types.py` | Conversão de horários e tipos de planejamento. |
| `domain/calendar/closures.py`, `person_blocks.py`, `queries.py` | Fechamentos, ausências individuais e consultas de impedimentos. |
| `domain/scheduling/appointments.py` | Reserva, ajustes e resultado das sessões. |
| `domain/scheduling/replacements.py`, `replacement_state.py` | Direito/encaixe de reposições e transições da dívida após cada tentativa. |
| `domain/scheduling/types.py` | Estados e decisões das sessões e reposições. |
| `domain/scheduling/generation/service.py` | Orquestração transacional da geração mensal. |
| `domain/scheduling/generation/candidates.py` | Busca determinística de candidatos a horários semanais. |
| `domain/scheduling/generation/diagnostics.py`, `types.py` | Diagnóstico dos déficits e contratos do gerador. |

Migrações: `apps/api/alembic.ini`, `apps/api/migrations/env.py`,
`apps/api/migrations/script.py.mako` e `apps/api/migrations/versions/`.
Infraestrutura de teste: `compose.test.yaml`, `scripts/test-api.sh`,
`apps/api/tests/conftest.py`, `apps/api/tests/factories.py`.
Cada task indica seus testes específicos. Criar `__init__.py` nos novos pacotes.

### Organização inicial de `models`

```text
db/
├── base.py
├── session.py
└── models/
    ├── __init__.py
    ├── registry.py
    ├── identity/
    │   ├── __init__.py
    │   ├── organization.py
    │   └── access.py
    ├── catalog/
    │   ├── __init__.py
    │   ├── people.py
    │   ├── affiliations.py
    │   ├── specialties.py
    │   └── facilities.py
    ├── planning/
    │   ├── __init__.py
    │   ├── treatment.py
    │   ├── availability.py
    │   └── weekly.py
    ├── calendar/
    │   ├── __init__.py
    │   ├── closures.py
    │   └── person_blocks.py
    └── scheduling/
        ├── __init__.py
        ├── agendas.py
        ├── appointments.py
        └── replacements.py
```

- Cada arquivo contém as entidades indicadas na tabela; associações ficam junto
  do domínio a que dão significado, sem uma pasta genérica de associações.
- Todos os modelos usam a mesma `Base` de `db/base.py`, com uma única metadata.
- Serviços e testes importam classes do módulo proprietário, por exemplo
  `from clinic_api.db.models.scheduling.appointments import Appointment`.
- `__init__.py` identifica o pacote, sem reunir todos os modelos ou iniciar conexões.
- `db/models/registry.py` expõe `register_models() -> None`: faz imports explícitos
  dos módulos já entregues para registrar suas tabelas, sem descoberta dinâmica.
  Cada task acrescenta seus módulos ao registro quando os implementa.
- Alembic e o setup de persistência chamam `register_models()` antes de usar
  `Base.metadata` ou configurar os mappers; importar o registro duas vezes não
  adiciona outra tabela ou outra metadata.
- FKs entre pacotes usam referências de tabela; relacionamentos usam referências
  de classe e `TYPE_CHECKING` quando necessário para evitar imports circulares.
  Em especial, sessão e dívida de reposição não devem importar uma à outra
  em runtime apenas para resolver anotações.
- Não criar pacotes vazios para funcionalidades futuras. Os arquivos desta
  árvore surgem nas tasks que introduzem suas entidades.

### Organização inicial de `domain`

Todos os diretórios abaixo terão `__init__.py` mínimo, omitido da árvore para
facilitar a leitura. As funções mantêm as assinaturas das tasks, mas residem no
módulo proprietário indicado aqui.

```text
domain/
├── shared/
│   └── errors.py
├── identity/
│   └── context.py
├── catalog/
│   ├── clinics.py
│   ├── people.py
│   ├── rooms.py
│   ├── affiliations.py
│   ├── specialties.py
│   └── lifecycle.py
├── planning/
│   ├── treatments.py
│   ├── availability.py
│   ├── weekly.py
│   ├── time.py
│   └── types.py
├── calendar/
│   ├── closures.py
│   ├── person_blocks.py
│   └── queries.py
└── scheduling/
    ├── appointments.py
    ├── replacements.py
    ├── replacement_state.py
    ├── types.py
    └── generation/
        ├── service.py
        ├── candidates.py
        ├── diagnostics.py
        └── types.py
```

- Tipos pertencem ao domínio que os define, sem um `domain/types.py` crescente.
  `shared` não deve virar uma coleção genérica de utilidades.
- Importar diretamente do módulo proprietário, sem fachadas agregando todo o domínio.
- Consultas de bloqueios em `calendar/queries.py` não chamam serviços de agenda.
  Agendamentos usam essas consultas; fechamentos/ausências chamam operações de
  agenda e reposição sem criar uma dependência circular entre os módulos.
- `scheduling/replacement_state.py` concentra a atualização de uma dívida após
  o resultado de sua tentativa. Sessões e reposições usam esse módulo; serviços
  de sessão não importam o serviço completo de reposições.
- Gerador separa seleção de candidatos, diagnóstico e orquestração transacional.
  Candidatos não gravam sessões; só a orquestração controla a geração mensal.
- Os arquivos são criados na task de sua funcionalidade, com testes de suas regras.

## Documentação obrigatória em cada task

Antes de fechar qualquer task, atualizar os documentos afetados:

| Mudança | Referência a manter |
| --- | --- |
| Regra ou fluxo de negócio | `docs/business/business-rules.md`, `workflows.md` e escopo, com IDs RN preservados |
| Tabela, coluna, estado, FK, índice, constraint ou política RLS | `docs/database/schema.md` e diagramas; vincular migração, regra e teste |
| Transação, interface de serviço, módulo ou dependência | `docs/architecture/clinic-domain-modules.md` e `docs/agents/database-context.md` |
| Variável, migração, bootstrap ou comando operacional | `docs/database/operations.md`, README da API e workflow |
| Escolha arquitetural nova com impacto | ADR em `docs/decisions/`, seguindo a numeração existente |
| Situação de entrega | Índices humano e para agentes: distinguir aprovado/planejado de implementado/verificado |

Cada task inclui essa atualização no mesmo objetivo revisável de implementação,
antes do commit autorizado. Documentar contratos, decisões e invariantes; não
copiar corpos de funções para Markdown nem duplicar regras em vários arquivos.
Se a mudança não afeta uma dessas referências, não inventar documentação ou ADR
redundante: conferir a referência existente e mantê-la como fonte canônica.

## Contrato físico do banco

A referência canônica de convenções, tabelas/campos, estados e constraints é
[docs/database/schema.md](../../database/schema.md). A implementação de cada task
deve ler e atualizar o trecho correspondente do dicionário. O contrato foi
separado do plano para agentes consultarem somente o assunto relevante e para
evitar duas definições físicas divergentes.

## Interfaces compartilhadas

Definir tipos imutáveis (dataclasses) e enums nos módulos proprietários:

- `domain/identity/context.py`: `AccessContext(user_id: UUID, tenant_id: UUID)`.
- `domain/planning/types.py`: `WeekWindow(weekday: int, start: time, end: time, valid_from: date, valid_until: date | None)`.
- `domain/scheduling/types.py`: `ReplacementDecision`, `AbsenceKind`
  (`therapist`, `patient_notice`, `patient_no_notice`), `AppointmentOrigin`,
  `AppointmentStatus`, `ReplacementStatus`.
- `domain/scheduling/generation/types.py`: `GenerationResult`, `GenerationDeficit`,
  `DeficitReason` e `SlotCandidate`, introduzidos na Task 9.
Enums usam membros Python em maiúsculas (`THERAPIST`, `DISPENSED`, etc.) e
valores persistidos minúsculos conforme o contrato físico.

`TenantSession` é uma subclasse de `sqlalchemy.orm.Session`, com
`context: AccessContext`, criada somente por `tenant_session`.
IDs retornados são `UUID`; consultas usam modelos tipados SQLAlchemy.
Serviços recebem `TenantSession`, usam `flush`, mas não fazem `commit`.
`tenant_session` confirma ao sair sem erro e faz rollback em qualquer exceção.

`domain/shared/errors.py`: `AccessDenied`, `ValidationError`, `SchedulingConflict`,
`InvalidTransition`, todos derivados de `DomainError`. Não retornar mensagens
SQL nem confiar em IDs de tenant enviados como autorização.

### Task 0: Iniciar documentação de negócio, banco e contexto para agentes

**Files:** documentação existente em `docs/business/README.md`, `docs/business/business-rules.md`, `docs/business/workflows.md`, `docs/superpowers/specs/2026-10-09-clinic-database-design.md`, `docs/architecture/clinic-database-diagrams.md`; criar `docs/database/README.md`, `docs/database/schema.md`, `docs/database/operations.md`, `docs/agents/README.md`, `docs/agents/database-context.md`, `docs/architecture/clinic-domain-modules.md`; atualizar `AGENTS.md`, `apps/api/AGENTS.md`, `README.md`, `docs/development/workflow.md`.

**Interfaces:** fonte funcional nos IDs RN-001 a RN-026; índice para agentes com
leitura por assunto, fontes canônicas, estado do projeto e mapa de módulos;
documentação do banco com referência ao desenho e ao contrato físico planejado.

- [x] **Step 1:** Registrar escopo, vocabulário, regras e exemplos discutidos com a clínica. Negócio, desenho e diagramas já existem e foram aprovados antes deste plano.
- [x] **Step 2:** Iniciar a referência do banco, explicitando modelo aprovado, tabelas por domínio, integridade, estados e o fato de que migrações ainda não existem.
- [x] **Step 3:** Criar índice/contexto otimizados para agentes e mapa dos módulos; registrar no `AGENTS.md` a leitura direcionada e a obrigação de documentar cada entrega.
- [x] **Step 4:** Conferir links locais, caminhos, cobertura das 26 regras e distinção entre planejado e implementado. Executar `git diff --check`; documentos de negócio e técnicos não devem se contradizer.
- [x] **Step 5:** Solicitar autorização antes de commitar a documentação e o plano; autorização recebida do usuário. Esta task foi iniciada durante o planejamento, não deve ser recriada pela sessão de implementação.

### Task 1: PostgreSQL, migrações e testes reais de persistência

**Files:** criar `settings.py`, `db/base.py`, `db/session.py` (engine apenas nesta task), arquivos Alembic, `compose.test.yaml`, `scripts/test-api.sh`, `apps/api/tests/conftest.py`, `apps/api/tests/factories.py`, `apps/api/tests/test_database.py`, migração `0001_identity.py`; modificar `apps/api/pyproject.toml`, `apps/api/uv.lock`, `Makefile`, `.env.example`, `.github/workflows/ci.yml`.

**Interfaces:** produzir `create_engine(database_url: str) -> Engine`,
`Settings(database_url: str, migration_database_url: str | None)`, `Base: DeclarativeBase`.
URLs são lidas de `DATABASE_URL` e `MIGRATION_DATABASE_URL`. Fixtures:
`admin_engine: Engine`, `runtime_engine: Engine`, `factory: ClinicFactory`.
Runtime não exige URL de migração; Alembic exige `MIGRATION_DATABASE_URL`.

Assertion de referência para o teste do papel runtime (importar `sqlalchemy.text`):

```python
def test_runtime_role_is_not_privileged(runtime_engine):
    with runtime_engine.connect() as connection:
        role = connection.execute(text(
            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )).one()
    assert role.rolsuper is False
    assert role.rolbypassrls is False
```

- [ ] **Step 1:** Escrever `test_upgrade_downgrade_upgrade` verificando `upgrade head`, presença de `tenants`, downgrade para base sem tabelas de negócio e upgrade novamente; `test_runtime_role_is_not_privileged` deve afirmar `rolsuper == False` e `rolbypassrls == False`.
- [ ] **Step 2:** Rodar `uv run --project apps/api pytest apps/api/tests/test_database.py -v`; confirmar falha por ausência de configuração/modelos. Se faltarem dependências, instalá-las via uv antes de executar e obter a falha de comportamento.
- [ ] **Step 3:** Adicionar `sqlalchemy>=2.0,<3`, `alembic>=1.16,<2`, `psycopg[binary]>=3.2,<4` via `uv add --project apps/api`. Criar engine síncrono e Alembic com metadata registrada. `0001_identity.py` cria `tenants`, `users`, `user_tenants` e `btree_gist`; habilita e força RLS sem políticas permissivas, negando acesso runtime até a Task 2.
- [ ] **Step 4:** Criar o runner de testes PostgreSQL 18. `scripts/test-api.sh` sobe um projeto Compose exclusivo, cria `clinic_migrator` (dono do esquema, BYPASSRLS, sem superuser) e `clinic_runtime` (sem superuser/BYPASSRLS), exporta URLs de teste, roda `pytest -W error -v` e sempre remove volumes por trap. Usar credenciais locais exclusivas desse banco descartável. Fixtures aplicam migrations com migrator, usam runtime nos serviços e limpam dados com migrator entre testes. Não pular testes de banco silenciosamente.
- [ ] **Step 5:** Fazer `make test` usar `bash scripts/test-api.sh` para a API e manter o comando de teste web. CI da API usa o mesmo runner com Docker disponível. Adicionar `make test-api` com suporte a argumentos em `PYTEST_ARGS`; `PYTEST_ARGS='apps/api/tests/test_database.py' make test-api` deve passar.
- [ ] **Step 6:** Conferir lockfile gerado e criar commit `build: add PostgreSQL migration and test foundation` quando autorizado.

### Task 2: Isolamento e contexto administrativo por tenant

**Files:** criar `db/models/identity/organization.py` (Tenant), `db/models/identity/access.py` (User e UserTenant), `db/models/registry.py`, os `__init__.py` desses pacotes, `domain/identity/context.py`, `domain/shared/errors.py`, migração `0002_tenant_isolation.py`, `apps/api/tests/test_tenant_isolation.py`, `apps/api/tests/test_model_registry.py`; completar `db/session.py`, `apps/api/migrations/env.py`, `apps/api/tests/factories.py`.

**Interfaces:** consumir engine da Task 1; produzir
`tenant_session(engine: Engine, context: AccessContext) -> AbstractContextManager[TenantSession]`.
Produzir `clinic_api.db.models.registry.register_models() -> None` para Alembic,
serviços e testes. Modelos desta task: `Tenant`, `User`, `UserTenant`.
Factory usa migrator: `factory.identity() -> AccessContext` cria usuário admin e
tenant; `factory.context_for(user_id: UUID, tenant_id: UUID) -> AccessContext` não concede acesso.

```python
def test_requires_active_admin_membership(factory, runtime_engine):
    permitted = factory.identity()
    other = factory.identity()
    forbidden = factory.context_for(permitted.user_id, other.tenant_id)
    with pytest.raises(AccessDenied):
        with tenant_session(runtime_engine, forbidden):
            pass
```

- [ ] **Step 1:** Testes: `test_requires_active_admin_membership` lança `AccessDenied` para usuário sem participação ativa; `test_cross_tenant_read_and_write` lê zero registros do outro tenant e rejeita insert com tenant errado; `test_pool_context_reset_after_exception` força pool de tamanho 1, aborta A e comprova que B só enxerga B; `test_missing_context_sees_no_business_rows` executa query runtime fora de contexto e recebe zero linhas. Em `test_model_registry.py`, `test_registered_models_match_migrated_tables` compara as tabelas de `Base.metadata` com as tabelas migradas do esquema, excluindo `alembic_version`, chama `register_models()` duas vezes e `configure_mappers()` sem erro; ampliar esse teste conforme as tasks acrescentem entidades.
- [ ] **Step 2:** Executar `PYTEST_ARGS='apps/api/tests/test_tenant_isolation.py' make test-api`; confirmar os testes vermelhos antes das políticas.
- [ ] **Step 3:** Usar `set_config(..., true)` por transação para `app.user_id` e `app.tenant_id`; conferir usuário, tenant e participação ativa admin antes de entregar sessão. Implementar RLS `ENABLE` e `FORCE`, `USING` e `WITH CHECK` nas tabelas de negócio. `user_tenants` permite ler apenas linhas do usuário corrente; demais políticas verificam tenant e participação ativa. `users` só expõe o próprio usuário e `tenants` apenas organizações autorizadas. Nesta entrega, provisionamento de tenants, usuários e participações ocorre com migrator; runtime tem somente SELECT nessas três tabelas, sem poder conceder acesso a si mesmo. Revogar CREATE de PUBLIC no esquema `public`; runtime recebe USAGE e os grants de dados necessários, nunca DDL ou bypass. Não usar variáveis de sessão persistentes nem deixar conexão autorizada após rollback.
- [ ] **Step 4:** Reexecutar Task 1 e 2 com `PYTEST_ARGS='apps/api/tests/test_database.py apps/api/tests/test_tenant_isolation.py apps/api/tests/test_model_registry.py' make test-api`; exigir sucesso e criar commit `feat(api): isolate administrative access by tenant` quando autorizado.

### Task 3: Cadastros e habilitações por clínica

**Files:** criar `db/models/catalog/people.py`, `db/models/catalog/affiliations.py`, `db/models/catalog/specialties.py`, `db/models/catalog/facilities.py`, `db/models/catalog/__init__.py`, `domain/catalog/clinics.py`, `domain/catalog/people.py`, `domain/catalog/rooms.py`, `domain/catalog/affiliations.py`, `domain/catalog/specialties.py`, `domain/catalog/lifecycle.py`, migração `0003_catalog.py`, `apps/api/tests/test_catalog.py`; estender `db/models/identity/organization.py` com `Clinic`, factories e `db/models/registry.py`.

**Interfaces:** produzir nos módulos de `domain/catalog/`:
`create_clinic(session: TenantSession, name: str, timezone: str, default_duration_minutes: int) -> UUID`,
`create_patient(session: TenantSession, name: str) -> UUID`,
`create_therapist(session: TenantSession, name: str) -> UUID`,
`create_specialty(session: TenantSession, name: str) -> UUID`,
`create_room(session: TenantSession, clinic_id: UUID, name: str) -> UUID`,
`set_affiliation(session: TenantSession, person_kind: Literal['patient', 'therapist'], person_id: UUID, clinic_id: UUID, active: bool) -> None`,
`set_specialty(session: TenantSession, resource_kind: Literal['therapist', 'room'], resource_id: UUID, specialty_id: UUID, active: bool) -> None`,
`set_active(session: TenantSession, entity: Literal['clinic', 'patient', 'therapist', 'specialty', 'room'], entity_id: UUID, active: bool) -> None`.

Localização: `create_clinic` em `clinics.py`; `create_patient` e `create_therapist`
em `people.py`; `create_room` em `rooms.py`; `set_affiliation` em `affiliations.py`;
`create_specialty` e `set_specialty` em `specialties.py`; `set_active` em `lifecycle.py`.

```python
def test_invalid_timezone_and_duration(factory, runtime_engine):
    context = factory.identity()
    with tenant_session(runtime_engine, context) as session:
        with pytest.raises(ValidationError):
            create_clinic(session, "Unidade", "Fuso/Inexistente", 30)
        with pytest.raises(ValidationError):
            create_clinic(session, "Unidade", "America/Sao_Paulo", 0)
```

- [ ] **Step 1:** `test_single_patient_in_two_clinics` afirma um ID com duas participações; `test_many_specialties_per_therapist_and_room` afirma duas habilitações distintas; `test_foreign_tenant_reference_is_rejected` espera erro de integridade e zero gravação; `test_invalid_timezone_and_duration` espera `ValidationError` para fuso desconhecido e duração 0; `test_inactivation_keeps_references` mantém relações após inativação.
- [ ] **Step 2:** Executar `PYTEST_ARGS='apps/api/tests/test_catalog.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Criar tabelas, chaves compostas e serviços; normalizar nomes de comparação por trim/casefold, preservando nome de exibição. Validar fuso por `zoneinfo.ZoneInfo`. Aplicar RLS da Task 2 às novas tabelas e conferir acesso admin em todas as operações.
- [ ] **Step 4:** Reexecutar os testes desta task e isolamento; criar commit `feat(api): add tenant clinic catalogs and affiliations` quando autorizado.

### Task 4: Planos de atendimento e disponibilidades vigentes

**Files:** criar `db/models/planning/treatment.py`, `db/models/planning/availability.py`, `db/models/planning/__init__.py`, `domain/planning/treatments.py`, `domain/planning/availability.py`, `domain/planning/time.py`, `domain/planning/types.py`, migração `0004_treatment_planning.py`, `apps/api/tests/test_planning.py`; estender `db/models/registry.py`.

**Interfaces:** produzir
`create_treatment_plan(session: TenantSession, patient_id: UUID, therapist_id: UUID, specialty_id: UUID, sessions_per_week: int, duration_minutes: int | None, valid_from: date, valid_until: date | None, clinic_ids: tuple[UUID, ...]) -> UUID`,
`add_availability(session: TenantSession, person_kind: Literal['patient', 'therapist'], person_id: UUID, clinic_id: UUID, window: WeekWindow) -> UUID`,
`add_clinic_hours(session: TenantSession, clinic_id: UUID, window: WeekWindow) -> UUID`,
`resolve_duration(session: TenantSession, treatment_plan_id: UUID, clinic_id: UUID) -> int`,
`end_treatment_plan(session: TenantSession, treatment_plan_id: UUID, valid_until: date) -> None`,
`local_interval(local_date: date, start: time, duration_minutes: int, timezone: str) -> tuple[datetime, datetime]`.

Localização: `create_treatment_plan`, `resolve_duration` e `end_treatment_plan`
em `domain/planning/treatments.py`; janelas e funcionamento em `availability.py`;
`local_interval` em `time.py`; `WeekWindow` em `types.py`.

```python
def test_timezone_conversion_and_dst_ambiguity():
    start, end = local_interval(date(2026, 10, 5), time(9), 30, "America/Sao_Paulo")
    assert start.astimezone(UTC) == datetime(2026, 10, 5, 12, tzinfo=UTC)
    assert end - start == timedelta(minutes=30)
    with pytest.raises(ValidationError):
        local_interval(date(2026, 3, 8), time(2, 30), 30, "America/New_York")
    with pytest.raises(ValidationError):
        local_interval(date(2026, 11, 1), time(1, 30), 30, "America/New_York")
```

- [ ] **Step 1:** `test_frequencies_are_per_specialty_not_per_clinic` cria planos de duas especialidades com 2 e 1 sessões e distribui o primeiro em duas clínicas sem virar frequência 4; `test_default_and_specific_duration` afirma 30 minutos padrão e override 45; `test_overlapping_plan_validity_rejected` espera erro, mas períodos adjacentes e especialidades diferentes são aceitos; `test_multiple_availability_windows` aceita manhã e tarde.
- [ ] **Step 2:** `test_timezone_conversion_and_dst_ambiguity` afirma UTC 12:00 para 09:00 em `America/Sao_Paulo` em 2026-10-05, e `ValidationError` para horário inexistente/ambíguo em transição DST; não escolher `fold` silenciosamente. Executar `PYTEST_ARGS='apps/api/tests/test_planning.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Implementar tabelas, vigências, exclusão GiST e funções. Validar frequência/duração positiva, dia 0–6, janelas e participação de ambos em cada clínica habilitada. Encerrar plano altera a vigência, preserva histórico e não modifica sessões futuras silenciosamente; elas requerem revisão explícita. Na conversão, duração em minutos representa tempo real decorrido; verificar round-trip de fuso e rejeitar ambiguidades.
- [ ] **Step 4:** Reexecutar planejamento e catálogo; criar commit `feat(api): add treatment plans and recurring availability` quando autorizado.

### Task 5: Horários semanais e identidade das ocorrências

**Files:** criar `db/models/planning/weekly.py`, `domain/planning/weekly.py`, migração `0005_weekly_slots.py` e `apps/api/tests/test_weekly_slots.py`; estender `db/models/registry.py`.

**Interfaces:** produzir
`add_weekly_slot(session: TenantSession, treatment_plan_id: UUID, clinic_id: UUID, room_id: UUID, weekday: int, start_time: time, valid_from: date, valid_until: date | None) -> UUID`,
`end_weekly_slot(session: TenantSession, slot_id: UUID, valid_until: date) -> None`,
`occurrence_dates(weekday: int, valid_from: date, valid_until: date | None, month: date) -> tuple[date, ...]`.

```python
def test_partial_month_dates():
    dates = occurrence_dates(0, date(2026, 1, 1), None, date(2026, 10, 1))
    assert dates == tuple(date(2026, 10, day) for day in (5, 12, 19, 26))
```

- [ ] **Step 1:** `test_slots_respect_global_weekly_frequency` permite duas vagas de um plano de frequência 2 entre duas clínicas e rejeita terceira vaga vigente; `test_slot_requires_common_availability_and_room` rejeita horário incompatível; `test_partial_month_dates` afirma que uma rotina de segunda em outubro de 2026 gera `(5, 12, 19, 26)` e não dias de setembro/novembro.
- [ ] **Step 2:** Rodar `PYTEST_ARGS='apps/api/tests/test_weekly_slots.py' make test-api`, confirmando falha.
- [ ] **Step 3:** Implementar rotina com duração efetiva, restrição de frequência em todas as vigências que se intersectam e validação de recursos. Impedir sobreposição dos padrões semanais de paciente, terapeuta e sala quando as vigências se cruzam, mesmo entre clínicas. Encerrar rotina não move sessões: a mudança é explícita e preserva IDs anteriores.
- [ ] **Step 4:** Executar testes desta task e planejamento; criar commit `feat(api): persist stable weekly scheduling patterns` quando autorizado.

### Task 6: Sessões, histórico e reservas concorrentes

**Files:** criar `db/models/scheduling/appointments.py`, `db/models/scheduling/__init__.py`, `domain/scheduling/appointments.py`, `domain/scheduling/types.py`, migração `0006_appointments.py`, `apps/api/tests/test_appointments.py`, `apps/api/tests/test_scheduling_concurrency.py`; estender `db/models/registry.py`.

**Interfaces:** produzir
`schedule_routine(session: TenantSession, slot_id: UUID, occurrence_date: date) -> UUID`,
`move_appointment(session: TenantSession, appointment_id: UUID, clinic_id: UUID, room_id: UUID, starts_at: datetime, outside_availability: bool, reason: str) -> None`,
`complete_appointment(session: TenantSession, appointment_id: UUID) -> None`,
`cancel_appointment(session: TenantSession, appointment_id: UUID, reason: str) -> None`.
Interno compartilhado: `validate_booking(session: TenantSession, treatment_plan_id: UUID, clinic_id: UUID, room_id: UUID, starts_at: datetime, duration_minutes: int, outside_availability: bool) -> None`.

Criar nesta task fixture `routine_appointment: tuple[AccessContext, UUID]`:
admin autorizado e sessão futura às 09:00, duração 30, clínica/sala habilitadas,
disponibilidades e funcionamento válidos. Factory usa migrator somente no setup.

```python
def test_completed_session_is_immutable(runtime_engine, routine_appointment):
    context, appointment_id = routine_appointment
    with tenant_session(runtime_engine, context) as session:
        complete_appointment(session, appointment_id)
        with pytest.raises(InvalidTransition):
            cancel_appointment(session, appointment_id, "Mudança indevida")
```

- [ ] **Step 1:** `test_adjacent_sessions_are_allowed` aceita 09:00–09:30 e 09:30–10:00; `test_move_preserves_occurrence_and_duration` muda data sem trocar slot/data de origem ou duração; `test_manual_exception_preserves_weekly_pattern` autoriza fora de disponibilidade com motivo, sem alterar rotina; `test_cancelled_session_releases_resources` permite outra reserva após cancelamento; `test_completed_session_is_immutable` espera `InvalidTransition` ao mover/cancelar.
- [ ] **Step 2:** `test_concurrent_patient_conflict_between_clinics` e `test_concurrent_room_conflict` usam duas conexões e barreira de threads, sem transação externa única: apenas um commit é bem-sucedido, o outro recebe `SchedulingConflict`, e não fica evento órfão. Rodar `PYTEST_ARGS='apps/api/tests/test_appointments.py apps/api/tests/test_scheduling_concurrency.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Criar sessões, histórico, FKs, exclusões e unicidade de ocorrência. Nesta migração, `origin` aceita somente `routine`; `replacement_due_id` e constraints de reposição são acrescentados na Task 7, depois de criar a tabela de dívidas. Serviço traduz violações conhecidas em erros de domínio. Registrar actor do contexto em cada alteração. Estado concluído é terminal, salvo entrega futura explícita de correção administrativa. Fora da disponibilidade não dispensa funcionamento ou bloqueios (adicionados na Task 8).
- [ ] **Step 4:** Executar os dois arquivos e testes de isolamento; criar commit `feat(api): add transactional appointments and conflict protection` quando autorizado.

### Task 7: Direitos e tentativas de reposição

**Files:** criar `db/models/scheduling/replacements.py`, `domain/scheduling/replacements.py`, `domain/scheduling/replacement_state.py`, migração `0007_replacement_dues.py`, `apps/api/tests/test_replacements.py`; estender `db/models/scheduling/appointments.py`, `domain/scheduling/appointments.py`, `domain/scheduling/types.py`, `db/models/registry.py`.

**Interfaces:** produzir
`record_absence(session: TenantSession, appointment_id: UUID, kind: AbsenceKind, decision: ReplacementDecision | None, reason: str) -> UUID | None`,
`decide_replacement(session: TenantSession, appointment_id: UUID, grant: bool, reason: str) -> UUID | None`,
`schedule_replacement(session: TenantSession, due_id: UUID, clinic_id: UUID, room_id: UUID, starts_at: datetime, outside_availability: bool, reason: str) -> UUID`,
`close_replacement(session: TenantSession, due_id: UUID, reason: str) -> None`.

Essas interfaces ficam em `domain/scheduling/replacements.py`. Helper interno
em `replacement_state.py`: `update_due_after_attempt(session: TenantSession, appointment_id: UUID) -> None`.
Ele sincroniza a dívida após realização, cancelamento, ausência ou dispensa da
tentativa, lendo estado/decisão e registrando a transição na mesma transação;
não abre outra dívida. Serviços de sessão e reposição o utilizam sem imports
circulares entre seus módulos principais.

```python
def test_therapist_absence_creates_one_due(runtime_engine, routine_appointment):
    context, appointment_id = routine_appointment
    with tenant_session(runtime_engine, context) as session:
        first = record_absence(session, appointment_id, AbsenceKind.THERAPIST, None, "Ausência")
        repeated = record_absence(session, appointment_id, AbsenceKind.THERAPIST, None, "Ausência")
        assert first is not None
        assert repeated == first
        assert session.scalar(select(func.count()).select_from(ReplacementDue)) == 1
```

- [ ] **Step 1:** `test_therapist_absence_creates_one_due` repete operação e afirma uma dívida; `test_patient_notice_requires_team_decision` deixa decisão pendente até grant e grava actor; `test_patient_no_notice_has_no_due` não cria dívida; `test_replacement_uses_original_therapist` mantém IDs originais; `test_completion_settles_due_not_weekly_quota` quita dívida sem alterar frequência/rotina.
- [ ] **Step 2:** `test_repeat_absence_reopens_same_due` falta do terapeuta na tentativa mantém uma dívida com duas sessões históricas; `test_no_notice_on_replacement_closes_due` encerra com motivo; `test_inactive_plan_preserves_but_blocks_due` mantém dívida e rejeita novo encaixe; `test_concurrent_replacement_attempts` permite somente uma tentativa ativa; `test_other_specialty_replacement_uses_freed_slot` realiza fono no horário da psicologia cancelada e afirma dívida de fono `completed`, psicologia `pending`. Rodar `PYTEST_ARGS='apps/api/tests/test_replacements.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Implementar dívida, adicionar `replacement_due_id` e ampliar `origin` para aceitar `replacement`. Criar índices parciais e trigger de origem. Alterar sessão e dívida na mesma transação; repetir a mesma decisão é idempotente, mas decisão contraditória após quitação lança `InvalidTransition`. Completar/cancelar tentativa atualiza a mesma dívida; cancelamento de tentativa sem perda de direito reabre. Encerrar com tentativa ativa cancela-a transacionalmente. Registrar motivo e actor, incluindo encerramento por falta sem aviso.
- [ ] **Step 4:** Reexecutar reposições, sessões e concorrência; criar commit `feat(api): track replacement rights and attempts` quando autorizado.

### Task 8: Fechamentos e ausências antecipadas

**Files:** criar `db/models/calendar/closures.py`, `db/models/calendar/person_blocks.py`, `db/models/calendar/__init__.py`, `domain/calendar/closures.py`, `domain/calendar/person_blocks.py`, `domain/calendar/queries.py`, migração `0008_calendar.py`, `apps/api/tests/test_calendar.py`; estender `db/models/registry.py` e integrar calendário a `domain/scheduling/appointments.py` e `domain/scheduling/replacements.py`.

**Interfaces:** produzir
`add_closure(session: TenantSession, clinic_id: UUID, starts_at: datetime, ends_at: datetime, reason: str) -> UUID`,
`add_person_block(session: TenantSession, person_kind: Literal['patient', 'therapist'], person_id: UUID, starts_at: datetime, ends_at: datetime, decision: ReplacementDecision | None, reason: str) -> UUID`,
`materialize_blocked_occurrence(session: TenantSession, slot_id: UUID, occurrence_date: date) -> UUID | None`.

`add_closure` fica em `domain/calendar/closures.py`; funções de ausência individual
em `person_blocks.py`. Em `queries.py`, produzir
`is_clinic_closed(session: TenantSession, clinic_id: UUID, starts_at: datetime, ends_at: datetime) -> bool`
e `is_person_blocked(session: TenantSession, patient_id: UUID, therapist_id: UUID, starts_at: datetime, ends_at: datetime) -> bool`;
essas consultas são usadas pela validação de agendamentos e pelo gerador.

```python
def test_closure_dispenses_routine_without_due(runtime_engine, routine_appointment):
    context, appointment_id = routine_appointment
    with tenant_session(runtime_engine, context) as session:
        appointment = session.get(Appointment, appointment_id)
        add_closure(session, appointment.clinic_id, appointment.starts_at, appointment.ends_at, "Recesso")
        session.refresh(appointment)
        assert appointment.status == AppointmentStatus.DISPENSED
        assert session.scalar(select(func.count()).select_from(ReplacementDue)) == 0
```

- [ ] **Step 1:** `test_closure_dispenses_routine_without_due` libera sessão futura e não cria dívida; `test_closure_reopens_existing_replacement_due` dispensa tentativa e reabre dívida; `test_early_therapist_absence_before_generation` materializa histórico e dívida sem agenda mensal; `test_block_without_planned_session_creates_no_due` não inventa atendimento; `test_closure_precedes_individual_absence` não cria dívida em feriado conhecido.
- [ ] **Step 2:** `test_late_closure_removes_unfulfilled_routine_entitlement` registra ausência antecipada e depois fechamento da mesma ocorrência: encerra dívida não quitada com motivo de dispensa, cancela tentativa futura se existir e não altera sessão já realizada; `test_manual_exception_cannot_bypass_block` espera `ValidationError`; `test_repeated_block_is_idempotent` afirma uma dívida por ocorrência. Rodar `PYTEST_ARGS='apps/api/tests/test_calendar.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Implementar bloqueios e interseção `[)`. Para pessoa, alcançar sessões existentes e slots vigentes no intervalo; ocorrência ainda não materializada vira histórico de ausência sem reserva. Fechamento dispensa rotina futura e reabre dívidas anteriores quando atinge tentativas. Preservar sessões realizadas e registrar histórico de toda dispensa/encerramento. Não gerar sessão para ocorrência suprimida por feriado ainda não materializada. Integrar essa validação a todos os novos encaixes.
- [ ] **Step 4:** Executar calendário, sessões e reposições; criar commit `feat(api): apply clinic closures and advance absences` quando autorizado.

### Task 9: Geração mensal incremental e diagnóstico de capacidade

**Files:** criar `db/models/scheduling/agendas.py`, `domain/scheduling/generation/service.py`, `domain/scheduling/generation/candidates.py`, `domain/scheduling/generation/diagnostics.py`, `domain/scheduling/generation/types.py`, migração `0009_monthly_generation.py`, `apps/api/tests/test_generation.py`; estender `db/models/registry.py`.

**Interfaces:** produzir
`GenerationResult(agenda_id: UUID, run_id: UUID, created_appointment_ids: tuple[UUID, ...], deficit_ids: tuple[UUID, ...])`,
`generate_month(session: TenantSession, clinic_id: UUID, month: date) -> GenerationResult`,
`list_current_deficits(session: TenantSession, agenda_id: UUID) -> tuple[GenerationDeficit, ...]`.
`GenerationDeficit` contém plano, início da semana, quantidade faltante, reason_code e details.

`generate_month` e `list_current_deficits` ficam em `generation/service.py`;
dataclasses e `DeficitReason` ficam em `generation/types.py`. `SlotCandidate` contém
`clinic_id`, `room_id`, `weekday`, `start_time` e `duration_minutes`.
Em `candidates.py`: `candidate_slots(session: TenantSession, treatment_plan_id: UUID, clinic_id: UUID, month: date) -> tuple[SlotCandidate, ...]`.
Em `diagnostics.py`: `diagnose_missing_slots(session: TenantSession, treatment_plan_id: UUID, clinic_id: UUID, week_start: date) -> tuple[DeficitReason, ...]`.
O serviço orquestra seleção, gravação e savepoints; os demais módulos não
confirmam transações nem geram sessões por conta própria.

Criar fixture `weekly_scenario: tuple[AccessContext, UUID]` com plano de uma sessão
por semana, slot segunda às 09:00, vigência cobrindo outubro de 2026, sem bloqueios
e recursos disponíveis das 08:00 às 12:00. O UUID identifica a clínica.

```python
def test_repeat_generation_preserves_manual_adjustments(runtime_engine, weekly_scenario):
    context, clinic_id = weekly_scenario
    with tenant_session(runtime_engine, context) as session:
        first = generate_month(session, clinic_id, date(2026, 10, 1))
        assert len(first.created_appointment_ids) == 4
        appointment = session.get(Appointment, first.created_appointment_ids[0])
        move_appointment(session, appointment.id, clinic_id, appointment.room_id,
                         appointment.starts_at + timedelta(minutes=1), False, "Ajuste")
        repeated = generate_month(session, clinic_id, date(2026, 10, 1))
        assert repeated.created_appointment_ids == ()
        assert appointment.manually_adjusted is True
        assert session.scalar(select(func.count()).select_from(Appointment)) == 4
```

- [ ] **Step 1:** `test_generation_builds_stable_weekly_pattern` gera horários iguais em todas as semanas elegíveis; `test_holiday_creates_no_appointment_or_deficit` não cria linha em feriado; `test_partial_capacity_returns_explicit_deficit` cria parte válida e identifica motivo; `test_repeat_generation_preserves_manual_adjustments` mantém IDs, histórico e data ajustada; `test_absence_is_not_refilled_as_routine` mantém falta e dívida sem nova sessão no horário antigo.
- [ ] **Step 2:** `test_cross_month_week_has_no_prorated_extra` mantém ocorrências naturais da semana; `test_frequency_is_shared_between_clinics` não duplica frequência; `test_concurrent_generation_is_idempotent` duas execuções não duplicam ocorrência; `test_existing_completed_replacement_is_preserved` mantém quitação; `test_room_and_availability_deficits_are_distinct` afirma reason_codes diferentes. Executar `PYTEST_ARGS='apps/api/tests/test_generation.py' make test-api` e confirmar falha.
- [ ] **Step 3:** Criar agenda/execuções/déficits e RLS. Serializar planejamento pelo tenant com `pg_advisory_xact_lock` também usado em mudanças de rotina. Normalizar mês para dia 1 e limitar datas pela vigência. Identidade de ocorrência usa slot/data esperada, nunca data ajustada. Gerar só slots da clínica selecionada, considerando slots/reservas de todas as clínicas ao controlar frequência e conflitos.
- [ ] **Step 4:** Para planos sem rotina suficiente, escolher vagas por busca gulosa determinística: planos com menos candidatos primeiro, desempate por ID; candidatos por dia, horário, clínica e sala. Buscar início em minutos inteiros nas interseções das janelas. Considerar reservas de todas as ocorrências do mês; ignorar dias de fechamento para capacidade e não construir novo padrão sobre ausência individual conhecida. Manter slots existentes; aceitar solução parcial sem promessa de ótimo. Aplicar a frequência global do plano em cada vigência antes de adicionar um slot.
- [ ] **Step 5:** Materializar sessões ou histórico de ausência antecipada apenas quando devido. Ocorrências já canceladas, faltantes, dispensadas ou movidas não são recriadas. Usar savepoints para um conflito esperado virar déficit sem desfazer outras sessões válidas. Déficits atuais são os da última execução bem-sucedida (`completed`/`partial`), sem acumular dívidas antigas de geração. Erro inesperado faz rollback da geração inteira; não publicar run `running` órfão.
- [ ] **Step 6:** Reexecutar geração, calendário e concorrência; criar commit `feat(api): generate monthly agendas incrementally` quando autorizado.

### Task 10: Migrações implantáveis e verificação completa

**Files:** modificar `compose.yaml`, `compose.dev.yaml`, `apps/api/Dockerfile`, `scripts/smoke.sh`, `.env.example`, `README.md`, `apps/api/README.md`, `docs/architecture/system-overview.md`; criar `scripts/bootstrap-db.sh` e `apps/api/tests/test_migrations.py`.

**Interfaces:** serviço Compose `db` com PostgreSQL 18; serviço `migrate` usa
`MIGRATION_DATABASE_URL` e executa `alembic upgrade head`; API usa apenas
`DATABASE_URL` do papel runtime. Migrações terminam antes de subir a API.
O bootstrap cria papéis/grants no banco novo, com valores fornecidos por ambiente;
não contém dados de pacientes ou credenciais reais versionadas.

```python
def test_runtime_cannot_migrate(runtime_engine):
    with pytest.raises(DBAPIError):
        with runtime_engine.begin() as connection:
            connection.execute(text("CREATE TABLE public.unauthorized_ddl (id integer)"))
```

- [ ] **Step 1:** `test_all_migrations_roundtrip` faz base → head → base → head em banco exclusivo e afirma todas as tabelas, RLS, exclusões e índices; `test_runtime_cannot_migrate` nega DDL; `test_database_migration_failure_prevents_api_start` é verificado no smoke com configuração deliberadamente inválida, sem deixar containers ativos.
- [ ] **Step 2:** Executar `PYTEST_ARGS='apps/api/tests/test_migrations.py' make test-api`, confirmando falha antes de completar deployment. A tabela Alembic e testes de catálogo do PostgreSQL devem mostrar papel runtime sem privilégios de dono, superuser ou BYPASSRLS.
- [ ] **Step 3:** Copiar Alembic/migrations para imagens development e runtime. Usar volume persistente do PostgreSQL e healthcheck `pg_isready`. `migrate` depende de banco saudável; API depende de migração bem-sucedida. URLs distintas por papel; credencial de migração não entra no ambiente da API. Não rodar migração no import ou a cada worker. No desenvolvimento preservar reload e volumes existentes.
- [ ] **Step 4:** Estender smoke para confirmar migração no container e acesso SQL runtime isolado, além das verificações web/HTTP atuais. Usar dados sintéticos descartáveis. Cleanup mantém `down --volumes --remove-orphans` no projeto exclusivo. Documentar instalação, migração, testes, variáveis e o estado entregue sem anunciar telas/endpoints inexistentes.
- [ ] **Step 5:** Executar `make check`, `make test`, `make build` e `make smoke`; exigir código de saída 0 em todos. Conferir `git diff --check`, diff e ausência de segredos. Criar commit `build: deploy clinic database migrations and verify integration` quando autorizado.

### Task 11: Consolidar documentação da entrega e referência para agentes

**Files:** consolidar `docs/database/schema.md`, `docs/database/operations.md`; atualizar `docs/database/README.md`, `docs/architecture/clinic-domain-modules.md`, `docs/architecture/clinic-database-diagrams.md`, `docs/agents/README.md`, `docs/agents/database-context.md`, `docs/business/README.md`, `docs/business/business-rules.md`, `docs/business/workflows.md`, `README.md`, `apps/api/README.md`.

**Interfaces:** dicionário físico verificável contra Alembic/metadata; instruções
operacionais reproduzíveis; mapa agente-friendly de regra → módulo → teste →
migração. Essa consolidação usa as atualizações feitas em cada task anterior.

- [ ] **Step 1:** Documentar todas as tabelas/colunas entregues, tipos, nulabilidade, padrões, PKs, FKs compostas, índices, checks, exclusões, estados e políticas RLS em `schema.md`. Indicar módulo proprietário, migração e regras RN correspondentes; não documentar tabelas futuras como existentes.
- [ ] **Step 2:** Documentar configuração dos papéis, bootstrap, upgrade/downgrade, execução de testes e comportamento dos volumes em `operations.md`, com os comandos efetivamente implementados nas Tasks 1 e 10. Atualizar os fluxos e a matriz de evidência regra/teste.
- [ ] **Step 3:** Atualizar o contexto dos agentes com interfaces, limites transacionais, leitura por assunto, testes específicos, migrações e estado entregue. Manter entradas curtas, links para fontes canônicas e IDs estáveis; não duplicar specs inteiras no contexto.
- [ ] **Step 4:** Conferir dicionário e diagramas contra metadata e migrações da Task 10, validar links locais e executar `git diff --check`. Verificar que todo domínio entregue tem referência funcional e técnica, e que nenhuma regra RN ficou sem evidência.
- [ ] **Step 5:** Solicitar autorização para commit `docs: consolidate clinic database and agent references`. Se esta consolidação revelar mudança de código, aplicar o ciclo de testes e repetir as verificações necessárias antes de declarar a entrega concluída.

## Matriz de cobertura das regras

| Regras | Tasks e evidência principal |
| --- | --- |
| RN-001, RN-003 | 2: RLS, participação admin e reutilização de conexão |
| RN-002, RN-004 | 3, 6: cadastros únicos, participações e recursos compatíveis |
| RN-005 a RN-008 | 4: vínculos, frequência, duração, vigência e janelas |
| RN-009, RN-010 | 5, 9: rotina estável e fronteira do mês |
| RN-011, RN-012 | 6, 8: validação e conflitos concorrentes entre clínicas |
| RN-013, RN-014 | 9: geração parcial, motivos e idempotência |
| RN-015, RN-016 | 6, 7: exceção manual, histórico e estados terminais |
| RN-017 a RN-020 | 8, 9: fechamentos, avisos e ausências antecipadas |
| RN-021 a RN-024 | 7: identidade da dívida, frequência e múltiplas tentativas |
| RN-025, RN-026 | 7, 8: nova falta, fechamento e condições inativas |

## Revisão do plano antes da execução

- [ ] Confirmar que as assinaturas utilizadas nas Tasks 5–9 correspondem às interfaces definidas acima.
- [ ] Confirmar que novas tabelas recebem RLS e FKs compostas na mesma migração que as cria.
- [ ] Confirmar que cada entidade está no pacote/módulo proprietário descrito na estrutura de arquivos e registrada para Alembic; executar `test_model_registry.py` ao acrescentar modelos.
- [ ] Confirmar que serviços e tipos estão nos pacotes proprietários de `domain`, sem módulos agregadores crescentes ou dependências circulares.
- [ ] Confirmar Task 0 e atualização documental em cada entrega; Task 11 consolida o realizado e o índice para agentes sem duplicar fontes canônicas.
- [ ] Confirmar que factories administrativas não são usadas para executar operações de domínio nos testes.
- [ ] Confirmar que testes concorrentes usam transações independentes e banco PostgreSQL real, sem SQLite ou mocks de exclusões.
- [ ] Confirmar que a leitura da agenda inclui sessões pelo mês/data atual, mas idempotência usa a ocorrência de origem.
- [ ] Confirmar que o deploy não fornece credenciais de migrator ao processo da API.

## Handoff

Método de execução escolhido pelo usuário em 2026-10-09: desenvolvimento com
subagentes, com implementador e revisão independente por task.

A implementação será retomada em uma próxima sessão, conforme solicitado pelo
usuário. Antes de iniciar, revisar o plano e carregar a skill
`subagent-driven-development`. Não iniciar produto ou instalar dependências
durante a etapa de plano.
