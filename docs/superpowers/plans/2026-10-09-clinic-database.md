# Plano de banco de dados, migrações e modelos ORM

> **Para execução por agentes:** usar `executing-plans` ou o método de execução
> autorizado na sessão. Os checkboxes registram entregas e verificações deste plano.

**Objetivo:** entregar o schema PostgreSQL multi-tenant da clínica, sua evolução
por Alembic e os modelos SQLAlchemy correspondentes.

**Arquitetura:** PostgreSQL mantém integridade, isolamento e restrições de
concorrência. Alembic versiona o schema; os modelos ORM compartilham uma única
`Base.metadata` e registro explícito. Testes usam banco PostgreSQL descartável.

**Stack:** PostgreSQL 18, SQLAlchemy 2, Alembic 1, Psycopg 3, Python 3.13,
uv, pytest e Docker Compose para o ambiente de banco dos testes.

**Referências:** [desenho aprovado](../specs/2026-10-09-clinic-database-design.md),
[dicionário físico](../../database/schema.md),
[diagramas](../../architecture/clinic-database-diagrams.md) e
[regras RN-001 a RN-026](../../business/business-rules.md).
O desenho contém funcionalidades além deste plano; somente sua parte de
persistência pertence a esta entrega.

## Escopo

- Tabelas, colunas, tipos, defaults, nulabilidade e relacionamentos.
- PKs, FKs compostas, unicidade, checks, índices, exclusões e triggers de integridade.
- RLS, políticas e privilégios dos papéis de banco.
- Migrações incrementais, upgrade/downgrade e bootstrap de papéis.
- Classes ORM, metadata e registro dos modelos.
- Testes de schema, persistência ORM, integridade, isolamento e concorrência SQL.
- Documentação física e operação das migrações.

Não fazem parte deste plano: entidades puras de domínio, repositórios, casos de
uso, serviços de negócio, autenticação, endpoints, DTOs, telas, algoritmos de
geração de agenda, conversão de horários, decisões de reposição ou transições
orquestradas de sessões. Também fica fora a integração de startup/deploy da API.
O código dessas camadas já existente na branch permanece fora das entregas e
não deve ser removido pela execução deste plano.

As regras RN orientam o desenho dos dados. Ter tabelas e constraints não
significa que os fluxos correspondentes estejam implementados. Os testes deste
plano inserem dados diretamente por SQL/ORM, sem depender de serviços clínicos.

## Estado da branch em 2026-11-04

Branch de execução: `feat/clinic-database-schema`, criada a partir de `52f1a6d`.
As entregas abaixo foram registradas em oito commits incrementais autorizados
pelo usuário. Não há push ou merge desta entrega.

| Entrega | Estado atual | Evidência |
| --- | --- | --- |
| Fundação e identidade | Implementadas e revalidadas | Revisões existentes `0001_identity`, `0002_tenant_isolation`; defaults ORM alinhados |
| Catálogo | Schema e ORM completos | `0003_catalog` preservada; nova `0004_catalog_integrity` |
| Planejamento e rotina | Implementados | `0005_treatment_planning`, `0006_weekly_slots` |
| Sessões e reposições | Implementadas | `0007_appointments`, `0008_replacement_schema` |
| Calendário e agenda mensal | Estruturas implementadas | `0009_calendar_schema`, `0010_monthly_agenda_schema` |
| Documentação | Atualizada | Dicionário físico com 26 tabelas, operação, diagramas, arquitetura e índices |
| Revisão independente | Correção aplicada e verificada | Falha REPEATABLE READ reproduzida; regressão verde com FK declarativa |

As seis tabelas iniciais de catálogo foram completadas com associações, campos
comuns, FKs compostas e RLS administrativa. `catalog/entities.py` foi dividido
nos módulos proprietários. O adaptador existente teve apenas seus imports
atualizados; nenhum caso de uso ou serviço clínico novo foi criado.

Uma coluna gerada `replacement_due.original_origin = 'routine'` e uma FK para
a identidade da sessão incluindo sua origem impedem transformar a origem em
tentativa, inclusive sob snapshot antigo. Os triggers continuam complementares.
Esse ajuste resolve a falha encontrada pela revisão independente.

### Evidência de execução

