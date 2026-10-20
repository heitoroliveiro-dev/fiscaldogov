# Roadmap — Transparência do Congresso

> Mantenha "Onde estou agora" curto e sempre verdadeiro. Detalhe de cada entrega vive em `specs/`, no PR e no `CHANGELOG.md` — não aqui.

## Onde estou agora

**Fase atual:** F0 — Discovery (em andamento) · **Próximo marco:** M1 — Câmara no ar (proposto)
**Próxima ação:** fechar as pendências de especificação (§12 do contexto) — começando pelos requisitos não funcionais.
**Bloqueios:** nenhum. SP01 condiciona a RN03 (ver abaixo).

## O Norte

Dar ao eleitor comum, pelo celular, uma forma simples, neutra e verificável de saber como seus deputados e senadores atuam — sempre com o dado oficial a um clique.

## Etapas até o produto final

> Ordem das features e marcos são **proposta** até você confirmar.

| # | Etapa | O que entrega | Depende de | Pronto quando | Status |
|---|---|---|---|---|---|
| F0 | Discovery | Contexto completo: RNFs, RN04–RN07 confirmadas, critérios das HUs validados, restrições, fluxo do usuário | — | §12 do contexto sem itens de especificação abertos | em andamento |
| F0.1 | Processo | Repositório com gitflow, Spec Kit, kit de contexto, hooks de segredo/commit | — | Hooks bloqueiam `.env` e commit fora do padrão | ✓ |
| F0.2 | Constituição | `.specify/memory/constitution.md` v1.0.0 | F0.1 | Ratificada via `/speckit-constitution` | ✓ v1.0.0 |
| SP01 | Spike: ausência justificada | Resposta: as APIs informam justificativa de ausência? | — | Relatório com endpoints consultados e exemplos reais | |
| F1 | Arquitetura | ADR-0001 stack; ADR de domínio/adaptadores (DA02, DA03); ADR de hospedagem; ADR de frequência do ETL; modelagem de dados multi-legislatura (R03) | F0 | Todo ADR crítico aceito com alternativas | |
| F2 | Fundação técnica | Scaffold, design system aplicado, lint, hooks da stack, CI, banco + migrations, esqueleto do ETL e do adaptador da Câmara | F1 | App sobe, CI verde, ETL grava um deputado com fonte e data | |
| F3.x | Features Câmara | HU01 (presença), HU02 (propostas), HU03 (tramitação), RF05 (perfil), RF06–RF08 (metodologia, fonte, atualização) | F2 (HU01 também SP01) | Cada uma com spec, testes e evidência | |
| ⭐ M1 | **Câmara no ar** | Eleitor consulta presença, propostas e votos de deputados pelo celular, com link para a fonte | F3.x | Pessoa real sem conhecimento técnico responde "meu deputado comparece?" sem ajuda | |
| F3.y | Senado | Adaptador do Senado reutilizando o domínio (DA05) | M1 | Mesmas telas funcionam para senadores sem alterar o domínio | |
| F4 | CI/CD + deploy | Pipeline, deploy, rollback, ETL agendado com alerta (R02) | F3.x | Deploy com rollback provado; falha do ETL gera alerta | |
| ⭐ M2 | **Lançamento público** | Câmara + Senado em produção | M1, F3.y, F4 | — | |

## Pendências antes do próximo marco

Espelha a §12 do contexto (a fonte é lá).

| # | Item | Origem | Triagem | Status |
|---|---|---|---|---|
| 1 | Nome definitivo do projeto | contexto §12 | decisão | aberto |
| 2 | Confirmar RN04–RN07 | contexto §7 | decisão | aberto |
| 3 | Validar critérios de aceite HU01–HU03 | contexto §6 | decisão (entra no `/speckit-specify`) | aberto |
| 4 | Requisitos não funcionais | contexto §8.2 | entrevista | aberto |
| 5 | Restrições (prazo, orçamento, horas/semana) | contexto §12 | entrevista | aberto |
| 6 | Diagrama de fluxo do usuário | contexto §12 | F0 | aberto |
| 7 | Modelagem de dados | contexto §12 | F1 | aberto |
| 8 | Plano de arquitetura + definição da stack | contexto §12 | F1 (ADRs) | aberto |
| 9 | Executar SP01 | contexto §10 | spike | aberto |
| 10 | Estudar projetos semelhantes e definir diferencial | R05 | F0 | aberto |
| 11 | Adaptações do design system ao público (densidade, tema, cor) | `docs/06-design/diretrizes-ui.md` | decisão | ✓ D1–D5 decididas em 2026-10-20 |

## Pendências técnicas (achados de revisão)

| Prioridade | Achado | Risco | Status / PR |
|---|---|---|---|
| — | — | — | — |

## Pendências fora do código (⚠️)

| Item | Bloqueado por | O que desbloqueia | Impede o quê |
|---|---|---|---|
| Branch protection em `main`/`develop` no GitHub | ⚠️ configuração manual em Settings → Branches (sem `gh` nesta máquina) | Proteção real das branches no remoto | Hoje a proteção é só o hook local |
| Domínio do site | ⚠️ nome definitivo | Registro do domínio | M2 |

## Backlog futuro (fora do escopo atual)

- Assembleias legislativas estaduais — 27 fontes heterogêneas; reavaliar após MVP estável, começando pela ALMG.
- Ligação de um mesmo projeto entre Câmara e Senado — identificadores e fluxos diferentes; pós-MVP.
- Votações em comissões — distorcem comparações; pós-MVP.
- Métricas de alinhamento (fidelidade partidária, alinhamento com o governo, similaridade de votos) — substituem rótulo ideológico (DA04); priorizar após M1.
