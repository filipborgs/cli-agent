# System Overview

O navegador acessa o web em 8080. Nginx entrega a SPA e encaminha `/api` para FastAPI em `api:8000`. `GET /api/health` retorna `{"status":"ok"}` e prova o caminho completo.

O web depende apenas do contrato HTTP gerado pela API. Persistencia, identidade, multi-tenancy, agendas, notificacoes e observabilidade foram adiados para especificacoes proprias.

O [desenho da agenda e do banco](../superpowers/specs/2026-10-09-clinic-database-design.md)
esta aprovado; PostgreSQL e servicos de negocio continuam planejados. Consulte o
[mapa dos modulos](clinic-domain-modules.md), a [referencia do banco](../database/README.md)
e o [indice para agentes](../agents/README.md) para leitura direcionada.
