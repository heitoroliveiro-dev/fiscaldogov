# Transparência do Congresso (nome provisório)

Site para o eleitor comum acompanhar, pelo celular e com linguagem simples, a atuação de deputados federais e senadores a partir dos dados abertos oficiais da Câmara e do Senado — com fonte e metodologia de cada número.

**Status:** Fase 1 — Arquitetura. Ainda não há código de aplicação. Stack: [ADR-0001](docs/01-architecture/adr/adr-0001-stack.md).

## Primeiros passos (todo clone)

```bash
git switch develop
git config core.hooksPath .githooks   # ativa os hooks de gitflow, segredos e Conventional Commits
```

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