- Baseline: 62 testes da API aprovados.
- Catálogo: 17 testes falharam pelas estruturas ausentes; primeira suíte verde
  com 79 testes aprovados.
- Planejamento/agenda/calendário/reposições: 27 testes falharam por schema
  ausente e passaram após as migrações.
- Auditoria: defaults ORM de identidade e erro de autorização do trigger foram
  corrigidos após falha; 54 testes de paridade/isolamento passaram.
- Qualificações, locks e unicidade concorrente de tentativas: 52 testes
  específicos aprovados com as coberturas adicionais.
- Revisão: regressão REPEATABLE READ falhou antes da FK discriminadora;
  60 testes de reposição, migração e isolamento passaram após a correção.
- Paridade das definições SQL: 6 testes de migrações aprovados, incluindo
  checks, exclusões e predicados de índices normalizados pelo PostgreSQL.
- Verificação final: `make check`, `make test`, `make build` e `make smoke`
  concluídos com código 0. `make test`: 180 testes da API e 9 do web aprovados.
- `git diff --check` aprovado e links locais conferidos em 12 documentos.
- Smoke cobre o contrato HTTP e os containers existentes; a validação do
  schema vem dos testes PostgreSQL, sem anunciar startup persistente da API.

### Decisões de execução

- Usar a branch nova nesta pasta, conforme autorização do usuário.
- Preservar migrações existentes e adicionar sete revisões encadeadas.
- Adicionar discriminador gerado e chave única para proteger a origem sob
  REPEATABLE READ; custo físico: uma coluna gerada e um índice único de suporte.
- Comparar definições SQL em tabelas temporárias para cobrir a paridade exigida;
  esse DDL é exclusivo dos testes.
- Manter índices separados para tentativas `scheduled` e `completed`, conforme
  contrato. Reconciliação dos estados e impedimento de ações de negócio após
  quitação dependem de serviços futuros.
- Autenticação, algoritmos de agenda, aplicação de calendário, transições e
  auditoria automática permanecem fora do escopo desta entrega.



Evidência utilizada para os commits: suíte final previamente aprovada: 180 testes API, 9 web; check/build/smoke com saída 0; sem nova execução, conforme solicitado.

## Restrições gerais

- Ler `AGENTS.md`, `apps/api/AGENTS.md` e as referências do assunto antes de editar.
- A API nunca depende do web. Este plano não altera `apps/web`.
- Preservar migrações existentes; corrigir o schema com novas revisões encadeadas.
  Os nomes sugeridos abaixo para migrações novas devem seguir o próximo número
  disponível, sem substituir `0001_identity`, `0002_tenant_isolation` ou `0003_catalog`.
- Usar nomes físicos singulares, conciliando o dicionário ainda parcialmente
  escrito no plural antes de criar cada conjunto de tabelas.
- IDs UUID; instantes concretos em `TIMESTAMPTZ`; intervalos de reserva `[)`.
  Vigências finais inclusivas devem ter representação equivalente nas exclusões.
- Toda referência de negócio inclui o tenant. Autores preservam vínculo histórico
  com `user_tenant`; não usar cascade delete que apague histórico clínico.
- Runtime não é dono do schema, não tem superuser, BYPASSRLS ou DDL.
- Novas tabelas recebem constraints, RLS e grants na mesma migração de criação.
- Testes de integridade antecedem mudanças de schema/modelos e devem falhar pelo
  contrato ausente antes da implementação. Usar PostgreSQL real, sem SQLite.
- Não editar lockfiles manualmente. Usar uv se for necessário regenerar o da API.
- Cada incremento inclui testes e documentação pertinente, com um objetivo por
  commit. Commits e pushes dependem da autorização vigente da sessão.

## Organização dos modelos ORM

Caminhos abaixo relativos a `apps/api/src/clinic_api/`:

