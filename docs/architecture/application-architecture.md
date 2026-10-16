# Arquitetura de aplicação

## Dependências

```text
HTTP routes -> application use cases -> domain
                                      <- infrastructure adapters
```

O domínio é autocontido: não importa FastAPI, SQLAlchemy, PostgreSQL, sessão
ou modelos de persistência. Ele define entidades, regras, enums e portas.

## Camadas

| Camada | Responsabilidade |
| --- | --- |
| `api` | Traduz HTTP em comandos e respostas; não aplica regras de negócio. |
| `application` | Implementa use cases e coordena dependências. |
| `domain` | Entidades, invariantes, serviços, enums e protocolos. |
| `db` | Modelos SQLAlchemy, repositórios e migrações PostgreSQL. |

Rotas chamam use cases, nunca serviços de domínio diretamente. Use cases
dependem de portas do domínio; adaptadores em `db` as implementam.

## Catálogo

Cada entidade possui arquivo próprio no domínio, como `catalog/clinic.py`,
`catalog/patient.py` e `catalog/patient_clinic.py`. `Clinic`, `Patient` e
`PatientClinic` são entidades puras. Cada use case em `application/catalog`
possui módulo próprio, cria as entidades e chama `CatalogRepository`, a porta
de persistência.
`PersonKind` e `ResourceKind` são enums de domínio.

Use cases recebem `AccessContext` da composição na borda e obtêm dele o tenant
autorizado. Identificadores de tenant não são aceitos como entrada de comandos
HTTP nem de use cases.

`flush()` pertence ao adaptador de persistência: envia mudanças na transação
atual sem commit, permitindo que constraints e RLS falhem antes do fim do use
case. A unidade de trabalho decide commit ou rollback.
