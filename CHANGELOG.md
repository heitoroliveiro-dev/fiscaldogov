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
- ADR-0003: arquitetura hexagonal do ETL, identidade própria com reconciliação e falha fechada, auditoria de correções e de números publicados; modelagem de dados do Marco 1.
- ADR-0002: site estático na Cloudflare gerado após o ETL, ETL no cron do Railway, backup diário no R2.
- ADR-0001: stack (Next.js + Tailwind + Radix; Postgres + Prisma Migrate; ETL e estatísticas em Python).
- Estudo de projetos semelhantes e diferencial do projeto; licença AGPL-3.0 (DA08); RN11 (mediana da Câmara) e RN12 (período padrão).
- Fluxo do usuário do Marco 1 (`docs/00-discovery/fluxo-usuario.md`), com RF09, RF10 e RN10.
- Escopo do Marco 1 e roadmap com estimativas e checkpoints até 31/01/2027.
- Decisões S1–S4: DA07 (fonte da presença), coautoria só de proponentes com coluna de apoios (RN02), taxa oficial da Câmara ao lado (RN09).
- Regras de negócio RN04–RN07 decididas, RN02 detalhada e RN08 nova; SP01 ampliado.
- Requisitos não funcionais RNF01–RNF10 e restrições do projeto no contexto (entrevista de 2026-10-20).
- Adaptações do design system ao público decididas (D1–D5: texto 16px e alvos de 44px no mobile, tema do sistema operacional, marca violeta, efeitos só na landing).
- Fontes complementares avaliadas (contexto §5.1): Portal da Transparência como candidata para emendas parlamentares após o M1; Conecta gov.br e API dinâmica própria descartados.
