# Transparência do Congresso (nome provisório)

Site para o eleitor comum acompanhar, pelo celular e com linguagem simples, a atuação de deputados federais e senadores a partir dos dados abertos oficiais da Câmara e do Senado — com fonte e metodologia de cada número.

**Status:** Fase 2 — Fundação técnica, em implementação ([specs/001-fundacao-tecnica](specs/001-fundacao-tecnica/tasks.md)). Stack: [ADR-0001](docs/01-architecture/adr/adr-0001-stack.md).

## Primeiros passos (todo clone)

```bash
git switch develop
git config core.hooksPath .githooks   # ativa os hooks de gitflow, segredos e Conventional Commits
```

## Rodar localmente

Requer Docker, Node 24 (`web/.nvmrc`) e [uv](https://docs.astral.sh/uv/).

```bash
docker compose up -d --wait                         # Postgres 18 com os papéis de desenvolvimento
export DATABASE_URL_DONO=postgresql://postgres:postgres@localhost:5432/fiscaldogov
npm --prefix web ci && npm --prefix web run db:migrate:deploy && npm --prefix web run db:generate

# site: com um dado fictício para ver a página
docker compose exec -T postgres psql -U postgres -d fiscaldogov < web/prisma/seed-e2e.sql
DATABASE_URL_LEITURA=postgresql://site_leitura:dev_site_leitura@localhost:5432/fiscaldogov \
  npm --prefix web run build                        # gera web/out/ (site estático)
npm --prefix web run test:e2e                       # Playwright + axe sobre o out/

# ETL: testes de unidade e arquitetura (integração: ver etl/README.md)
uv run --directory etl --frozen pytest -m "not integration"
```

Os testes do ETL (inclusive os de integração e o de backup) estão em [etl/README.md](etl/README.md). As travas do pre-commit e do CI estão em [CONTRIBUTING.md](CONTRIBUTING.md#hooks), e a operação em produção em [docs/05-runbooks/](docs/05-runbooks/).

## Como o projeto é conduzido

- **Metodologia:** Spec-Driven Development com GitHub Spec Kit — base em `../sdd-method/`. Comandos `/speckit-*` no Claude Code.
- **Branches:** Gitflow (`main`, `develop`, `feature/`, `bugfix/`, `chore/`, `release/`, `hotfix/`) — ver [CONTRIBUTING.md](CONTRIBUTING.md).
- **Design system:** `../design-system/linear` — ver [docs/06-design/diretrizes-ui.md](docs/06-design/diretrizes-ui.md).

## Onde está cada coisa

| Arquivo | Conteúdo |
|---|---|
| [docs/00-discovery/contexto-projeto.md](docs/00-discovery/contexto-projeto.md) | O que é o produto e por quê (fonte de verdade) |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Fases, marcos e pendências |
| [CLAUDE.md](CLAUDE.md) | Contexto lido pelo agente em toda sessão |
| [docs/PLAYBOOK-CONDUCAO.md](docs/PLAYBOOK-CONDUCAO.md) | Como conduzir o projeto com IA |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de mudanças |

## Fontes de dados

- Câmara dos Deputados — <https://dadosabertos.camara.leg.br/api/v2>
- Senado Federal — <https://legis.senado.leg.br/dadosabertos>

## Licença

[AGPL-3.0](LICENSE). Código e metodologia são abertos para que qualquer pessoa possa conferir como cada número é calculado.
