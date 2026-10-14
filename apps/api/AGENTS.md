# API Instructions

Mantenha codigo em `src/clinic_api`, tipos estritos e testes de endpoint em `tests`. Use `uv`, Ruff, mypy e pytest; nao exponha detalhes internos em respostas HTTP.

- Organize `db/models` e `domain` em pacotes por dominio, com modulos pequenos de responsabilidades relacionadas; consulte `docs/architecture/clinic-domain-modules.md` a partir da raiz.
- Para persistencia e agenda, leia `docs/agents/database-context.md` e atualize a documentacao de negocio, schema, contratos e operacao afetados na mesma entrega.
