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

1. **pre-commit:** bloqueia commit direto em `main`/`develop` e branch fora do padrão → bloqueia `.env`/segredo staged.
2. **commit-msg:** Conventional Commits.

Lint, format e testes relacionados entram no pre-commit na F2 (fundação técnica), quando a stack estiver decidida.

Hook falhou? Conserte o problema. **Nunca** `--no-verify`.

## Fluxo

- Feature não trivial: SDD completo (ver `CLAUDE.md`).
- Bug de ~1 arquivo / CRUD trivial: trilha rápida (plan mode + teste + evidência).

## Definition of Done

Ver `CLAUDE.md` e o template de PR. Evidência anexada é obrigatória.
