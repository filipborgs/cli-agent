# Fundacao do monorepo web e API

**Data:** 2026-10-06
**Status:** Design aprovado

## Contexto

O produto sera uma aplicacao para clinicas gerenciarem atendimentos e
compatibilizarem as agendas de terapeutas e pacientes. Esta especificacao cobre
somente a fundacao tecnica do produto. As regras clinicas e de agendamento serao
definidas em especificacoes futuras.

O repositorio deve favorecer simplicidade, velocidade de desenvolvimento e
trabalho seguro por pessoas e agentes de IA. A fundacao precisa tornar os
limites dos componentes, os comandos de verificacao e as decisoes arquiteturais
faceis de localizar.

## Objetivos

- Criar um monorepo poliglota com uma SPA React e uma API Python independentes.
- Provar o fluxo completo do navegador ate a API por meio de um endpoint de
  saude.
- Oferecer desenvolvimento local e builds reproduziveis em containers.
- Estabelecer formatacao, lint, tipos, testes, build e smoke test desde o inicio.
- Executar todas as verificacoes obrigatorias em pull requests no GitHub.
- Documentar arquitetura, decisoes e workflows para reduzir convencoes
  implicitas.

## Fora do escopo

- Banco de dados e migracoes.
- Autenticacao e autorizacao.
- Multi-tenancy por clinica.
- Modelos de clinica, terapeuta, paciente, atendimento ou disponibilidade.
- Calculo e resolucao de conflitos de agenda.
- Filas, notificacoes e tarefas em segundo plano.
- Observabilidade de producao.
- Infraestrutura ou configuracao de um provedor de nuvem.

Esses itens serao introduzidos por especificacoes proprias. A fundacao nao deve
criar abstracoes vazias para acomoda-los antecipadamente.

## Abordagem escolhida

O repositorio usara uma abordagem poliglota leve. Cada aplicacao preservara as
ferramentas idiomaticas de seu ecossistema:

- `pnpm` para o web em TypeScript.
- `uv` para a API em Python.
- `Makefile` como interface pequena e estavel para tarefas que atravessam o
  repositorio.
- Docker Compose para executar e validar os servicos em conjunto.

Turborepo e Nx nao serao adotados nesta etapa. Cache distribuido, generators e
um grafo central de tarefas nao compensam sua configuracao adicional para dois
servicos. Essa decisao pode ser revista quando houver volume mensuravel de
pacotes ou gargalos nos builds.

## Arquitetura

O sistema tera dois servicos no mesmo repositorio:

```text
Navegador -> container web -> /api -> container api
```

O container web serve os arquivos estaticos da SPA e encaminha requisicoes em
`/api` para a API. Em desenvolvimento, o proxy do Vite preserva o mesmo caminho.
O navegador trabalha com uma unica origem no fluxo padrao, evitando uma
dependencia desnecessaria de CORS.

Os servicos possuem dependencias, builds, testes e imagens proprios. O web
depende somente do contrato HTTP publico da API, nunca de modulos Python. A API
nao depende de detalhes da interface React.

## Estrutura do repositorio

```text
/
  AGENTS.md
  README.md
  Makefile
  compose.yaml
  apps/
    web/
      AGENTS.md
      README.md
      src/
      tests/
    api/
      AGENTS.md
      README.md
      src/
      tests/
  docs/
    architecture/
    decisions/
    development/
    superpowers/
      specs/
```

Arquivos adicionais de configuracao, lockfiles e Dockerfiles permanecerao
proximos do escopo a que pertencem. Nao havera um pacote compartilhado ate
existir codigo realmente compartilhavel.

## Aplicacao web

O web usara React, Vite e TypeScript em modo estrito, sobre Node 24 LTS e
`pnpm`. A fundacao tera uma composicao minima da aplicacao e um cliente HTTP
pequeno para consultar `GET /api/health`.

A tela inicial apresentara estados explicitos de carregamento, sucesso e falha.
Nao serao adicionados roteador, gerenciador de estado, biblioteca de consulta de
dados ou kit visual antes de um fluxo de produto exigir essas dependencias.

Vitest e Testing Library cobrirao o comportamento observavel da tela. ESLint,
Prettier e o compilador TypeScript verificarao estilo, lint e tipos.

## API

A API usara FastAPI sobre Python 3.13. `uv` gerenciara o ambiente, as
dependencias e o lockfile. Ruff cuidara de lint e formatacao, mypy verificara os
tipos e pytest executara os testes.

`GET /api/health` respondera com status HTTP 200 e o corpo:

```json
{
  "status": "ok"
}
```

O endpoint servira a tela inicial, os testes de integracao e o health check do
container. O OpenAPI gerado pelo FastAPI sera a fonte do contrato HTTP nesta
etapa. Um cliente TypeScript gerado somente sera considerado quando os primeiros
contratos de dominio justificarem o custo.