| Módulo | Entidades |
| --- | --- |
| `db/base.py` | `Base` e convenções comuns de metadata |
| `db/models/identity/organization.py` | `Tenant` |
| `db/models/identity/access.py` | `User`, `UserTenant` |
| `db/models/catalog/facilities.py` | `Clinic`, `Room` |
| `db/models/catalog/people.py` | `Patient`, `Therapist` |
| `db/models/catalog/affiliations.py` | `PatientClinic`, `TherapistClinic` |
| `db/models/catalog/specialties.py` | `Specialty`, `TherapistSpecialty`, `RoomSpecialty` |
| `db/models/planning/treatment.py` | `TreatmentPlan`, `TreatmentPlanClinic` |
| `db/models/planning/availability.py` | `PatientAvailability`, `TherapistAvailability`, `ClinicHours` |
| `db/models/planning/weekly.py` | `WeeklySlot` |
| `db/models/calendar/closures.py` | `ClinicClosure` |
| `db/models/calendar/person_blocks.py` | `PersonBlock` |
| `db/models/scheduling/appointments.py` | `Appointment`, `AppointmentEvent` |
| `db/models/scheduling/replacements.py` | `ReplacementDue` |
| `db/models/scheduling/agendas.py` | `MonthlyAgenda`, `GenerationRun`, `GenerationDeficit` |
| `db/models/registry.py` | `register_models() -> None` com imports explícitos e idempotentes |

O catálogo existente será dividido por responsabilidade na Task 3, atualizando
seus imports consumidores sem mudar comportamento. Criar pacotes apenas quando
forem usados. `__init__.py` não agrega entidades nem inicia conexões.
Relacionamentos entre módulos devem evitar imports circulares em runtime.

## Contrato físico e verificação por incremento

O dicionário é a fonte de colunas, estados e constraints; não duplicar sua
definição completa neste plano. Antes de cada migração, detalhar o trecho
correspondente e conferir consistência com o desenho aprovado.

Para cada entrega:

1. Escrever testes de banco e confirmar falha pelo contrato ainda ausente.
2. Criar a migração e os modelos ORM correspondentes.
3. Atualizar o registro e conferir `configure_mappers()` e round-trip ORM.
4. Executar os testes específicos e `test_model_registry.py`, com saída 0.
5. Atualizar schema, diagramas e referências técnicas/operacionais afetadas.
6. Registrar evidências e preparar um commit coeso, conforme autorização.

Usar `PYTEST_ARGS='apps/api/tests/<arquivo>.py apps/api/tests/test_model_registry.py'
make test-api`. O runner cria banco descartável e remove seus volumes.
Não executar fixtures destrutivas contra banco persistente.

## Focos de revisão

- Uma referência válida em outro tenant deve ser rejeitada por FK composta,
  mesmo usando migrator que ignora RLS: Task 3 e teste comum nas tasks seguintes.
- Variáveis de contexto sem participação administrativa não autorizam DML:
  Tasks 2 e 3; repetir a matriz RLS em cada tabela nova.
- Reservas concorrentes de pessoas entre clínicas só permitem um commit:
  Task 6, com duas conexões e transações independentes.
- Adjacência de intervalos e vigências não deve ser tratada como sobreposição:
  Tasks 4 e 6, incluindo datas finais inclusivas.
- Ciclo de referências sessão/reposição e downgrade deve manter o schema
  consistente, sem metadata divergente: Tasks 7 e 10.

## Etapas

### Task 0: Referências de persistência

**Arquivos:** `docs/database/schema.md`, `docs/database/operations.md`,
`docs/architecture/clinic-database-diagrams.md`, `docs/agents/database-context.md`
e índices correspondentes.

- [x] Registrar desenho inicial e referências de banco.
- [x] Conciliar o estado documentado com as três migrações existentes e seus
  modelos, sem apresentar o catálogo parcial como completo.
- [x] Documentar nomes singulares e distinguir contratos planejados de schema
  efetivamente entregue. Manter progresso somente neste plano.

### Task 1: Fundação PostgreSQL e Alembic

**Arquivos existentes:** `apps/api/alembic.ini`, `apps/api/migrations/env.py`,
`apps/api/migrations/versions/0001_identity.py`, `db/base.py`, `db/session.py`,
`compose.test.yaml`, `scripts/test-api.sh`, `scripts/bootstrap-db.sh`,
`apps/api/tests/conftest.py`, `apps/api/tests/factories.py` e `test_database.py`.

- [x] Criar engine, metadata, configuração Alembic e migração inicial de identidade.
- [x] Criar runner descartável PostgreSQL 18 e bootstrap de papéis distintos.
- [x] Adicionar testes de upgrade → downgrade → upgrade e privilégios runtime.
- [x] Revalidar `PYTEST_ARGS='apps/api/tests/test_database.py' make test-api`;
  exigir retorno a base sem tabelas de negócio e recriação no head.

