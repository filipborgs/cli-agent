# Monorepo Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Entregar um monorepo executavel com SPA React, API FastAPI, containers, verificacoes automatizadas e documentacao orientada a agentes.

**Architecture:** O navegador acessa o container web, que serve a SPA e encaminha `/api` para o container da API. `pnpm` e `uv` permanecem responsaveis por seus ecossistemas, enquanto Make e Docker Compose oferecem os comandos compartilhados na raiz.

**Tech Stack:** Node 24 LTS, React, Vite, TypeScript, pnpm, Vitest, Testing Library, Python 3.13, FastAPI, uv, Ruff, mypy, pytest, Docker Compose, nginx e GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-06-monorepo-foundation-design.md`

## Global Constraints

- Usar Node 24 LTS no desenvolvimento, no CI e na imagem de build do web.
- Usar Python 3.13 no desenvolvimento, no CI e na imagem da API.
- Manter web e API independentes; o web consome apenas o contrato HTTP publico.
- Expor `GET /api/health` com status 200 e corpo exato `{"status":"ok"}`.
- Nao adicionar banco, autenticacao, roteador web, gerenciador de estado, biblioteca de consultas, kit visual, Playwright ou meta de cobertura.
- Instalar dependencias exclusivamente pelos lockfiles gerados por `pnpm` e `uv`.
- Nao versionar segredos; respostas HTTP nunca devem expor stack traces.
- Executar os processos finais sem root e manter dependencias de desenvolvimento fora das imagens finais.
- Manter `README.md` para entrada humana e `AGENTS.md` curtos e operacionais para agentes.
- Todos os comandos compartilhados devem estar disponiveis no `Makefile` raiz.

## Review Focus

- API indisponivel ou retornando status nao-2xx: o web deve mostrar o estado de falha sem expor detalhes internos; coberto na Task 2.
- Resposta 2xx com JSON malformado ou `status` inesperado: o cliente web deve rejeitar o contrato; coberto na Task 2.
- Componente desmontado com requisicao pendente: a requisicao deve ser abortada sem atualizar o estado desmontado; coberto na Task 2.
- Caminho desconhecido sob `/api`: o proxy deve preservar o caminho e devolver o 404 da API, sem servir `index.html`; coberto na Task 3.
- Falha ao iniciar ou tornar saudavel qualquer container: o smoke test deve falhar e sempre remover os recursos criados; coberto na Task 3.

---

### Task 1: API FastAPI e contrato de saude

**Files:**
- Create: `.gitignore`
- Create: `.editorconfig`
- Create: `apps/api/.python-version`
- Create: `apps/api/pyproject.toml`
- Create: `apps/api/uv.lock`
- Create: `apps/api/src/clinic_api/__init__.py`
- Create: `apps/api/src/clinic_api/main.py`
- Create: `apps/api/tests/test_health.py`

**Interfaces:**
- Consumes: nenhuma interface de aplicacao anterior.
- Produces: `clinic_api.main.app: FastAPI`, `HealthResponse(status: Literal["ok"])` e `GET /api/health -> 200 {"status":"ok"}`.

- [ ] **Step 1: Criar os arquivos basicos do repositorio**

Configurar `.editorconfig` para UTF-8, LF, newline final e espacos. Configurar `.gitignore` para excluir `.env`, `.venv`, `node_modules`, caches, cobertura, `dist` e artefatos locais, preservando `.env.example`. Definir `3.13` em `apps/api/.python-version`.

- [ ] **Step 2: Criar a configuracao minima do projeto Python**

Definir em `apps/api/pyproject.toml` o pacote `cli-agent-api`, `requires-python = ">=3.13,<3.14"`, layout `src` com backend Hatchling, dependencias de runtime `fastapi` e `uvicorn`, e grupo `dev` com `httpx`, `mypy`, `pytest` e `ruff`. Configurar pytest para `tests`, Ruff para Python 3.13 e mypy estrito sobre `src`.

- [ ] **Step 3: Gerar e validar o lockfile da API**

Run: `uv lock --project apps/api && uv sync --project apps/api --all-groups --frozen`

Expected: ambiente criado e todas as dependencias instaladas a partir de `apps/api/uv.lock`.

- [ ] **Step 4: Escrever os testes que definem o contrato HTTP**

Em `apps/api/tests/test_health.py`, importar `app` e usar `httpx.AsyncClient` com `httpx.ASGITransport(app=app)` e `base_url="http://test"` para consultar o contrato sem iniciar um servidor.

```python
def test_health_returns_ok() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_api_path_does_not_expose_internal_details() -> None:
    response = client.get("/api/missing")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}
    assert "traceback" not in response.text.lower()


