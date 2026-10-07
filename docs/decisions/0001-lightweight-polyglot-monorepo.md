# ADR 0001: Monorepo poliglota leve

## Contexto

O projeto combina React/TypeScript e Python/FastAPI, com prioridade para simplicidade.

## Decisao

Usar pnpm para web, uv para API, Make como interface comum e Docker Compose para integracao.

## Alternativas

Turborepo e Nx foram descartados nesta etapa por adicionarem configuracao e convencoes sem ganho proporcional para dois servicos.

## Consequencias

Cada stack permanece idiomatica; comandos compartilhados ficam estaveis no Makefile. Ferramentas centralizadas poderao ser reavaliadas quando houver mais pacotes ou custo mensuravel de builds.