### Task 2: Identidade ORM e isolamento no banco

**Arquivos:** modelos de identidade e registro, revisão existente
`0002_tenant_isolation.py`, `test_tenant_isolation.py`, `test_model_registry.py`.
**Regras relacionadas:** RN-001 e RN-003.

- [x] Mapear `Tenant`, `User` e `UserTenant` e registrar modelos explicitamente.
- [x] Criar políticas RLS de identidade e restringir runtime a SELECT nessas tabelas.
- [x] Completar testes SQL para contexto ausente, usuário/tenant inativo,
  participação inativa ou inexistente e tentativa de escrita/provisionamento
  pelo runtime; verificar RLS habilitada e forçada e ausência de DDL/BYPASSRLS.
- [x] Revalidar os três arquivos de teste desta task e da Task 1. Conferir
  idempotência do registro e equivalência de tabelas ORM/migrações.

### Task 3: Completar schema e ORM do catálogo

**Arquivos:** módulos de catálogo da tabela acima, registro, nova migração
`0004_catalog_integrity.py` e `apps/api/tests/test_catalog_schema.py`.
**Regras relacionadas:** RN-001 a RN-004 e preservação de referências da RN-026.

- [x] Criar as seis tabelas e classes ORM iniciais do catálogo.
- [x] Escrever testes SQL/ORM para múltiplas clínicas por pessoa, múltiplas
  especialidades por terapeuta/sala, unicidade de nomes normalizados, duração
  positiva e preservação de referências ao inativar cadastros.
- [x] Adicionar testes que rejeitem referências entre tenants com migrator,
  e matriz de SELECT/INSERT/UPDATE/DELETE com runtime para cada tabela.
  Um contexto de tenant sem admin ativo deve negar acesso.
- [x] Confirmar falha com `PYTEST_ARGS='apps/api/tests/test_catalog_schema.py'
  make test-api` antes de completar o schema.
- [x] Criar `therapist_clinic`, `therapist_specialty` e `room_specialty`;
  adicionar chaves compostas, campos comuns ausentes, checks, índices,
  RLS com participação administrativa, grants e defaults previstos no dicionário.
- [x] Dividir `catalog/entities.py` nos módulos proprietários; atualizar imports,
  registro e mapear as novas associações. Comparar tipos, nulabilidade,
  defaults e constraints ORM com a migração.
- [x] Executar testes de catálogo/schema, identidade e registro e atualizar
  dicionário e diagramas antes de encerrar o incremento.

### Task 4: Planos de atendimento e disponibilidades

**Arquivos:** `db/models/planning/treatment.py`, `availability.py`, registro,
`0005_treatment_planning.py` e `apps/api/tests/test_planning_schema.py`.
**Regras relacionadas:** RN-005 a RN-008.

- [x] Escrever testes para frequência/duração positivas, duração opcional,
  vigência válida, dia 0–6, início de janela menor que fim e FKs entre tenants.
  Planos da mesma combinação paciente/terapeuta/especialidade não podem ter
  vigências sobrepostas; vigências adjacentes e especialidades distintas são aceitas.
- [x] Confirmar falha com o runner antes da migração.
- [x] Criar `treatment_plan`, `treatment_plan_clinic`, `patient_availability`,
  `therapist_availability` e `clinic_hours`, com exclusão GiST de vigências,
  chaves compostas, RLS e modelos ORM correspondentes.
- [x] Executar testes específicos, matriz RLS e registro; conferir em SQL a
  equivalência entre vigência inclusiva e range usado pela exclusão.

### Task 5: Persistência da rotina semanal

**Arquivos:** `db/models/planning/weekly.py`, registro,
`0006_weekly_slots.py` e `apps/api/tests/test_weekly_slot_schema.py`.
**Regras relacionadas:** suporte de dados para RN-009, RN-010 e RN-014.

- [x] Escrever testes para persistir `WeeklySlot`, recuperar sua vigência,
  rejeitar dia/duração/vigência inválidos e sala de outra clínica ou tenant.