def test_debug_mode_is_disabled() -> None:
    assert app.debug is False
```

- [ ] **Step 5: Executar os testes para confirmar a falha inicial**

Run: `uv run --project apps/api pytest apps/api/tests/test_health.py -v`

Expected: FAIL durante a importacao porque `clinic_api.main` ainda nao existe.

- [ ] **Step 6: Implementar a aplicacao e o endpoint minimo**

Criar `apps/api/src/clinic_api/__init__.py` vazio. Em `apps/api/src/clinic_api/main.py`, definir `HealthResponse(BaseModel)` com `status: Literal["ok"] = "ok"`, criar `app = FastAPI(title="Clinic API", debug=False)` e implementar `async def health() -> HealthResponse` registrado em `GET /api/health` com `response_model=HealthResponse`.

- [ ] **Step 7: Executar testes e verificacoes da API**

Run: `uv run --project apps/api pytest -v`

Expected: 3 tests passed.

Run: `uv run --project apps/api ruff format --check apps/api && uv run --project apps/api ruff check apps/api && uv run --project apps/api mypy apps/api/src`

Expected: todos os comandos terminam com exit code 0.

- [ ] **Step 8: Commitar a API**

```bash
git add .gitignore .editorconfig apps/api
git commit -m "feat(api): add health endpoint"
```

### Task 2: SPA React e estados da API

**Files:**
- Create: `.node-version`
- Create: `package.json`
- Create: `pnpm-workspace.yaml`
- Create: `pnpm-lock.yaml`
- Create: `apps/web/package.json`
- Create: `apps/web/index.html`
- Create: `apps/web/tsconfig.json`
- Create: `apps/web/tsconfig.app.json`
- Create: `apps/web/tsconfig.node.json`
- Create: `apps/web/vite.config.ts`
- Create: `apps/web/eslint.config.js`
- Create: `apps/web/.prettierrc.json`
- Create: `apps/web/src/api/health.ts`
- Create: `apps/web/src/App.tsx`
- Create: `apps/web/src/main.tsx`
- Create: `apps/web/src/styles.css`
- Create: `apps/web/tests/setup.ts`
- Create: `apps/web/tests/health.test.ts`
- Create: `apps/web/tests/App.test.tsx`

**Interfaces:**
- Consumes: `GET /api/health -> {"status":"ok"}` da Task 1.
- Produces: `getHealth(signal?: AbortSignal): Promise<HealthResponse>` e o componente `App`, com textos observaveis `Verificando API...`, `API operacional` e `Nao foi possivel conectar a API.`.

- [ ] **Step 1: Criar o workspace e a configuracao minima do web**

Definir Node `24` em `.node-version` e criar o `package.json` raiz privado com `packageManager: "pnpm@10.18.3"`. Incluir somente `apps/web` em `pnpm-workspace.yaml` e criar o projeto Vite sem roteador. Definir o nome `cli-agent-web` no `apps/web/package.json`, com scripts `dev`, `build`, `test` (`vitest run`), `lint`, `format`, `format:check` e `typecheck`; dependencias de teste devem incluir jsdom, Vitest e Testing Library. Configurar TypeScript estrito, titulo `Clinic` em `index.html` e o proxy Vite `/api -> http://api:8000` sem reescrever o caminho.

- [ ] **Step 2: Instalar dependencias e gerar o lockfile**

Run: `corepack enable && pnpm install --frozen-lockfile=false`

Expected: `pnpm-lock.yaml` criado na raiz e dependencias do workspace instaladas.

- [ ] **Step 3: Escrever os testes do cliente HTTP**

Em `apps/web/tests/health.test.ts`, simular `fetch` e cobrir:

```typescript
it("returns the valid health response", async () => {
  // fetch resolves with status 200 and { status: "ok" }
  await expect(getHealth()).resolves.toEqual({ status: "ok" });
});

it.each([
  [503, { status: "unavailable" }],
  [200, { status: "unexpected" }],
  [200, "not-an-object"],
])("rejects an invalid API response", async (status, body) => {
  // fetch resolves with the supplied status and body
  await expect(getHealth()).rejects.toThrow("Invalid health response");
});

it("normalizes malformed JSON as an invalid response", async () => {
  // response.json() rejects with SyntaxError
  await expect(getHealth()).rejects.toThrow("Invalid health response");
});
```

