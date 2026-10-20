# Changelog

Todas as mudanças relevantes deste projeto são registradas aqui.

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) · Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Unreleased]

### Added
- Contexto do projeto em `docs/00-discovery/contexto-projeto.md` (fonte de verdade do produto).
- Spec Kit 1.2.3 (`.specify/`, comandos `/speckit-*` em `.claude/skills/`).
- Kit de contexto do método SDD: `CLAUDE.md`, `CONTRIBUTING.md`, playbook, guia de documentação, roadmap, template de ADR, estratégia de testes, template de PR.
- Gitflow: branches `main` e `develop`; hooks em `.githooks/` bloqueiam commit direto em `main`/`develop`, branch fora do padrão, `.env`/segredo staged e mensagem fora do Conventional Commits.
- Hook `UserPromptSubmit` do Claude Code com lembrete das regras do projeto.
- Diretrizes de UI baseadas no design system `../design-system/linear`, com as adaptações ao público em aberto.
- Insumo (proposta) para a constituição do projeto.
