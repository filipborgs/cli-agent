# Development Workflow

1. Escreva o teste que demonstra o comportamento e confirme a falha.
2. Implemente o minimo para torna-lo verde.
3. Rode verificacoes do escopo; antes de integrar, rode `make check`, `make test`, `make build` e `make smoke`.
4. Atualize lockfiles somente por `corepack pnpm install` ou `uv lock`.
5. Atualize documentacao quando limites, comandos ou decisoes mudarem.
6. Mantenha um objetivo testavel por commit.

Quando o remote GitHub existir, configure a protecao de `main` para exigir os checks `web`, `api` e `containers`. Essa configuracao e operacional e deve ser aplicada no GitHub; ela nao e representada apenas pelos arquivos do repositorio.