- [ ] **Step 4: Escrever os testes dos estados da tela**

Em `apps/web/tests/App.test.tsx`, mockar `getHealth` e verificar:

- promessa pendente mostra `Verificando API...`;
- resposta valida troca para `API operacional`;
- rejeicao mostra `Nao foi possivel conectar a API.` e nao mostra a mensagem original;
- `unmount()` antes da resolucao deixa o `AbortSignal` recebido por `getHealth` com `aborted === true`.

- [ ] **Step 5: Executar os testes para confirmar a falha inicial**

Run: `pnpm --dir apps/web test`

Expected: FAIL porque `src/api/health.ts` e `src/App.tsx` ainda nao existem.

- [ ] **Step 6: Implementar o cliente HTTP**

Em `apps/web/src/api/health.ts`, exportar `interface HealthResponse { status: "ok" }` e `async function getHealth(signal?: AbortSignal): Promise<HealthResponse>`. Consultar `/api/health`, aceitar somente resposta HTTP bem-sucedida com objeto cujo `status` seja exatamente `ok`, e lancar `Error("Invalid health response")` para status nao-2xx, JSON invalido ou qualquer outro contrato. Preservar `AbortError` para o cleanup do componente.

- [ ] **Step 7: Implementar a tela e a entrada React**

Em `App.tsx`, renderizar o nome `Clinic`, iniciar no estado de carregamento, chamar `getHealth` com `AbortController` em um efeito, atualizar sucesso ou falha somente se o sinal nao estiver abortado e abortar no cleanup. `main.tsx` deve montar `App` em `#root`; `styles.css` deve centralizar um painel de status legivel em telas moveis e desktop, sem dependencia visual externa.

- [ ] **Step 8: Executar testes e verificacoes do web**

Run: `pnpm --dir apps/web test`

Expected: todos os testes passam.

Run: `pnpm --dir apps/web format:check && pnpm --dir apps/web lint && pnpm --dir apps/web typecheck && pnpm --dir apps/web build`

Expected: todos os comandos terminam com exit code 0 e `apps/web/dist` e criado.

- [ ] **Step 9: Commitar o web**

```bash
git add .node-version package.json pnpm-workspace.yaml pnpm-lock.yaml apps/web
git commit -m "feat(web): show API health status"
```

### Task 3: Containers, proxy e comandos raiz

**Files:**
- Create: `.dockerignore`
- Create: `.env.example`
- Create: `apps/api/.dockerignore`
- Create: `apps/api/Dockerfile`
- Create: `apps/web/Dockerfile`
- Create: `apps/web/nginx.conf`
- Create: `compose.yaml`
- Create: `compose.dev.yaml`
- Create: `scripts/smoke.sh`
- Create: `Makefile`

**Interfaces:**
- Consumes: `clinic_api.main:app`, build Vite e caminho `/api/health` das Tasks 1 e 2.
- Produces: web em `http://localhost:${WEB_PORT:-8080}`, API interna em `api:8000`, e alvos `make dev|format|check|test|build|smoke`.

- [ ] **Step 1: Escrever primeiro o smoke test executavel**

Criar `.env.example` com `WEB_PORT=8080`. Criar `scripts/smoke.sh` com `set -euo pipefail`, project name Compose exclusivo, `trap` que sempre executa `docker compose down --volumes --remove-orphans`, espera limitada por saude e estas assercoes:

```bash
curl --fail --silent "http://localhost:${WEB_PORT:-8080}/" | grep -q "Clinic"
test "$(curl --fail --silent "http://localhost:${WEB_PORT:-8080}/api/health")" = '{"status":"ok"}'
test "$(curl --silent --output /dev/null --write-out '%{http_code}' "http://localhost:${WEB_PORT:-8080}/api/missing")" = "404"
```

Se `docker compose up --build --wait` falhar ou exceder o timeout, o script deve retornar codigo diferente de zero depois do cleanup.

- [ ] **Step 2: Executar o smoke test para confirmar a falha inicial**

Run: `bash scripts/smoke.sh`

Expected: FAIL porque `compose.yaml` ainda nao existe.

