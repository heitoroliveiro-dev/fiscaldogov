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
- Constituição v1.0.0 ratificada (`.specify/memory/constitution.md`): 7 princípios, 3 inegociáveis.
- DA06 no contexto: produto é web responsivo, mobile-first, sem app nativo no MVP.
- Relatório do spike SP01 (Câmara): fontes de presença, justificativa e autoria.
- Regras de negócio RN04–RN07 decididas, RN02 detalhada e RN08 nova; SP01 ampliado.
- Requisitos não funcionais RNF01–RNF10 e restrições do projeto no contexto (entrevista de 2026-10-20).
- Adaptações do design system ao público decididas (D1–D5: texto 16px e alvos de 44px no mobile, tema do sistema operacional, marca violeta, efeitos só na landing).
