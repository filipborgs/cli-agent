# System Overview

O navegador acessa o web em 8080. Nginx entrega a SPA e encaminha `/api` para FastAPI em `api:8000`. `GET /api/health` retorna `{"status":"ok"}` e prova o caminho completo.

O web depende apenas do contrato HTTP gerado pela API. Persistencia, identidade, multi-tenancy, agendas, notificacoes e observabilidade foram adiados para especificacoes proprias.
