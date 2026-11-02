# Contribuindo com Transparência do Congresso

## Branches (Gitflow)

| Branch | Nasce de | Volta para | Para quê |
|---|---|---|---|
| `main` | — | — | Produção. Cada commit em `main` é uma versão publicada, com tag `vX.Y.Z`. |
| `develop` | `main` | — | Integração. Sempre deve compilar e passar nos testes. |
| `feature/NNN-nome` | `develop` | `develop` | Feature SDD. Mesmo `NNN-nome` da pasta `specs/NNN-nome/`. |
| `feature/<nome>` | `develop` | `develop` | Feature de trilha rápida. |
| `bugfix/<nome>` | `develop` | `develop` | Bug ainda não publicado em produção. |
| `chore/<nome>` | `develop` | `develop` | Tooling, dependências, docs. |
| `release/X.Y.Z` | `develop` | `main` **e** `develop` | Preparar versão: CHANGELOG, número de versão, só correções. Nada de feature nova. |
| `hotfix/X.Y.Z` | `main` | `main` **e** `develop` | Correção urgente de produção, com teste de regressão. |

`main` e `develop` são protegidas: sem commit direto, sem force push, merge só por PR com CI verde. O hook `pre-commit` bloqueia commit direto nelas e nomes de branch fora do padrão acima.

### Comandos (git puro — `git-flow` não é necessário)

```bash
# feature (SDD ou rápida)
git switch develop && git pull
git switch -c feature/001-nome-curto
# ... commits ... depois PR para develop (merge --no-ff)

# release
git switch develop && git pull
git switch -c release/0.1.0
# atualizar CHANGELOG ([Unreleased] → [0.1.0] - AAAA-MM-DD) e versão do projeto
# PR release/0.1.0 → main; após o merge:
git switch main && git pull && git tag -a v0.1.0 -m "v0.1.0" && git push origin v0.1.0
git switch develop && git merge --no-ff main     # devolve a release para develop (via PR, se a proteção exigir)

# hotfix
git switch main && git pull
git switch -c hotfix/0.1.1
# teste que reproduz o bug → fix → PR para main → tag v0.1.1 → merge de main em develop
```

## Versionamento

[SemVer](https://semver.org/lang/pt-BR/). Enquanto não houver lançamento público, versões `0.x.y`. A tag é criada **só** em `main`.

## Commits

Conventional Commits, validado no `commit-msg`:

```
<tipo>(escopo opcional): <descrição no imperativo, minúsculo, sem ponto final>
```

Tipos: `build`, `chore`, `ci`, `docs`, `feat`, `fix`, `perf`, `refactor`, `revert`, `style`, `test`. Commits de merge (`Merge ...`) são aceitos.

## Hooks

Ativar uma vez por clone:

```bash
git config core.hooksPath .githooks
```

1. **pre-commit**, nesta ordem:
   - bloqueia commit direto em `main`/`develop` e branch fora do padrão;
   - bloqueia `.env`/segredo staged;
   - com arquivo staged em `web/`: `lint-staged` (`web/.lintstagedrc.json`) roda ESLint com `--fix`, Prettier e `vitest related --run` só nos arquivos staged. O que dá para corrigir sozinho (formatação, parte do lint) é corrigido e volta para o stage; erro de lint ou teste quebrado bloqueia. Aviso de lint não bloqueia, como no CI;
   - com arquivo staged em `etl/`: `ruff format --check`, `ruff check` e `pytest -m "not integration"` (unidade + arquitetura). Aqui nada é corrigido sozinho: rode `uv run --directory etl ruff format` e faça o stage de novo. Essas três checagens olham a pasta inteira, não só o que está staged.
2. **commit-msg:** Conventional Commits.

Ferramenta ausente bloqueia o commit com a instrução (falha fechada): `npm --prefix web ci` para o site, [uv](https://docs.astral.sh/uv/getting-started/installation/) para o ETL. Os testes de integração (precisam de Postgres) rodam só no CI.

Hook falhou? Conserte o problema. **Nunca** `--no-verify`.

## Fluxo

- Feature não trivial: SDD completo (ver `CLAUDE.md`).
- Bug de ~1 arquivo / CRUD trivial: trilha rápida (plan mode + teste + evidência).

## Definition of Done

Ver `CLAUDE.md` e o template de PR. Evidência anexada é obrigatória.
