# Implementation Plan: Fundação técnica — esqueleto ponta a ponta

**Branch**: `feature/001-fundacao-tecnica` | **Date**: 2026-10-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-fundacao-tecnica/spec.md`

## Summary

Construir o caminho completo **fonte oficial → coleta → banco → página estática publicada** com um único deputado, e as travas que todas as features seguintes vão herdar:

- **Coleta:** um ETL em Python (arquitetura hexagonal, ADR-0003) roda no cron do Railway às 03:00, com reserva às 05:00. Ele coleta a lista de deputados em exercício e o histórico do selecionado na API v2 da Câmara, sem tocar no endpoint que traz CPF. Grava tudo numa única transação com o papel `etl_escrita`, guarda as respostas brutas sanitizadas e um `pg_dump` no R2, e dispara a publicação.
- **Publicação:** o GitHub Actions gera o site Next.js em exportação estática, lendo com o papel `site_leitura`, e o publica na Cloudflare (`*.workers.dev`).
- **Operação:** o alerta de falha no canal do RNF07 foi antecipado da F4. A página avisa quando a última conferência passa de 48 h, calculando no navegador, e identifica a versão publicada.
- **Travas:** o pre-commit passa a rodar lint, formatação e testes das duas partes. O CI tem 7 jobs obrigatórios, incluindo integração contra Postgres efêmero com as migrations do Prisma e E2E com axe.

Decisões e alternativas: [research.md](research.md).

## Technical Context

**Language/Version**: TypeScript 6 (Node 24 LTS) no site · Python 3.14 no ETL

**Primary Dependencies**:
- Site: Next.js 16, React 19, Tailwind CSS 4, Radix e componentes do design system, next-themes, Prisma 7 (`@prisma/adapter-pg`).
- ETL: SQLAlchemy 2 Core, psycopg 3, httpx, boto3.
- Publicação: Wrangler 4.

**Storage**: PostgreSQL no Railway (mesma major no CI) · Cloudflare R2 para respostas brutas e backups

**Testing**:
- pytest (unidade, arquitetura, integração contra Postgres de serviço no CI);
- Vitest + Testing Library;
- Playwright + `@axe-core/playwright` (E2E em 360 e 1440 px, claro e escuro);
- Lighthouse mobile (validação manual R9).

**Target Platform**: navegadores modernos de celular e computador · ETL em container Linux no Railway · build em GitHub Actions (Ubuntu)

**Project Type**: aplicação web estática + processo de coleta agendado (duas partes no mesmo repositório)

**Performance Goals**:
- LCP ≤ 2,5 s no 4G (SC-001);
- dados publicados até 08:00 (FR-014);
- coleta da F2 em segundos, com teto de 60 min (FR-013a).

**Constraints**:
- custo total ≤ US$ 10/mês (RNF04);
- site sem nada dinâmico (ADR-0002);
- nenhum CPF no banco nem nos brutos (RNF06);
- credenciais de dono e de escrita só no Railway.

**Scale/Scope**: 1 deputado, ~2 a 5 períodos e filiações, 2 execuções agendadas por dia · 1 página · 10 tabelas

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Como este plano atende | Verificação |
|---|---|---|
| **I. Todo dado é rastreável à fonte oficial** (NON-NEGOTIABLE) | Todo registro tem `fonte_url` e `coletado_em`; a página mostra a fonte, o link para `camara.leg.br/deputados/{id}` e a data da execução que gerou a versão publicada; o build falha se não houver dado, em vez de publicar página sem origem. | E2E de `contracts/pagina-publica.md` (fonte, link, data); integração: nenhuma linha sem `fonte_url`. |
| **II. Neutralidade política** (NON-NEGOTIABLE) | O deputado é escolhido por regra objetiva (ordem alfabética entre os em exercício), não por escolha pessoal; sem cor de partido; página marcada como teste e fora dos buscadores. | Teste de unidade da regra de seleção (nomes com acento e maiúsculas); E2E confere `noindex`. |
| **III. Estatística = regra pública + teste** (NON-NEGOTIABLE) | Não há estatística nesta feature. A derivação de períodos e filiações (base do futuro denominador) é função pura testada com histórico real gravado antes da implementação (TDD). | pytest com fixture do deputado 204496 (22 eventos). |
| **IV. Estatística ancorada no mandato** | Mandato e período de exercício existem desde já, com não sobreposição garantida pelo banco; multi-legislatura no modelo (`legislatura_numero`). | Integração: inserir períodos sobrepostos é recusado. |
| **V. Fontes isoladas; site nunca depende da API ao vivo** | Site estático lê só o banco, no build, com `site_leitura` (só `SELECT`); só o ETL chama a API e escreve; adaptador da Câmara isolado do domínio; falha da coleta não derruba o site. | Integração: escrita com `site_leitura` recusada; teste de arquitetura (`dominio` não importa `adaptadores`); roteiro R5/R9.4. |
| **VI. Segurança básica** | Credenciais só nos cofres (`contracts/ambientes-e-segredos.md`); hook de segredos mantido; SQLAlchemy Core parametrizado (sem SQL concatenado); sem parâmetros de ordenação/filtro vindos de usuário nesta feature. | Hook de segredos; revisão do diff; `ruff` com regras de segurança (`S`). |
| **VII. DoD com evidência** | Cada critério de sucesso tem um roteiro no `quickstart.md`; review por subagente contra este plano antes do PR. | Evidências dos roteiros R1–R10 anexadas ao PR. |
| **Restrições de domínio** | Web responsivo 360–1440 px (D1–D3 aplicadas); linguagem simples no aviso de testes; Câmara apenas. | E2E nas quatro combinações de largura e tema. |
| **Fluxo** | Gitflow (`feature/001-…` → `develop`); SDD completo. | — |

**Resultado do gate:** ✅ passa sem exceções. Reavaliado após a fase 1 (data model e contratos): ✅ sem mudanças.

## Project Structure

### Documentation (this feature)

```text
specs/001-fundacao-tecnica/
├── plan.md              # este arquivo
├── research.md          # fase 0
├── data-model.md        # fase 1
├── quickstart.md        # fase 1 — roteiros R1–R10
├── contracts/           # fase 1
│   ├── fonte-camara-api-v2.md
│   ├── etl-cli.md
│   ├── pagina-publica.md
│   ├── publicacao.md
│   └── ambientes-e-segredos.md
├── checklists/requirements.md
└── tasks.md             # fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
web/                               # site (Next.js, exportação estática)
├── package.json                   # "type": "module"; scripts: dev, build, lint, typecheck, test, test:e2e, db:*
├── next.config.ts                 # output: 'export'
├── prisma.config.ts
├── prisma/
│   ├── schema.prisma              # fonte única do schema (ADR-0001)
│   └── migrations/0001_fundacao/  # tabelas, enums, cargas fixas, invariantes, GRANTs
├── tokens/ · scripts/             # do design system (geração de tokens + verificação WCAG)
├── public/_headers                # X-Robots-Tag: noindex
├── wrangler.jsonc                 # static assets: ./out
├── src/
│   ├── app/layout.tsx · page.tsx
│   ├── components/ui/             # Card, Badge, Button, Separator (do design system)
│   ├── components/                # alternar-tema, fonte-oficial, aviso-testes, aviso-desatualizado (script no navegador)
│   ├── lib/db.ts                  # PrismaClient com adapter-pg (leitura)
│   ├── lib/dados.ts               # consulta do deputado exibido e da última execução
│   ├── lib/formatar-data.ts       # America/Sao_Paulo
│   └── styles/                    # do design system
└── tests/ · e2e/