Falhas esperadas retornarao JSON e codigos HTTP adequados. Erros inesperados
serao registrados no servidor, responderao sem stack trace ou detalhes internos
e nao impedirao o processo de continuar atendendo novas requisicoes quando isso
for seguro.

## Configuracao e segredos

Valores variaveis serao recebidos por ambiente. Arquivos de exemplo versionados
documentarao os nomes e valores seguros para desenvolvimento; segredos e
arquivos locais reais serao ignorados pelo Git.

As versoes de Node e Python serao declaradas no repositorio e usadas tambem nas
imagens e no GitHub Actions. Dependencias serao instaladas a partir dos
lockfiles, garantindo o mesmo conjunto em ambientes locais e no CI.

## Containers

Web e API terao Dockerfiles multi-stage e imagens finais independentes. Os
processos executarao sem privilegios de root quando suportado pelas imagens
base. As imagens finais conterao apenas artefatos e dependencias necessarios em
tempo de execucao.

O `compose.yaml` conectara os servicos por uma rede interna, publicara a entrada
do web e configurara health checks. O modo de desenvolvimento podera montar o
codigo e ativar recarga, enquanto o smoke test usara imagens construidas para
representar o caminho de execucao implantavel.

## Interface de desenvolvimento

O `Makefile` oferecera os seguintes alvos estaveis:

- `make dev`: inicia os servicos locais com recarga.
- `make format`: aplica os formatadores de ambos os servicos.
- `make check`: verifica formatacao, lint e tipos sem modificar arquivos.
- `make test`: executa os testes de ambos os servicos.
- `make build`: produz os builds e as imagens.
- `make smoke`: inicia as imagens e valida o web e a API pelo proxy.

Cada aplicacao tambem documentara seus comandos nativos para diagnostico e
trabalho isolado. Os alvos raiz nao esconderao erros nem implementarao logica de
negocio.

## Documentacao orientada a agentes

O `README.md` raiz sera a entrada para pessoas: objetivo, pre-requisitos, inicio
rapido, estrutura e comandos. O `AGENTS.md` raiz sera curto e operacional,
contendo o mapa do repositorio, limites entre servicos, verificacoes
obrigatorias e regras globais.

Cada aplicacao tera um `AGENTS.md` com somente as instrucoes especificas de sua
stack. Instrucoes locais complementam as globais e nao as duplicam. Os READMEs
locais explicarao execucao e diagnostico do componente.

- `docs/architecture` descrevera componentes, limites e fluxos de dados.
- `docs/decisions` guardara ADRs curtos para decisoes duraveis.
- `docs/development` documentara workflows que exigem contexto adicional.

Documentacao explicara intencao e operacao; configuracoes continuarao sendo a
fonte de detalhes mecanicamente verificaveis. Mudancas em comandos, limites ou
decisoes deverao atualizar a documentacao relacionada no mesmo pull request.

## Estrategia de testes

- Testes do web verificarao os estados de carregamento, sucesso e falha da tela
  sem depender de uma API real.
- Testes da API verificarao o endpoint de saude pelo cliente de testes do
  FastAPI.
- O smoke test construira e iniciara os dois containers, verificara a entrega da
  SPA e consultara a API atraves do proxy do web.
- Nao havera Playwright nem meta numerica de cobertura nesta etapa. Ambos serao
  considerados quando existirem fluxos de produto suficientes para tornar o
  investimento util.

## Integracao continua

O GitHub Actions executara em pull requests e na branch principal:

1. verificacoes e testes do web, com cache do `pnpm`;
2. verificacoes e testes da API, com cache do `uv`;
3. build das aplicacoes e imagens;
4. smoke test dos containers.

Os jobs independentes de web e API poderao rodar em paralelo. O build e o smoke
test somente iniciarao depois das verificacoes anteriores passarem. Formato,
lint, tipos, testes, build e smoke test serao gates de integracao.

## Criterios de aceite

A fundacao sera considerada pronta quando:

1. uma pessoa ou agente novo conseguir localizar as instrucoes relevantes a
   partir do `README.md` e do `AGENTS.md` raiz;
2. os pre-requisitos e comandos documentados forem suficientes para iniciar o
   ambiente sem conhecimento externo do repositorio;
3. a SPA abrir e exibir o sucesso ou a falha da consulta de saude da API;
4. `make check`, `make test`, `make build` e `make smoke` terminarem com sucesso
   em um checkout limpo;
5. o GitHub Actions executar as mesmas verificacoes e bloquear integracoes com
   falhas;
6. nenhum segredo, stack trace HTTP ou dependencia de desenvolvimento estiver
   presente nos artefatos finais;
7. os limites entre web e API e as decisoes adiadas estiverem documentados.

## Evolucao planejada

As proximas especificacoes deverao tratar separadamente persistencia,
identidade e acesso, multi-tenancy e o primeiro fluxo vertical do dominio. A
ordem sera decidida a partir do MVP do produto. Toda evolucao preservara, salvo
uma decisao arquitetural explicita, a dependencia unidirecional do web sobre o
contrato HTTP da API.
