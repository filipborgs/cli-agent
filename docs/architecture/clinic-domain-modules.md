# Módulos de persistência e negócio da clínica

Persistência disponível: 21 tabelas com modelos ORM, Alembic até `0008_replacement_schema` e RLS administrativa: identidade e catálogo, planos e disponibilidades, rotina semanal, sessões e eventos, reposições.
A tabela abaixo descreve a organização prevista e entregue; consulte o
[dicionário](../database/schema.md) para o inventário implementado.
Serviços clínicos além dos casos de uso iniciais do catálogo são planejados.

## Limites por domínio

| Domínio | Modelos em `db/models/` | Serviços/tipos em `domain/` | Responsabilidade |
| --- | --- | --- | --- |
| Identidade e organização | `identity/organization.py`, `access.py` | `identity/context.py` | Tenant, usuário e contexto autorizado; clínica pertence ao catálogo. |
| Cadastros | `catalog/facilities.py`, `people.py`, `affiliations.py`, `specialties.py` | `catalog/clinic.py`, `patient.py`, `patient_clinic.py`, `therapist.py`, `specialty.py`, `room.py`, `types.py`, `ports.py` | Pessoas, unidades, salas e habilitações. |
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

`environment.py` centraliza os nomes (`EnvironmentVariable: StrEnum`) e todo
acesso ao ambiente Python. Os métodos de instância `.optional()` e `.required()`
aceitam `str` (default), `int` ou `bool`, com retorno inferido pelo tipo pedido,
e leem somente na chamada,
sem cache: ausente/vazio resulta em `None` no opcional ou `ValueError` seguro no
requerido. Conversões inválidas lançam `ValueError` seguro em ambos os métodos;
strings preservam espaços, inteiros usam base decimal e booleanos usam tokens
explícitos sem distinção de caixa e sem espaços externos.
`Settings`, Alembic e fixtures dependem desse módulo, sem acesso
direto ao SO. O [contrato de configuração](../database/operations.md#acesso-centralizado-ao-ambiente-python)
detalha chaves, overrides e validação; [test_environment.py](../../apps/api/tests/test_environment.py)
verifica métodos e inferência estática. Imports da API/health continuam sem exigir configuração.

`create_engine(database_url: str) -> Engine` cria conexões síncronas,
sem sessões/transações de tenant. `Settings` separa URL runtime da administrativa;
Alembic exige somente a administrativa. `Base: DeclarativeBase` centraliza a
metadata; `db/models/registry.py` importa explicitamente os modelos já entregues para manter a metadata coerente com as migrações. Seeds/limpeza administrativos
ficam em testes; o runtime não contorna RLS. Contratos/evidência:
[`test_database.py`](../../apps/api/tests/test_database.py),
[`test_settings.py`](../../apps/api/tests/test_settings.py) e
[operação](../database/operations.md). RN-001/RN-003 têm defesa por RLS administrativa, inclusive para usuário/tenant
inativos; serviços clínicos de agenda ainda não estão disponíveis.

Nomes físicos e estados estão no [dicionário](../database/schema.md); regras
funcionais estão nos [IDs RN](../business/business-rules.md). Contratos de serviço
devem ser descritos nesta página junto do módulo proprietário, indicando entradas,
retornos, limites transacionais e testes correspondentes.

Toda nova funcionalidade deve indicar seu domínio e módulo proprietário. Se
um módulo crescer com responsabilidades independentes, subdividi-lo dentro do
pacote e atualizar os imports, registro, testes e esta referência na mesma entrega.
Ao implementar interfaces, registrar aqui suas transações e ligações regra/teste,
mantendo detalhes consultáveis por assunto para agentes e revisores.

## Contratos dos modelos ORM

`db/models/common.py` define colunas comuns de tenant, timestamps e atividade.
Cada classe ORM usa a mesma `Base`; `register_models()` registra explicitamente
os módulos por domínio sem conectar ao banco. Os imports consumidores usam o
módulo proprietário. `Clinic`/`Room` ficam em `catalog/facilities.py`;
`Patient`/`Therapist` em `people.py`; participações em `affiliations.py` e
habilitações em `specialties.py`.

Modelos adicionais de `planning`, `calendar` e `scheduling` são entregues
conforme o inventário do dicionário; descrevem somente persistência.
As migrações são snapshots independentes dos modelos atuais. RLS, funções e
triggers são criados pelas migrações. A FK ORM de `Appointment` para
`ReplacementDue` usa `use_alter=True`; a referência inversa aponta para a
sessão original. A migração resolve explicitamente a ordem de criação/remoção.

[Dicionário](../database/schema.md) liga classe → migração → RN → teste e detalha
os locks FOR SHARE de integridade e as exclusões GiST. Não há sincronização
automática de dívida, geração de sessões ou auditoria por esses modelos.
Testes de schema por domínio e `test_model_registry.py` verificam os modelos
entregues; auditoria transversal adicional permanece planejada.