- [ ] **Step 3: Criar a imagem da API**

Usar uma imagem uv com Python 3.13 para instalar do lockfile. Definir stages `development` e `runtime`; o runtime deve conter apenas dependencias de producao, copiar `src`, executar como usuario sem root e iniciar `uvicorn clinic_api.main:app --host 0.0.0.0 --port 8000`.

- [ ] **Step 4: Criar a imagem e o proxy do web**

Usar a raiz como contexto de build para acessar `pnpm-workspace.yaml` e `pnpm-lock.yaml`; `.dockerignore` raiz deve excluir artefatos locais. Usar Node 24 para os stages `development` e `build`, instalando com `pnpm install --frozen-lockfile`. O runtime deve usar nginx unprivileged, servir a SPA em 8080, encaminhar `/api/` para `http://api:8000` sem remover `/api`, retornar o `index.html` somente para rotas fora de `/api` e expor `GET /healthz` para seu proprio health check.

- [ ] **Step 5: Definir Compose de runtime e desenvolvimento**

Em `compose.yaml`, criar servicos `api` e `web`, usando `apps/api` como contexto da API e a raiz como contexto do web. Configurar rede interna, health checks e dependencia `web -> api` com `condition: service_healthy`; publicar somente `${WEB_PORT:-8080}:8080`. Em `compose.dev.yaml`, selecionar os stages `development`, montar os codigos e executar Uvicorn com `--reload` e Vite em `0.0.0.0:8080`; preservar o proxy `/api -> api:8000`.

- [ ] **Step 6: Criar a interface Make**

Implementar os seis alvos definidos na especificacao. `check` deve executar format-check, lint e tipos em ambas as stacks; `test` deve executar pytest e Vitest; `build` deve compilar o web, construir o pacote Python e executar `docker compose build`; `dev` deve usar os dois arquivos Compose; `smoke` deve chamar somente `scripts/smoke.sh`.

- [ ] **Step 7: Validar Compose e o fluxo completo**

Run: `docker compose config && docker compose -f compose.yaml -f compose.dev.yaml config`

Expected: ambas as configuracoes sao validas e somente o web publica porta no host.

Run: `make smoke`

Expected: pagina web responde, `/api/health` retorna o JSON exato, `/api/missing` retorna 404 e os containers sao removidos ao final.

- [ ] **Step 8: Confirmar cleanup tambem no caminho de falha**

Run: `WEB_PORT=0 make smoke`

Expected: FAIL com codigo diferente de zero; depois, `docker compose ls` nao lista o project name usado pelo script.

- [ ] **Step 9: Commitar a infraestrutura local**

```bash
git add .dockerignore .env.example Makefile compose.yaml compose.dev.yaml scripts apps/api/Dockerfile apps/api/.dockerignore apps/web/Dockerfile apps/web/nginx.conf
git commit -m "build: add containerized development workflow"
```

### Task 4: Documentacao orientada a pessoas e agentes

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`
- Create: `apps/api/README.md`
- Create: `apps/api/AGENTS.md`
- Create: `apps/web/README.md`
- Create: `apps/web/AGENTS.md`
- Create: `docs/architecture/system-overview.md`
- Create: `docs/decisions/0001-lightweight-polyglot-monorepo.md`
- Create: `docs/development/workflow.md`

**Interfaces:**
- Consumes: comandos e caminhos implementados nas Tasks 1-3.
- Produces: entrada humana pelo `README.md`, regras globais pelo `AGENTS.md` e instrucoes locais sem duplicacao.

- [ ] **Step 1: Escrever a entrada humana do repositorio**

Documentar no `README.md`: objetivo, escopo atual, pre-requisitos exatos, `make dev`, URL `http://localhost:8080`, todos os alvos Make, estrutura e links para arquitetura e workflow. Distinguir ambiente de desenvolvimento de `make smoke`.

- [ ] **Step 2: Escrever as instrucoes globais para agentes**

Manter `AGENTS.md` curto: mapa do repositorio, dependencia permitida `web -> HTTP -> api`, arquivos que nao devem ser editados manualmente (`pnpm-lock.yaml`, `uv.lock`), obrigacao de testes antes da implementacao, regra de commits pequenos (um unico objetivo testavel e revisavel por commit, sem agrupar entregas independentes) e comandos `make check`, `make test`, `make build` e `make smoke` antes da conclusao.

