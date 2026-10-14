# Operação do banco de dados

Status: documentação operacional iniciada. Banco, papéis PostgreSQL, migrações
e comandos dedicados ainda serão implementados pelas Tasks 1 e 10 do
[plano](../superpowers/plans/2026-10-09-clinic-database.md).

## Comandos disponíveis hoje

Os comandos existentes do projeto são `make dev`, `make check`, `make test`,
`make build` e `make smoke`. Eles validam a fundação web/API atual; ainda não
comprovam persistência, isolamento de tenants ou geração de agenda.

## Configuração planejada

| Item | Finalidade prevista |
| --- | --- |
| PostgreSQL 18 | Banco compartilhado, com dados isolados por tenant. |
| `DATABASE_URL` | Conexão runtime, sem privilégios de migração ou BYPASSRLS. |
| `MIGRATION_DATABASE_URL` | Conexão administrativa exclusiva de bootstrap/migrações. |
| `clinic_runtime` | Papel de dados usado pela API e pelos testes de domínio. |
| `clinic_migrator` | Dono do esquema para migração e provisionamento administrativo. |
| Serviço Compose `migrate` | Aplica migrações antes de iniciar a API. |
| `make test-api` | Runner planejado de testes da API com PostgreSQL descartável. |

Estes itens descrevem o alvo do plano, não comandos/configurações já disponíveis.
Não colocar credenciais reais nos exemplos versionados.

## Procedimentos a completar na implementação

1. Documentar bootstrap de um banco novo, criação de papéis e grants.
2. Publicar comandos verificados para `upgrade`, consulta de revisão e `downgrade`.
3. Explicar acesso administrativo versus runtime e contexto de tenant por transação.
4. Explicar o volume persistente de desenvolvimento e a limpeza dos bancos descartáveis.
5. Documentar runner/fixtures, testes concorrentes e isolamento entre tenants.
6. Explicar dependências e falhas de startup do banco, migração e API.
7. Registrar evidência de `make check`, `make test`, `make build` e `make smoke`
   da entrega, sem transformar resultados de uma sessão em garantia permanente.

Cada procedimento deve incluir pré-requisitos, comando, resultado esperado e
efeito nos dados, com versões e variáveis efetivamente implementadas.
