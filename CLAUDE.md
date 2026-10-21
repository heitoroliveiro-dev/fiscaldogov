# CLAUDE.md — Transparência do Congresso (nome provisório)

> Hub de contexto do projeto, lido pelo agente em toda sessão. **Máximo ~200 linhas e ~15 KB.** Este arquivo indexa, não duplica: detalhe vive em `docs/`, histórico em `CHANGELOG.md`, contrato de feature em `specs/`.

## O que é

Site que permite ao eleitor comum acompanhar, pelo celular e com linguagem simples, a atuação de deputados federais e senadores a partir dos dados oficiais das duas casas — de forma neutra e verificável.
Fonte de verdade do produto: `docs/00-discovery/contexto-projeto.md`.

## Stack (imutável sem ADR)

- **Site:** Next.js 16 + React 19 + TypeScript estrito + Tailwind v4 + Radix (design system). Só lê o banco, via Prisma, com papel só-`SELECT`.
- **Banco:** PostgreSQL (Railway). Schema e migrations: **Prisma 7** (`schema.prisma` é a fonte única).
- **ETL, domínio e estatísticas:** Python 3.14 + SQLAlchemy 2 Core (reflection) + psycopg 3. **Toda estatística é calculada só no Python** e gravada pronta.
- **Cache:** CDN. Sem Redis no M1.
- **Hospedagem:** site **estático** (`output: 'export'`) gerado após cada ETL e servido pela **Cloudflare**; build no GitHub Actions; ETL no **cron do Railway** (03:00 BRT); backup `pg_dump` → R2. Nada dinâmico no site.

Justificativa: `docs/01-architecture/adr/adr-0001-stack.md` e `adr-0002-hospedagem.md`.
- **Plataforma:** site web com domínio próprio, responsivo para computador e celular (mobile-first); sem app nativo no MVP (DA06).
- **Licença:** AGPL-3.0, código e metodologia abertos (DA08). Repositório público: segredo vazado é público na hora.
- **UI:** design system em `../design-system/linear` (Next.js + Tailwind v4 + Radix + shadcn/ui). Regras em `docs/06-design/diretrizes-ui.md`.

## Regras imutáveis (hard constraints)

- NUNCA commitar segredos (`.env`, chaves, tokens). Variáveis de ambiente.
- NUNCA SQL cru concatenado — query builder/ORM parametrizado.
- NUNCA commit direto em `main` ou `develop`; NUNCA force push nelas. Gitflow: ver `CONTRIBUTING.md`.
- NUNCA apagar branch sem confirmação.
- Todo dado exibido tem **fonte oficial + link para o registro original + data da última atualização** (OE04, RF07, RF08).
- **Neutralidade:** nenhum rótulo ideológico; posicionamento só por métricas derivadas de votos (DA04). Linguagem neutra.
- Toda estatística tem **regra pública** na página de metodologia e **teste automatizado** cobrindo os casos de borda (suplente, troca de partido, licença) — erro de dado vira acusação injusta (R01).
- Estatística por parlamentar é calculada sobre o **período em exercício do mandato** (DA03).
- Uma fonte de dados = um adaptador; o domínio não conhece o formato das APIs (DA02, ADR-0003). Nomes do domínio em português.
- Registro não reconciliado não entra no cálculo: falha fechada, nunca número parcial publicado (ADR-0003).
- Nenhuma feature não trivial sem o fluxo SDD (abaixo).

Constituição completa: `.specify/memory/constitution.md` (v1.0.0, ratificada em 2026-10-20). Manter coerente com esta lista — emenda e esta lista mudam no mesmo commit.

## Fluxo SDD (GitHub Spec Kit)

**Constitution → Specify → Clarify → Plan → Checklist → Tasks → Analyze → Implement**, depois review por subagente contra `plan.md`.

Não pular fase em feature não trivial. Bug de ~1 arquivo ou CRUD trivial no padrão existente: trilha rápida (plan mode + teste + evidência). Na dúvida, SDD. Triagem: `docs/PLAYBOOK-CONDUCAO.md`.

Branch da feature SDD: `feature/NNN-nome` criada a partir de `develop`, com o mesmo `NNN-nome` da pasta `specs/`.

## Definition of Done (todo merge)

- [ ] Testes passando; cobertura mínima de `docs/03-testing/estrategia-testes.md`
- [ ] Lint sem erros
- [ ] Nenhum segredo hardcoded
- [ ] Validação de entrada revisada nos pontos novos
- [ ] Fonte oficial + link + data de atualização em todo dado novo exibido
- [ ] Doc atualizada (ADR/README/runbook/CHANGELOG/contrato/metodologia)
- [ ] Review por subagente contra o `plan.md`
- [ ] Evidência anexada (output de teste, comando + retorno, screenshot)

## Verificação: evidência, não afirmação

Ao concluir, mostre evidência. Critérios checáveis ("a taxa do deputado X no período Y é 87,5% = 35/40 sessões"), nunca interpretáveis ("cálculo correto"). Proibido `skip`, assert removido ou teste afrouxado para passar. Todo bug corrigido ganha teste de regressão.

## Comandos

```
# hooks: git config core.hooksPath .githooks   (uma vez por clone)
# dev / test / lint / build / migrate / etl: definidos na F2 (stack: ADR-0001)
```

## Fase atual

- **Fase:** F2 — Fundação técnica. **Feature ativa:** `specs/001-fundacao-tecnica` (tarefas prontas, implementação em andamento).
- **Marco 1:** presença + perfil + metodologia, 57ª legislatura, até 31/01/2027 (contexto §4.1).
- **Próximo:** `/speckit-implement` da 001 — fase Foundational, depois US1 (ordem e progresso em `specs/001-fundacao-tecnica/tasks.md`).
- Histórico completo: `docs/ROADMAP.md` e `CHANGELOG.md` (não duplicar aqui).

## Índice de documentação (carregar sob demanda)

| Preciso de... | Vá para |
|---|---|
| O que o produto é | `docs/00-discovery/contexto-projeto.md` |
| Telas e navegação do Marco 1 | `docs/00-discovery/fluxo-usuario.md` |
| Concorrentes e diferencial | `docs/00-discovery/estudo-semelhantes.md` |
| Como conduzo o projeto | `docs/PLAYBOOK-CONDUCAO.md` |
| O que/onde/quando documentar | `docs/GUIA-DOCUMENTACAO.md` |
| Fases, marcos, pendências | `docs/ROADMAP.md` |
| Branches, commits, releases (gitflow) | `CONTRIBUTING.md` |
| Decisões de arquitetura | `docs/01-architecture/adr/` |
| Modelagem de dados | `docs/01-architecture/modelagem-dados.md` |
| Testes | `docs/03-testing/estrategia-testes.md` |
| UI/UX e design system | `docs/06-design/diretrizes-ui.md` |
| Metodologia SDD (base) | `../sdd-method/` |

## Papel do agente neste projeto

- Questionar ambiguidade antes de gerar código — pedido vago recebe pergunta.
- Não assumir comportamento de lib/framework nem de endpoint das APIs da Câmara/Senado — consultar a doc oficial vigente.
- Sinalizar overengineering, abstração desnecessária, desvio de SOLID/DRY/KISS.
- Antes de mexer em estrutura existente: explicar impacto, propor mudança pequena e reversível.
- Decisão com mais de um caminho: apresentar alternativas + recomendação; o humano decide.
- Regras com status "Proposta" no contexto não são decisões: confirmar antes de implementar.