- [x] Confirmar falha antes de criar `weekly_slot` e seu modelo ORM.
- [x] Criar FKs compostas para plano, clínica e sala, checks, índices e RLS.
  Frequência global e escolha de horários não são implementadas nesta task.
- [x] Executar testes específicos, matriz RLS e registro; documentar a chave
  do slot que será referenciada pela ocorrência da sessão.

### Task 6: Sessões, eventos e reservas concorrentes

**Arquivos:** `db/models/scheduling/appointments.py`, registro,
`0007_appointments.py` e `apps/api/tests/test_appointment_schema.py`.
**Regras relacionadas:** restrições de RN-011, RN-012, RN-014 a RN-016.

- [x] Escrever testes para estados/origem válidos, duração e intervalo positivos,
  coerência plano/paciente/terapeuta/especialidade e sala/clínica, referência de
  autor no mesmo tenant e persistência JSONB dos eventos.
- [x] Testar unicidade de `(tenant_id, weekly_slot_id, occurrence_date)` mesmo
  após mudança do intervalo ou estado, sem executar serviço de reagendamento.
- [x] Testar exclusões por paciente, terapeuta e sala, inclusive entre clínicas:
  intervalos adjacentes são aceitos; sobrepostos em `scheduled`/`completed`
  são rejeitados; estados sem reserva liberam o horário preservando a linha.
  Duas transações concorrentes devem permitir apenas uma reserva conflitante.
- [x] Confirmar falha; criar `appointment` e `appointment_event`, modelos ORM,
  checks, FKs compostas, exclusões parciais GiST, índices e RLS.
  Adicionar campos e checks de reposição na Task 7, quando existir a dívida.
- [x] Criar triggers de integridade de novas reservas para clínica habilitada,
  terapeuta habilitado e sala compatível, conforme dicionário; testar rejeição
  e preservação do histórico quando cadastros forem inativados.
- [x] Executar testes de sessões/schema, concorrência, matriz RLS e registro.

### Task 7: Dívidas e tentativas de reposição

**Arquivos:** `db/models/scheduling/replacements.py`, `appointments.py`, registro,
`0008_replacement_schema.py` e `apps/api/tests/test_replacement_schema.py`.
**Regras relacionadas:** suporte de dados para RN-021 a RN-026.

- [x] Escrever testes para uma dívida por sessão original, origem restrita a
  sessão de rotina, vínculo/tenant coerentes e checks dos estados persistidos.
- [x] Testar uma tentativa `scheduled` e uma `completed` por dívida por índices
  parciais, incluindo inserções concorrentes e rejeição de dívida filha.
- [x] Confirmar falha; criar `replacement_due`, FK de `appointment` para dívida,
  referência inversa à origem, checks de origem/ocorrência, índices e trigger
  de integridade da sessão original. Definir criação/remoção dessas FKs em
  ordem explícita para resolver o ciclo no upgrade/downgrade e no ORM.
- [x] Executar testes específicos, matriz RLS e registro. Não implementar
  concessão, agendamento, quitação ou reabertura automática da dívida.

### Task 8: Fechamentos e bloqueios individuais

**Arquivos:** modelos `calendar/closures.py`, `calendar/person_blocks.py`, registro,
`0009_calendar_schema.py` e `apps/api/tests/test_calendar_schema.py`.
**Regras relacionadas:** suporte de dados para RN-017 a RN-020.

- [x] Escrever testes para intervalos positivos, autor do mesmo tenant e
  exatamente uma pessoa por bloqueio (paciente ou terapeuta, nunca ambos).
- [x] Confirmar falha; criar `clinic_closure` e `person_block`, modelos ORM,
  FKs compostas, checks, índices de consulta temporal e RLS.
- [x] Executar testes específicos, matriz RLS e registro. Não materializar
  ausências, cancelar sessões ou gerar direitos como efeito desses registros.

### Task 9: Estruturas da agenda mensal e diagnóstico

**Arquivos:** `db/models/scheduling/agendas.py`, registro,
`0010_monthly_agenda_schema.py` e `apps/api/tests/test_agenda_schema.py`.
**Regras relacionadas:** suporte de dados para RN-013 e RN-014.

- [x] Escrever testes de mês no dia 1, unicidade tenant/clínica/mês, vínculo
  execução/agenda, contagem positiva de déficit, estados e motivos permitidos,
  JSONB e referências ao plano/execução no mesmo tenant.