etl/                               # coleta (Python)
├── pyproject.toml · uv.lock
├── Dockerfile                     # Python 3.14 + postgresql-client + Node/Prisma CLI (só para migrate)
├── railway.json                   # cron 0 6,8 * * *, preDeploy: prisma migrate deploy, restart: never
├── src/etl/
│   ├── __main__.py                # comandos: coletar, reserva, agendado, verificar-config
│   ├── dominio/                   # entidades, seleção (FR-006), derivação de períodos/filiações
│   ├── portas/                    # FonteDaCasa, RepositorioDeDados, ArmazemDeBrutos, Backup, Publicador
│   ├── adaptadores/
│   │   ├── camara/api_v2.py       # + sanitização dos brutos
│   │   ├── persistencia/          # SQLAlchemy Core com reflection
│   │   ├── brutos_r2/
│   │   ├── backup_r2/             # pg_dump → R2
│   │   ├── publicacao/            # workflow_dispatch
│   │   └── alertas/               # mensagem no canal do RNF07 (FR-029)
│   ├── pipeline/                  # execução, transação, vigia de 60 min, nova tentativa
│   └── config.py
└── tests/
    ├── unidade/ · arquitetura/
    ├── integracao/                # marcador "integration"
    └── fixtures/camara/

.github/workflows/ci.yml           # 7 jobs obrigatórios
.github/workflows/publicar.yml
.githooks/pre-commit               # + lint/format/testes por parte alterada
scripts/dev-banco-papeis.sql       # cria papéis com senhas de teste (CI/local)
docs/05-runbooks/
├── banco-papeis.md                # criar papéis em produção, rotação de senha
├── restauracao-backup.md
└── operacao-coleta.md             # acionar manualmente, ler execucao_etl
```

**Structure Decision**: duas partes independentes no mesmo repositório — `web/` (Node) e `etl/` (Python) —, cada uma com seu gerenciador e seus testes. O schema vive em `web/prisma/` (o Prisma pertence ao lado Node), e o ETL o consome por reflection. Não há código compartilhado entre as partes; o banco é o contrato.

## Complexity Tracking

Sem violações da constituição a justificar.

Registro de escolhas que podem parecer complexidade e que foram mantidas de propósito:

| Escolha | Por quê | Alternativa mais simples descartada |
|---|---|---|
| Node + CLI do Prisma dentro da imagem do ETL | Aplicar migrations no Railway sem levar a credencial de dono ao GitHub (research §3) | Job de migration no GitHub Actions — credencial de dono fora do Railway |
| Três papéis no banco (dono, escrita, leitura) | Princípio V e menor privilégio garantidos pelo banco | Um papel só — o site poderia escrever e o ETL alterar a estrutura |
| Um único cron com dois horários e comando `agendado` | Reserva das 05:00 (FR-013) sem um segundo serviço | Dois serviços cron com a mesma imagem |
