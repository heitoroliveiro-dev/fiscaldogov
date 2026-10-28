# ETL — coleta dos dados oficiais

Coleta os dados da API da Câmara, grava no Postgres e dispara a publicação do site. Toda estatística é calculada aqui, nunca no site (ADR-0001). Arquitetura hexagonal: o domínio (`src/etl/dominio/`) não conhece as fontes nem o banco (ADR-0003); cada fonte é um adaptador em `src/etl/adaptadores/`.

Comandos e códigos de saída: [`specs/001-fundacao-tecnica/contracts/etl-cli.md`](../specs/001-fundacao-tecnica/contracts/etl-cli.md). Variáveis: [`etl/.env.example`](.env.example).

## Preparar o ambiente

Requer [uv](https://docs.astral.sh/uv/) (instala o Python 3.14 de `.python-version` se faltar).

```bash
cd etl
uv sync --frozen
```

## Testes de unidade e de arquitetura

Não precisam de banco nem de rede.

```bash
uv run --frozen pytest -m "not integration"
```

## Testes de integração

Rodam contra o Postgres local do `docker-compose.yml` (mesma major da produção), com as migrations do Prisma aplicadas e os três papéis de `scripts/dev-banco-papeis.sql`. Os testes de `tests/integracao/` usam transação desfeita ao fim, ou apagam o que gravaram quando testam o próprio COMMIT.

```bash
# na raiz do repositório
docker compose up -d --wait
DATABASE_URL_DONO=postgresql://postgres:postgres@localhost:5432/fiscaldogov \
  npm --prefix web run db:migrate:deploy

# em etl/
export DATABASE_URL_TESTE=postgresql://postgres:postgres@localhost:5432/fiscaldogov
export DATABASE_URL_ESCRITA_TESTE=postgresql://etl_escrita:dev_etl_escrita@localhost:5432/fiscaldogov
export DATABASE_URL_LEITURA_TESTE=postgresql://site_leitura:dev_site_leitura@localhost:5432/fiscaldogov
export ETL_EXIGIR_INTEGRACAO=1
uv run --frozen pytest
```

Senhas acima são só de desenvolvimento e CI; as de produção ficam nos cofres dos provedores.

- **Sem as variáveis de banco**, os testes de integração são pulados com a mensagem do motivo.
- **Com `ETL_EXIGIR_INTEGRACAO=1`** (o CI define), variável ausente é erro, nunca pulo: um teste mascarado não pode passar por verde (constituição, princípio III). Use-a sempre que for conferir a suíte completa.

## Lint e formatação

```bash
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```