- [x] Confirmar falha; criar `monthly_agenda`, `generation_run` e
  `generation_deficit`, seus modelos ORM, constraints, índices e RLS.
- [x] Executar testes específicos, matriz RLS e registro. Não implementar
  geração de sessões, seleção de vagas ou cálculo de déficits.

### Task 10: Validar cadeia de migrações e equivalência ORM

**Arquivos:** `apps/api/tests/test_migrations.py`, `test_model_registry.py`,
runner/bootstrap e documentação operacional quando necessário.

- [x] Criar teste base → head → base → head em banco exclusivo; conferir
  tabelas, FKs cíclicas, políticas, grants, exclusões, triggers e índices.
- [x] Ampliar o teste de equivalência além dos nomes de tabelas: comparar tipos,
  nulabilidade, defaults, PKs, FKs, checks e uniques ORM com o banco; verificar
  explicitamente objetos PostgreSQL mantidos somente pelas migrações, como RLS
  e triggers. `configure_mappers()` e registro repetido não devem falhar.
- [x] Testar round-trip ORM das entidades e runtime sem permissão de migrar,
  alterar schema ou assumir papel migrator. Usar conexão runtime direta para
  comprovar negação de DDL, sem depender de caso de uso.
- [x] Executar a suíte da API com `make test-api`. Antes de concluir mudanças
  transversais de infraestrutura, executar `make check`, `make test`,
  `make build` e `make smoke`, registrando resultados e bloqueios reais.

### Task 11: Consolidar documentação física

**Arquivos:** `docs/database/schema.md`, `operations.md`, `README.md`, diagramas,
mapa de modelos, índices humano/agentes e README da API afetados.

- [x] Documentar cada tabela entregue com tipos, nulabilidade, defaults,
  PKs/FKs, checks, índices, exclusões, triggers, RLS e migração proprietária.
- [x] Conferir diagramas contra schema e ORM, mantendo nomes físicos coerentes.
- [x] Documentar bootstrap, papéis, URLs separadas e comandos de
  upgrade/downgrade e testes que realmente existem.
- [x] Distinguir schema disponível de fluxos ainda não implementados;
  não anunciar endpoints, serviços ou geração de agenda por existir uma tabela.
- [x] Conferir links locais, executar `git diff --check` e registrar a
  verificação final neste plano. Preparar commits por incremento autorizado.

## Critério de conclusão

O plano termina quando todas as estruturas aprovadas estiverem migradas e
mapeadas, testes de persistência e integridade tiverem resultado registrado e
a documentação refletir o banco entregue. A cobertura RN aqui se limita às
restrições e estruturas de dados; a cobertura integral dos comportamentos será
responsabilidade de planos futuros de aplicação.

Os oito commits incrementais foram autorizados. Push e merge continuam
fora do escopo autorizado.

## Sequência de commits autorizada

A sequência abaixo mantém um objetivo por incremento. Cada commit deve levar
sua fatia dos modelos, registro, testes e documentação; não incluir referências
a estruturas futuras como implementadas em snapshots intermediários.

1. `feat(db): complete tenant-safe catalog schema and ORM` — revisão 0004,
   divisão do catálogo, defaults de identidade e imports consumidores.
2. `feat(db): persist treatment plans and availability` — revisão 0005 e
   modelos/testes de planejamento.
3. `feat(db): persist weekly slots` — revisão 0006 e modelos/testes da rotina.
4. `feat(db): enforce appointment resource integrity` — revisão 0007,
   sessões/eventos, exclusões, trigger e testes de concorrência/qualificação.
5. `feat(db): constrain replacement ancestry and attempts` — revisão 0008,
   modelo da dívida, FK discriminadora, índices e regressão REPEATABLE READ.
6. `feat(db): persist clinic closures and person blocks` — revisão 0009,
   modelos e testes de calendário.
7. `feat(db): persist monthly agenda generation records` — revisão 0010,
   modelos e testes das estruturas de geração.
8. `test(db): verify migration and ORM contracts` — auditoria transversal,
   paridade de definições, consolidação documental e evidência final do plano.

Os commits são registrados na ordem acima; autorização de commit não implica push.
