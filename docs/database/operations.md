# Operação do banco de dados

A infraestrutura usa PostgreSQL 18, papéis separados, Alembic e testes reais.
O schema disponível contém 23 tabelas com modelos ORM, Alembic até `0009_calendar_schema` e RLS administrativa: identidade e catálogo, planos e disponibilidades, rotina semanal, sessões e eventos, reposições, calendário. Compose persistente de desenvolvimento,
serviço `migrate`, integração de startup e autenticação continuam planejados.
Veja o [schema](schema.md).

## Configuração e contratos

| Item | Contrato implementado |
| --- | --- |
| `DATABASE_URL` | URL SQLAlchemy `postgresql+psycopg://...` runtime; obrigatória ao carregar `Settings()` sem valor explícito. |
| `MIGRATION_DATABASE_URL` | URL administrativa; opcional para `Settings`, obrigatória para Alembic, sem fallback para runtime. |
| `clinic_runtime` | LOGIN, NOSUPERUSER, NOBYPASSRLS; sem propriedade/CREATE no esquema; somente SELECT nas identidades e DML nas tabelas de negócio sujeito a RLS. |
| `clinic_migrator` | LOGIN, NOSUPERUSER, BYPASSRLS; dono de `public` e tabelas; CREATE no banco para instalar a extensão confiável `btree_gist`. |

Os dois papéis não possuem CREATEDB, CREATEROLE ou REPLICATION. `PUBLIC` não tem
acesso ao esquema `public`; runtime recebe USAGE. Default privileges do migrator
cobrem tabelas futuras e sequências (USAGE/SELECT), mas `alembic_version` fica
sem grants runtime. Todas as tabelas de aplicação têm RLS forçada. O contexto existente usa
`tenant_session(engine, AccessContext)`, que valida participação administrativa
ativa e define `app.user_id` e `app.tenant_id` com `set_config(..., true)`
localmente à transação. Sem contexto não há linhas visíveis; rollback remove o
contexto antes de uma conexão retornar ao pool.

`Settings(database_url: str, migration_database_url: str | None)` permite valores
explícitos e lê as variáveis quando omitidos. `create_engine(database_url: str)`
retorna engine síncrono SQLAlchemy com `pool_pre_ping`; importar a API/health
não abre conexão nem exige essas variáveis. `.env.example` contém somente
exemplos locais; não é carregado automaticamente por `Settings`.

### Acesso centralizado ao ambiente Python

[`clinic_api/environment.py`](../../apps/api/src/clinic_api/environment.py) é o
único proprietário dos nomes de variáveis e do acesso a `os.environ`/`os.getenv`
no código Python da API, migrations e fixtures. `EnvironmentVariable(StrEnum)`
define as chaves `DATABASE_URL` e `MIGRATION_DATABASE_URL`, com valores iguais
aos nomes externos existentes; declarações shell/Compose mantêm esse contrato.
Consumidores importam o enum em vez de repetir strings ou consultar o SO.

- `EnvironmentVariable.DATABASE_URL.required()` devolve `str`;
  `.optional()` devolve `str | None`. `.value` continua sendo o nome da chave,
  nunca o conteúdo do ambiente. Ambos os métodos leem a chave a cada chamada.
- O argumento posicional `value_type` aceita somente `str` (default), `int` e
  `bool`: `.required(int)` infere `int`, `.optional(int)` infere `int | None`,
  `.required(bool)` infere `bool` e `.optional(bool)` infere `bool | None`.
  Passar `str` explicitamente mantém os retornos de string correspondentes.
- Ausente ou igual a `""` resulta em `None` no opcional e `ValueError` no
  requerido, para todos os tipos. Conteúdo presente inválido lança `ValueError`
  em ambos: opcional não esconde erro de conversão como ausência.
- Inteiros usam `int(valor, 10)` (por exemplo, `"42"`, `" -12 "` e `"0"`);
  `"abc"`, `"1.5"` e `"0x10"` são inválidos. Booleanos removem espaços externos
  e ignoram caixa: `true/1/yes/on` viram `True`, `false/0/no/off` viram `False`;
  qualquer outro conteúdo é inválido. Não se usa `bool(string)`.
- Erros de conversão identificam chave e tipo esperado, sem conteúdo bruto;
  exceções subjacentes de conversão não aparecem no encadeamento exibido.
- Não há leitura no import, cache, carregamento de `.env`, normalização de
  espaços em strings ou validação da sintaxe da URL nesses métodos; strings não
  vazias são preservadas. A conexão continua sob responsabilidade do engine.
- `Settings` é uma dataclass frozen: suas fábricas de defaults chamam `.required()`
  para runtime e `.optional()` para migrations. Overrides explícitos
  dispensam a leitura da chave correspondente, inclusive `None` administrativo.
