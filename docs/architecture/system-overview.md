# System Overview

O navegador acessa o web em 8080. Nginx entrega a SPA e encaminha `/api` para FastAPI em `api:8000`. `GET /api/health` retorna `{"status":"ok"}` e prova o caminho completo.

O web depende apenas do contrato HTTP da API. Persistência disponível:
12 tabelas com modelos ORM, Alembic até `0004_catalog_integrity` e RLS administrativa: identidade e catálogo.
Demais estruturas, autenticação e serviços clínicos continuam planejados.

O [desenho da agenda e do banco](../superpowers/specs/2026-10-09-clinic-database-design.md)
esta aprovado; startup persistente PostgreSQL e servicos de negocio continuam planejados. Consulte o
[mapa dos modulos](clinic-domain-modules.md), a [referencia do banco](../database/README.md)
e o [indice para agentes](../agents/README.md) para leitura direcionada.
