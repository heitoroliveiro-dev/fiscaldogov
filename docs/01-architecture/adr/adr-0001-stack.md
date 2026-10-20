# ADR-0001 — Stack do projeto

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** Heitor Oliveiro

## Contexto

Precisamos fixar linguagens, frameworks, banco e ferramentas antes da fundação técnica (F2). As forças em jogo, já decididas no contexto do projeto:

- **DA01:** o site lê de um banco próprio, alimentado por um ETL periódico em **Python**; o site não consulta as APIs oficiais ao vivo.
- **Constituição, princípio V:** o site público é somente leitura; só o ETL escreve no banco.
- **Constituição, princípio III:** toda estatística tem regra pública e teste — a metodologia não pode ter duas implementações que possam divergir.
- **DA02/DA07:** um adaptador por fonte; a Câmara exige JSON (API v2), XML (webservice legado) e HTML (página pública).
- **RNF04:** custo ≤ US$ 10/mês e páginas públicas servidas por cache/CDN; os dados mudam uma vez por dia (RNF01).
- **RNF03, RNF05, RNF09:** LCP ≤ 2,5 s no 4G, WCAG 2.2 AA, layout de 360 px a 1440 px.
- **Design system** de referência em `../design-system/linear` (Next.js + Tailwind v4 + Radix).
- **Restrição:** um desenvolvedor, 8 h/semana; código aberto sob AGPL-3.0 (DA08).

## Decisão

| Camada | Escolha |
|---|---|
| **Frontend** | **Next.js 16** (App Router) + **React 19** + **TypeScript** estrito + **Tailwind CSS v4** + **Radix** com convenções shadcn/ui, a partir do design system `../design-system/linear` v1.0.0. Node 24 LTS, npm. |
| **Banco** | **PostgreSQL**, hospedado no Railway (plano Hobby já existente). Versão major fixada na F2. |
| **Schema e migrations** | **Prisma ORM 7** (Prisma Migrate). `schema.prisma` é a fonte única do schema; migrations em SQL versionadas no repositório e aplicadas com `prisma migrate deploy` antes do ETL. |
| **Acesso do site ao banco** | **Prisma Client**, somente leitura, conectado com um **papel do Postgres que só tem `SELECT`** — o princípio V garantido pelo banco, não só pelo código. |
| **ETL, domínio e estatísticas** | **Python 3.14**: adaptadores por fonte, modelo de domínio e **todo o cálculo das estatísticas** (taxas, medianas, taxa do partido). Escreve com **SQLAlchemy 2 (Core)** + **psycopg 3**, lendo a estrutura das tabelas do próprio banco (reflection), com um papel do Postgres de escrita. Ferramentas: pytest, ruff, uv (lockfile). Bibliotecas de apoio (cliente HTTP, parser de XML/HTML, validação) são escolhidas no plano da F2. |
| **Estatísticas** | Calculadas **só no Python** e gravadas prontas no banco, com a versão da metodologia e a data do cálculo. O site exibe; filtros (partido, estado, ano) selecionam linhas já calculadas. |
| **Cache** | A CDN, na frente de páginas geradas após cada execução do ETL. **Sem Redis no M1.** Detalhe de renderização e hospedagem do site: ADR de hospedagem. |
| **Testes** | pytest (cálculo, adaptadores com respostas gravadas, ETL contra Postgres efêmero); Vitest + Testing Library (componentes); Playwright em viewports de celular e computador (E2E); axe (RNF05); Lighthouse em perfil mobile (RNF03). |

Estrutura do repositório (detalhe no plano da F2): uma pasta para o site (Next.js, com o `schema.prisma` e as migrations) e uma para o ETL (Python).

## Alternativas consideradas

- **Supabase (gratuito ou Pro) como banco.** Os recursos que o diferenciam — autenticação, tempo real, API REST automática — não são usados por um site público somente leitura, e a API automática seria mais uma superfície de ataque. O plano gratuito tem 500 MB, não tem backup e pausa o projeto após 7 dias sem uso; o Pro (US$ 25/mês) estoura a RNF04.
- **Redis como cache já no M1.** Os dados mudam uma vez por dia e a CDN já faz o cache das páginas; seria um serviço a mais para operar e pagar sem ganho. Reavaliar na HU03, para limitar requisições da busca.
- **Alembic (Python) como dono das migrations, com o Prisma só lendo (`prisma db pull`).** Coerente com "quem escreve é dono do schema", mas descartado por preferência do responsável pelo Prisma Migrate. A reflection no Python evita duplicar a definição das tabelas.
- **Prisma também no Python (Prisma Client Python).** Descartado: o projeto foi arquivado em abril de 2025.
- **ETL em TypeScript, com Prisma de ponta a ponta.** Uma linguagem só, mas revoga a DA01; o ecossistema Python é mais adequado para coleta e tratamento de dados.
- **Calcular as estatísticas no Next (consultas ou views SQL).** Daria mais liberdade para combinar filtros, mas a metodologia passaria a ter uma segunda implementação, e o site precisaria do banco a cada requisição (contra a RNF04).

## Consequências

- **Positivas:**
  - Uma única implementação da metodologia, em funções puras testadas com pytest.
  - O site não calcula nada e não escreve nada; o papel só-leitura torna isso uma garantia do banco.
  - Reaproveita o design system e o Railway já existentes; custo dentro do teto.
- **Negativas / trade-offs:**
  - Duas linguagens e duas cadeias de ferramentas (Node e Python) para um desenvolvedor.
  - O schema é definido no Prisma, mas quem escreve é o Python: o pipeline precisa de Node para aplicar migrations, e o Python não tem tipos estáticos gerados das tabelas.
  - Qualquer combinação de filtro nova exige um cálculo novo no ETL.
- **Riscos e mitigação:**
  - *Divergência entre o schema e o ETL* → teste no CI que aplica as migrations num Postgres efêmero e roda o ETL contra ele.
  - *Prisma 8 está em release candidate* → fixar a major 7 e atualizar por decisão deliberada.
  - *Backup do Postgres no Railway Hobby* → definir no ADR de hospedagem (proposta: dump diário feito pelo ETL para armazenamento externo, com runbook de restauração).

## Referências

- Contexto do projeto: DA01, DA02, DA07, DA08, RNF01–RNF10; constituição v1.0.0, princípios III e V.
- Prisma Client Python, repositório arquivado: <https://github.com/RobertCraigie/prisma-client-py>
- Supabase, planos e limites: <https://supabase.com/pricing>
- Railway, preços: <https://railway.com/pricing>
- Versões verificadas em 2026-10-20: `prisma` 7.10.1 (8.0.0 em rc), `next` 16.4.2.