- [ ] **Step 3: Escrever documentacao especifica de cada aplicacao**

Os READMEs locais devem listar setup, comandos nativos e diagnostico. Os `AGENTS.md` locais devem registrar somente convencoes da stack: TypeScript estrito e testes comportamentais no web; layout `src`, tipos estritos e endpoint tests na API.

- [ ] **Step 4: Registrar arquitetura, decisao e workflow**

`system-overview.md` deve explicar componentes, proxy, fluxo de saude e limites adiados. O ADR 0001 deve registrar contexto, decisao por pnpm + uv + Make + Compose, alternativas Turbo/Nx e consequencias. `workflow.md` deve explicar ciclo TDD, atualizacao de lockfiles, verificacao por escopo e checklist de pull request.

- [ ] **Step 5: Validar a documentacao contra o repositorio**

Run: `make check && make test`

Expected: comandos documentados existem e terminam com exit code 0.

Run: `git diff --check`

Expected: nenhum erro de whitespace.

- [ ] **Step 6: Commitar a documentacao**

```bash
git add README.md AGENTS.md apps/api/README.md apps/api/AGENTS.md apps/web/README.md apps/web/AGENTS.md docs/architecture docs/decisions docs/development
git commit -m "docs: document architecture and agent workflow"
```

### Task 5: GitHub Actions e verificacao final

**Files:**
- Create: `.github/workflows/ci.yml`
- Modify: `docs/development/workflow.md`

**Interfaces:**
- Consumes: lockfiles e comandos das Tasks 1-4.
- Produces: checks nomeados `web`, `api` e `containers`, executados em pull requests e pushes para `main`.

- [ ] **Step 1: Criar os jobs independentes de web e API**

Configurar `ci.yml` para `pull_request` e push em `main`, usando `actions/checkout@v4`, `pnpm/action-setup@v4`, `actions/setup-node@v4`, `actions/setup-python@v5` e `astral-sh/setup-uv@v6`. O job `web` deve configurar pnpm pela versao declarada no `package.json`, Node 24 com cache pnpm, instalar com lockfile congelado e executar format-check, lint, typecheck, test e build. O job `api` deve configurar Python 3.13 e uv com cache, sincronizar pelo lockfile e executar Ruff format-check, Ruff lint, mypy e pytest.

- [ ] **Step 2: Criar o gate de containers**

Adicionar job `containers` com `needs: [web, api]`. Configurar nesse job Node 24, pnpm, Python 3.13 e uv antes de executar `make build` e `make smoke`; o proprio smoke test e responsavel pelo cleanup mesmo quando falhar.

- [ ] **Step 3: Documentar a protecao da branch**

Atualizar `docs/development/workflow.md` para exigir os checks `web`, `api` e `containers` na protecao de `main`. Registrar que essa configuracao deve ser aplicada no GitHub depois que o remote existir, pois nao e representada somente pelos arquivos do repositorio.

- [ ] **Step 4: Validar localmente os mesmos gates do CI**

Run: `make check`

Expected: formatacao, lint e tipos passam em web e API.

Run: `make test`

Expected: pytest e Vitest passam sem testes ignorados inesperadamente.

Run: `make build`

Expected: aplicacoes, pacote Python e imagens sao produzidos com exit code 0.

Run: `make smoke`

Expected: fluxo navegador-proxy-API passa e o ambiente e removido.

- [ ] **Step 5: Revisar artefatos e segredos antes do commit**

Run: `git status --short && git diff --check`

Expected: somente `ci.yml` e a atualizacao planejada do workflow estao pendentes; nenhum arquivo de ambiente real, `.venv`, `node_modules`, build local ou segredo aparece.

- [ ] **Step 6: Commitar o CI**

```bash
git add .github/workflows/ci.yml docs/development/workflow.md
git commit -m "ci: validate web API and containers"
```

- [ ] **Step 7: Verificar o historico e a arvore final**

Run: `git status --short && git log --oneline -6`

Expected: worktree limpo e cinco commits de implementacao acima do commit da especificacao.

- [ ] **Step 8: Aplicar protecao da branch quando houver remote GitHub**

No GitHub, marcar `web`, `api` e `containers` como checks obrigatorios para integrar em `main`. Se o remote ainda nao existir, registrar essa unica pendencia operacional no handoff sem afirmar que a protecao ja esta ativa.
