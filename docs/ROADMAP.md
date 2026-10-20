# Roadmap — Transparência do Congresso

> Mantenha "Onde estou agora" curto e sempre verdadeiro. Detalhe de cada entrega vive em `specs/`, no PR e no `CHANGELOG.md` — não aqui.

## Onde estou agora

**Fase atual:** F2 — Fundação técnica · **Próximo marco:** M1 — Câmara no ar (proposto)
**Próxima ação:** especificar a F2 pelo fluxo SDD (`/speckit-specify`).
**Prazo:** M1 até 31/01/2027 · **Ritmo planejado:** 8 h/semana · **Próximo checkpoint:** 23/11 (F2).
**Bloqueios:** nenhum. SP01 condiciona a RN03 (ver abaixo).

## O Norte

Dar ao eleitor comum, pelo celular, uma forma simples, neutra e verificável de saber como seus deputados e senadores atuam — sempre com o dado oficial a um clique.

## Etapas até o produto final

Capacidade: 8 h/semana (~115 h até 31/01/2027). Horas são estimativa de ordem de grandeza (2026-10-20). **Regra:** atraso de mais de 1 semana em um checkpoint obriga a reavaliar o escopo do M1 antes de seguir.

| # | Etapa | O que entrega | Horas | Checkpoint | Pronto quando | Status |
|---|---|---|---|---|---|---|
| F0 | Discovery | Contexto completo; fluxo do usuário; estudo de projetos semelhantes (R05) | 4–6 | 02/11 | §12 do contexto sem itens de especificação abertos | ✓ (nome definitivo segue aberto, não bloqueia) |
| F0.1 | Processo | Gitflow, Spec Kit, kit de contexto, hooks | — | — | Hooks bloqueiam `.env` e commit fora do padrão | ✓ |
| F0.2 | Constituição | `.specify/memory/constitution.md` | — | — | Ratificada | ✓ v1.0.0 |
| SP01 | Spike Câmara | Fontes de presença, justificativa e autoria | — | — | Relatório + decisões S1–S4 | ✓ |
| F1 | Arquitetura | ADR-0001 stack; ADR-0002 hospedagem; ADR-0003 domínio e adaptadores; modelagem de dados | 10–15 | 02/11 | Todo ADR crítico aceito com alternativas | ✓ 2026-10-20 |
| F2 | Fundação técnica | Scaffold com o design system, projeto do ETL, banco + migrations, CI, deploy de um "esqueleto" em produção | 15–25 | 23/11 | Página vazia no ar via CI; ETL grava um deputado com fonte e data | |
| F3.1 | ETL base da Câmara | Deputados, mandatos, partidos da 57ª (paginação, DA03) | 12–20 | 07/12 | Banco com os 513 deputados e mandatos da 57ª, conferidos contra a API | |
| F3.2 | HU01 Presença | Presença e justificativa (DA07), cálculo RN03–RN05 e RN08, ranking, link oficial (RN09) | 20–30 | 04/01 | Taxa de deputados de amostra confere com o cálculo manual documentado | |
| F3.3 | Perfil + home + metodologia | RF05 (troca de partido), RF06–RF08, RF09 (home com gráficos, RN10), RF10 (prévia de compartilhamento) | 19–31 | 18/01 | Toda tela de dado mostra fonte, link e data; metodologia publicada; link compartilhado mostra a prévia | |
| F4 | Operação mínima | CDN, monitor externo, alertas no Telegram (RNF02, RNF07) | 8–12 | 31/01 | Falha simulada do ETL chega no Telegram; site atrás de cache | |
| ⭐ M1 | **Câmara no ar** | Eleitor consulta a presença dos deputados da 57ª pelo celular, com metodologia e fonte | **89–140** | **31/01/2027** | Pessoa real sem conhecimento técnico responde "meu deputado comparece?" sem ajuda | |
| F5.1 | HU02 Propostas | Ranking por tipo, autoria, coautoria e apoios | 15–20 | pós-M1 | — | |
| F5.2 | 56ª legislatura | Carga histórica, lacuna de 2020 (S1), divergência de 2019 (S4) | 6–10 | pós-M1 | RNF10 completo | |
| F5.3 | HU03 Tramitação | Busca, detalhe, votos nominais | 25–35 | pós-M1 | — | |
| F5.4 | RN09 completa | Número oficial da Câmara lido diariamente | 6–8 | pós-M1 | — | |
| SP01-B | Spike Senado | Mesmas perguntas do SP01 para o Senado | — | antes de F6 | — | |
| F6 | Senado | Adaptador do Senado reutilizando o domínio (DA05) | — | — | Mesmas telas para senadores sem alterar o domínio | |
| ⭐ M2 | **Lançamento público** | Câmara completa + Senado | — | — | — | |

## Pendências antes do próximo marco

Espelha a §12 do contexto (a fonte é lá).

| # | Item | Origem | Triagem | Status |
|---|---|---|---|---|
| 1 | Nome definitivo do projeto | contexto §12 | decisão | aberto |
| 2 | Confirmar RN04–RN07 | contexto §7 | decisão | ✓ + RN08 |
| 3 | Validar critérios de aceite HU01–HU03 | contexto §6 | decisão (entra no `/speckit-specify`) | aberto |
| 4 | Requisitos não funcionais | contexto §8.2 | entrevista | ✓ RNF01–RNF10 |
| 5 | Restrições (prazo, orçamento, horas/semana) | contexto §12 | entrevista | ✓ §8.3 |
| 12 | Escopo mínimo do Marco 1 | R06 | decisão | ✓ contexto §4.1 |
| 6 | Diagrama de fluxo do usuário | contexto §12 | F0 | ✓ `docs/00-discovery/fluxo-usuario.md` |
| 7 | Modelagem de dados | contexto §12 | F1 | ✓ |
| 8 | Plano de arquitetura + definição da stack | contexto §12 | F1 (ADRs) | ✓ ADR-0001 a 0003 |
| 9 | Executar SP01 | contexto §10 | spike | ✓ Câmara |
| 13 | Decisões S1–S4 do SP01 | relatório SP01 | decisão | ✓ DA07, RN02, RN09 |
| 14 | SP01-B (Senado) | DA05 | spike | antes de F3.y |
| 10 | Estudar projetos semelhantes e definir diferencial | R05 | F0 | ✓ `docs/00-discovery/estudo-semelhantes.md` |
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
| Bot do Telegram para alertas | ⚠️ criação pelo responsável (BotFather) | Token + chat id como variáveis de ambiente | Alertas do RNF07 (F4) |
| Contas Cloudflare (Workers, R2, DNS) e token do GitHub para o ETL | ⚠️ criação pelo responsável | Publicação do site e backup (ADR-0002) | F2 (publicar o esqueleto) |

## Backlog futuro (fora do escopo atual)

- Assembleias legislativas estaduais — 27 fontes heterogêneas; reavaliar após MVP estável, começando pela ALMG.
- Ligação de um mesmo projeto entre Câmara e Senado — identificadores e fluxos diferentes; pós-MVP.
- Votações em comissões — distorcem comparações; pós-MVP.
- Métricas de alinhamento (fidelidade partidária, alinhamento com o governo, similaridade de votos) — substituem rótulo ideológico (DA04); priorizar após M1.