- Alembic chama somente `EnvironmentVariable.MIGRATION_DATABASE_URL.required()`;
  funciona sem `DATABASE_URL` e nunca a usa como fallback. O runtime não exige
  credencial administrativa nem a usa para suprir runtime ausente.
- Fixtures `admin_engine` e `runtime_engine` usam o mesmo método `.required()`
  e suas respectivas chaves. Testes alteram o ambiente usando o enum.

Evidências: [métodos e assertions de tipos](../../apps/api/tests/test_environment.py),
[Settings/import sem configuração](../../apps/api/tests/test_settings.py) e
[migrações com PostgreSQL real](../../apps/api/tests/test_database.py).
Valide também a inferência estática com
`uv run --project apps/api mypy --strict apps/api/src apps/api/tests/test_environment.py`.

## Runner descartável (local e CI)

Pré-requisitos: Docker/Compose disponíveis ao usuário, uv e Python 3.13.
Execute na raiz:

```bash
make test-api
PYTEST_ARGS='apps/api/tests/test_database.py' make test-api
PYTEST_ARGS='apps/api/tests/test_database.py -k runtime' make test-api
make test
```

`scripts/test-api.sh` usa `compose.test.yaml` com `postgres:18`, projeto exclusivo
por processo/sufixo aleatório, volume próprio e porta dinâmica ligada a
`127.0.0.1`. O healthcheck TCP evita o servidor temporário da inicialização.
Após readiness, o runner chama `scripts/bootstrap-db.sh`, exporta URLs próprias
e roda `uv run --project apps/api pytest -W error -v` com a pasta de testes
explícita. Credenciais `disposable_*_password` só servem a esse banco descartável.
Argumentos do shell são repassados a pytest. `make test` mantém os testes web.
A CI da API usa o mesmo runner em Ubuntu com Docker disponível.

O trap EXIT (incluindo INT/TERM) remove containers, rede e volumes após sucesso
ou falha. Não usa bancos/volumes de desenvolvimento. Fixtures aplicam `upgrade
head` com migrator e fazem TRUNCATE das tabelas de aplicação antes/depois de cada
teste com esse papel. `admin_engine`, `runtime_engine` e `factory: ClinicFactory`
são as interfaces de teste; seeds de identidade usam SQL, sem ORM.
Todos os testes da API passam pela limpeza; sem URLs, a execução direta falha
explicitamente, sem skip de persistência. Rodar testes concorrentes em processos
independentes significa usar um runner separado por processo; pytest-xdist no
mesmo banco ainda não é suportado.

## Bootstrap compartilhado de banco novo

Pré-requisitos: container PostgreSQL ativo, banco existente e acesso psql
administrativo local via `docker exec`. Exemplo, com credenciais locais:

```bash
POSTGRES_USER=postgres POSTGRES_DB=clinic \
MIGRATOR_PASSWORD=local_migrator_password RUNTIME_PASSWORD=local_runtime_password \
bash scripts/bootstrap-db.sh CONTAINER_ID
```

O script cria os papéis se ausentes, reaplica atributos/senhas, transfere `public`
ao migrator e configura grants/default privileges. Reexecutá-lo é possível, mas
rotaciona as senhas informadas. Seu alvo é o banco novo; não é ferramenta para
sanear memberships/grants arbitrários de instalações existentes. Provisionamento
persistente deve usar o mesmo contrato de papéis e privilégios.

## Alembic em um banco provisionado

Defina apenas a URL administrativa; a URL runtime não é necessária:

```bash
export MIGRATION_DATABASE_URL='postgresql+psycopg://clinic_migrator:local_migrator_password@localhost:5432/clinic'
uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
uv run --project apps/api alembic -c apps/api/alembic.ini current
# Destrutivo: remove todas as tabelas de aplicação, dados e btree_gist.
uv run --project apps/api alembic -c apps/api/alembic.ini downgrade base
uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
```

`head` é `0009_calendar_schema`; `current` mostra a revisão efetivamente
aplicada ao banco selecionado. Após downgrade para base só permanece bookkeeping
do Alembic. O caminho de migrations é relativo ao ini, independente do diretório
atual. Alembic carrega o registro ORM; revisar qualquer autogenerate manualmente:
políticas, funções, triggers e algumas expressões de índices/exclusões precisam
de operações explícitas e não são reconstruídos apenas pela metadata.

### Verificação do schema

Use `make test-api` ou filtre pelos testes `test_*_schema.py` já presentes.
O runner valida as migrações em banco descartável e remove seus volumes.
A auditoria transversal de todas as estruturas será acrescentada após as
migrações restantes. Serviços de negócio e startup persistente são planejados.

`make check`, `make test`, `make build` e `make smoke` validam a entrega
transversal. Smoke ainda comprova o contrato HTTP/containers existente; não
comprova startup integrado do banco nem serviços clínicos futuros.
