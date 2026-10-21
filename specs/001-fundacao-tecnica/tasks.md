---

description: "Lista de tarefas da 001 — Fundação técnica"
---

# Tasks: Fundação técnica — esqueleto ponta a ponta

**Input**: Design documents from `/specs/001-fundacao-tecnica/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: obrigatórios. A constituição exige TDD na lógica não trivial (princípio III), e a spec pede travas e testes explícitos (FR-021 a FR-023). Em cada história, os testes vêm **antes** da implementação e devem **falhar** primeiro.

**Organization**: tarefas agrupadas por história. Entre as histórias P2, a ordem escolhida é US3 → US4 → US2, porque as travas (CI) protegem todo o trabalho seguinte.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência pendente)
- **[Story]**: história da spec (US1…US5)
- **⚠️**: depende de ação humana ou externa (do responsável)

## Path Conventions

Duas partes no mesmo repositório (plan.md → Project Structure): `web/` (Next.js, Node) e `etl/` (Python, pacote `etl/src/etl/`). Workflows em `.github/workflows/`, runbooks em `docs/05-runbooks/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: esqueletos das duas partes, ferramentas de estilo e banco local.

- [X] T001 Definir a versão major do Postgres e confirmar `btree_gist`; registrar em `specs/001-fundacao-tecnica/research.md` §11 — feito: **18**, verificado localmente na mesma base da imagem da Railway. A criação do serviço em produção (imagem `postgres-ssl:18` explícita) passou para a T051, pois a Railway estava com deploys pausados em 2026-10-20
- [X] T002 Criar `web/package.json` (`"type": "module"`, Node 24, scripts `dev`, `build`, `lint`, `typecheck`, `test`, `test:e2e`, `tokens`, `db:generate`, `db:migrate:dev`, `db:migrate:deploy`), `web/tsconfig.json` (TypeScript 6 estrito, `module: ESNext`, `moduleResolution: bundler`) e `web/next.config.ts` com `output: 'export'`, conforme research §1–2
- [X] T003 [P] Configurar ESLint 10 (`web/eslint.config.mjs`, base do design system) e Prettier (`web/.prettierrc.json`) em `web/`
- [X] T004 [P] Copiar do design system (`../design-system/linear`, opção B, research §8) para `web/`: `tokens/`, `scripts/`, `src/styles/`, `src/lib/utils.ts`, `components.json` e os componentes `card`, `button` e `separator` em `web/src/components/ui/` (só os usados na página); `npm --prefix web run tokens` precisa passar (verificação WCAG)
- [X] T005 [P] Criar `etl/pyproject.toml`:
  - Python 3.14;
  - dependências `sqlalchemy>=2.1,<2.2`, `psycopg[binary]>=3.3,<3.4`, `httpx>=0.28,<0.29`, `boto3>=1.43,<2`;
  - desenvolvimento `pytest>=9.1,<10`, `ruff>=0.17,<0.18`;
  - ruff com as regras `E,F,I,B,S,UP`;
  - marcador pytest `integration`;
  - gerar `etl/uv.lock`;
  - criar o pacote vazio `etl/src/etl/__init__.py` com as subpastas `dominio/`, `portas/`, `adaptadores/{camara,persistencia,brutos_r2,backup_r2,publicacao,alertas}/` e `pipeline/` (cada uma com `__init__.py`).
- [X] T006 Criar `docker-compose.yml` na raiz com Postgres local na mesma major anotada em T001 e `scripts/dev-banco-papeis.sql` que cria os papéis `etl_escrita` e `site_leitura` com senhas de teste (só desenvolvimento e CI; senhas de produção nunca no repositório — research §3)
- [X] T007 [P] Criar `web/.env.example` e `etl/.env.example` com os nomes de `contracts/ambientes-e-segredos.md`, sem valores; acrescentar ao `.gitignore` `web/src/generated/`, `web/out/`, `web/test-results/`, `etl/.venv/`

**Checkpoint**: `npm --prefix web run lint` e `uv run --directory etl ruff check` rodam sem erro em projetos vazios; `docker compose up` sobe o banco.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: schema com invariantes e permissões, acesso ao banco, configuração, registros e a trava de arquitetura — tudo de que US1–US5 dependem.

**⚠️ CRITICAL**: nenhuma história começa antes do fim desta fase.

### Testes primeiro (devem falhar)

- [X] T008 [P] Escrever `etl/tests/integracao/conftest.py`: conexão com `DATABASE_URL_TESTE` (papel dono), `DATABASE_URL_ESCRITA_TESTE` e `DATABASE_URL_LEITURA_TESTE`, com fixture que abre a transação e faz rollback ao fim de cada teste. Localmente, sem as variáveis, os testes de integração são pulados com mensagem clara; com `ETL_EXIGIR_INTEGRACAO=1` (definida no CI), variável ausente é **erro**, nunca pulo (princípio III: nenhum teste mascarado)
- [X] T009 [P] Escrever `etl/tests/integracao/test_invariantes.py`, um teste por invariante de `data-model.md`:
  1. `periodo_exercicio.fim > inicio` quando `fim` não é nulo.
  2. Períodos do mesmo mandato não se sobrepõem.
  3. "No máximo uma filiação aberta por parlamentar".
  4. `identificador_externo` com `num_nonnulls(parlamentar_id, partido_id) = 1`.
  5. As cargas fixas existem: (`CD`, Câmara dos Deputados) e a legislatura 57 de 2023-02-01 a 2027-01-31.
- [X] T010 [P] Escrever `etl/tests/arquitetura/test_dependencias.py`: nenhum módulo em `etl/src/etl/dominio/` importa `etl.adaptadores` nem bibliotecas de I/O (`httpx`, `sqlalchemy`, `boto3`, `psycopg`) — FR-023, ADR-0003
- [X] T011 [P] Escrever `etl/tests/unidade/test_registro.py`: o logger de operação mascara valores de variáveis que contêm `TOKEN`, `SECRET`, `PASSWORD` ou `DATABASE_URL`, e senhas dentro de URLs de conexão (FR-030)
- [X] T012 [P] Escrever `etl/tests/unidade/test_config.py`: variável obrigatória ausente → `ConfiguracaoInvalida` com o nome da variável; o comando sai com código 2 (contracts/etl-cli.md)

### Implementação

- [X] T013 Criar `web/prisma.config.ts` (schema em `prisma/schema.prisma`, migrations em `prisma/migrations`, `.env` via `dotenv`; a URL de `DATABASE_URL_DONO` é **opcional ao carregar** — exigida só pelos comandos de migration —, porque o `prisma generate` do `publicar.yml` roda sem ela; confirmar o comportamento do `env()` do Prisma 7 e, se ele exigir a variável, ler de `process.env` sem falhar) e `web/prisma/schema.prisma` com generator `prisma-client` (`output = "../src/generated/prisma"`) e as 10 tabelas de `data-model.md` via `@@map`:
  - `casa_legislativa`, `legislatura`, `partido`;
  - `parlamentar` (`nome_ordenacao`; **"Sem CPF e sem nome civil"**);
  - `identificador_externo` (enum `sistema`: `camara_v2`, `camara_v2_partido`);
  - `mandato`, com "Único (parlamentar, casa, legislatura)";
  - `periodo_exercicio` (enum `condicao`: `titular`, `suplente`);
  - `filiacao`;
  - `execucao_etl`: enum `status` com `em_andamento`, `sucesso`, `com_pendencias`, `falha` e `dispensada`; enum `gatilho` com `agendada`, `reserva` e `manual`;
  - `coleta_bruta`.
- [X] T014 Gerar a migration `web/prisma/migrations/0001_fundacao/` com `prisma migrate dev --create-only` e acrescentar ao SQL:
  - `CREATE EXTENSION IF NOT EXISTS btree_gist`;
  - CHECK `fim > inicio`;
  - `EXCLUDE USING gist (mandato_id WITH =, tstzrange(inicio, fim) WITH &&)`;
  - índice único parcial `(parlamentar_id) WHERE fim IS NULL` em `filiacao`;
  - CHECK `num_nonnulls(parlamentar_id, partido_id) = 1`;
  - cargas fixas de casa e legislatura;
  - `GRANT SELECT, INSERT, UPDATE, DELETE` e `ALTER DEFAULT PRIVILEGES` para `etl_escrita`;
  - `GRANT SELECT` e `ALTER DEFAULT PRIVILEGES` para `site_leitura`;
  - `GRANT USAGE, SELECT ON ALL SEQUENCES` e privilégios padrão equivalentes para `etl_escrita` (o `pg_dump` da US5 roda com esse papel e precisa ler sequences e `_prisma_migrations`).

  Rodar T009 até ficar verde.
- [ ] T015 [P] Implementar `etl/src/etl/config.py` (leitura e validação das variáveis de `contracts/ambientes-e-segredos.md`; `ConfiguracaoInvalida`) e um `etl/src/etl/__main__.py` mínimo, que carrega a configuração antes de qualquer comando e sai com código 2 se ela for inválida (o teste de código de saída da T012 depende dele; a T040 acrescenta os comandos), até T012 passar
- [ ] T016 [P] Implementar `etl/src/etl/registro.py` (logger estruturado em stdout com mascaramento de segredos) até T011 passar
- [ ] T017 Implementar `etl/src/etl/adaptadores/persistencia/banco.py`: engine SQLAlchemy 2 Core com psycopg 3, `MetaData.reflect()` das tabelas do Prisma, unidade de trabalho com uma única transação, `statement_timeout` de sessão
- [ ] T018 Implementar `etl/src/etl/adaptadores/persistencia/execucoes.py`: `iniciar(gatilho, versao_codigo)` (transação própria, status `em_andamento`), `finalizar(id, status, contagens, tentativas, erros, pendencias)` e `ultima_bem_sucedida()`; teste em `etl/tests/integracao/test_execucoes.py`
- [ ] T019 [P] Criar `web/src/lib/db.ts`: `PrismaClient` com `@prisma/adapter-pg`, conectado a `DATABASE_URL_LEITURA`, importado de `web/src/generated/prisma`
- [ ] T020 Rodar T010 (arquitetura) verde com a árvore de pacotes de T005 e documentar no `etl/README.md` como rodar unidade e integração localmente

**Checkpoint**: `prisma migrate deploy` num banco vazio + `pytest -m integration` verde para invariantes e execuções; arquitetura e registro verdes.

---

## Phase 3: User Story 1 — Um dado oficial publicado, com fonte e data (Priority: P1) 🎯 MVP

**Goal**: coleta manual → banco → página estática publicada com nome, partido atual, UF, fonte, link e "Conferido na fonte oficial em".

**Independent Test**: `python -m etl coletar --gatilho manual`, acionar `publicar.yml` e abrir o `*.workers.dev` no celular e no computador (quickstart R2, R3, R3b, R9.2).

### Testes da US1 (escrever primeiro, devem falhar)

- [ ] T021 [P] [US1] Gravar as fixtures reais, sanitizadas, em `etl/tests/fixtures/camara/`: `deputados-pagina1-2026-10-20.json` (`GET /deputados?itens=100&pagina=1`) e `historico-204496-2026-10-20.json` (`GET /deputados/204496/historico`, 22 eventos) — nunca chamar `/deputados/{id}`
- [ ] T022 [P] [US1] Escrever `etl/tests/unidade/test_selecao.py`: ordenação por nome em minúsculas e sem acento ("Átila" antes de "Bruno", "álvaro" igual a "Alvaro"), escolha do primeiro, `nome_ordenacao` gerado (FR-006)
- [ ] T023 [P] [US1] Escrever `etl/tests/unidade/test_historico.py`, com a fixture 204496:
  - os períodos abrem em `situacao = "Exercício"` e fecham no próximo evento diferente ("Licença", "Afastado"…);
  - a `condicao` sai de `condicaoEleitoral`;
  - as filiações mudam quando muda a `siglaPartido`, e o evento inicial "Partido no início da legislatura" define a primeira;
  - a UF vem do primeiro evento;
  - eventos fora de ordem são ordenados por `dataHora`, com empate mantendo a ordem da fonte (FR-007b).
- [ ] T024 [P] [US1] Escrever `etl/tests/unidade/test_sanitizacao.py`: remoção recursiva de `cpf`, `dataNascimento`, `municipioNascimento`, `ufNascimento`, `escolaridade` (contracts/fonte-camara-api-v2.md)
- [ ] T025 [P] [US1] Escrever `etl/tests/unidade/test_api_v2.py`, com um transporte httpx falso servindo as fixtures:
  - a paginação segue `links[rel=next]`;
  - `User-Agent` e `Accept` são enviados;
  - o timeout é de 30 s;
  - campo usado ausente ou de tipo inesperado → `RespostaInvalida`;
  - lista vazia, ou menos de 500 deputados em exercício, → `FonteIncompleta`;
  - histórico vazio → `FonteIncompleta`;
  - nenhuma chamada a `/deputados/{id}`.
- [ ] T026 [P] [US1] Escrever `etl/tests/unidade/test_brutos.py`: chave `camara/api-v2/<caminho>/<sha256>.json.gz`; conteúdo compactado; não regrava se o `sha256` for igual ao da última `coleta_bruta` da mesma URL (FR-011)
- [ ] T027 [US1] Escrever `etl/tests/integracao/test_coletar.py`, com fonte falsa e armazém de brutos falso:
  - a coleta grava parlamentar, identificadores, mandato, períodos e filiação, todos com `fonte_url` e `coletado_em` (FR-008);
  - nenhuma coluna ou valor de CPF no banco (FR-009);
  - rodar duas vezes produz o mesmo estado, sem duplicar (FR-007a);
  - os parlamentares já armazenados têm o histórico atualizado (FR-007);
  - erro na gravação desfaz os dados de domínio, mas mantém os registros de `coleta_bruta` da execução que falhou (FR-012);
  - `execucao_etl` termina `sucesso`, com contagens.
- [ ] T028 [P] [US1] Escrever `web/tests/formatar-data.test.ts`: "Conferido na fonte oficial em DD/MM/AAAA às HH:MM (horário de Brasília)" em `America/Sao_Paulo`, inclusive para um horário UTC que vira o dia anterior em Brasília
- [ ] T029 [P] [US1] Escrever `web/tests/aviso-desatualizado.test.tsx`: aviso "Atenção: os dados podem estar desatualizados." com conferência de 49 h atrás; ausente com 47 h (FR-002a, SC-011)
- [ ] T030 [P] [US1] Escrever `web/tests/dados.test.ts`: a consulta do deputado exibido escolhe o período aberto (`fim` nulo) da 57ª com menor `nome_ordenacao`; sem deputado em exercício, ou sem execução bem-sucedida, lança erro que faz o build falhar (FR-016a)
- [ ] T031 [US1] Escrever `web/e2e/pagina.spec.ts` + `web/playwright.config.ts`, contra o `out/` servido localmente:
  - todos os elementos e seletores de `contracts/pagina-publica.md`;
  - `noindex` no HTML;
  - `/versao.json` com `execucao_id` e commit;
  - 360 px e 1440 px × claro e escuro, sem rolagem horizontal;
  - zero violações do `@axe-core/playwright` (WCAG 2.2 A/AA);
  - alvos ≥ 44 px abaixo de 1024 px;
  - em 1440 px, o bloco `data-testid=fonte` está à direita do `h1` (mesma faixa vertical), e abaixo dele em 360 px (FR-003).

### Implementação da US1

- [ ] T032 [P] [US1] Criar `etl/src/etl/dominio/entidades.py` (dataclasses imutáveis: `Parlamentar`, `IdentificadorExterno`, `Mandato`, `PeriodoDeExercicio`, `Partido`, `Filiacao`, `EventoHistorico`)
- [ ] T033 [P] [US1] Implementar `etl/src/etl/dominio/selecao.py` (`normalizar_nome`, `selecionar_deputado`) até T022 passar
- [ ] T034 [US1] Implementar `etl/src/etl/dominio/historico.py` (`derivar_periodos`, `derivar_filiacoes`, `derivar_uf`, como funções puras) até T023 passar
- [ ] T035 [P] [US1] Criar as portas em `etl/src/etl/portas/__init__.py` como `typing.Protocol`: `FonteDaCasa`, `RepositorioDeDados`, `ArmazemDeBrutos`, `Backup`, `Publicador`, `Alertador`
- [ ] T036 [US1] Implementar `etl/src/etl/adaptadores/camara/sanitizacao.py` e `etl/src/etl/adaptadores/camara/api_v2.py`:
  - httpx com `User-Agent: fiscaldogov-etl (+https://github.com/heitoroliveiro-dev/fiscaldogov)`, timeout de 30 s e no máximo 4 requisições simultâneas;
  - `listar_em_exercicio()` paginado e `historico(id)`;
  - validação dos campos usados;
  - `FonteIncompleta` e `RespostaInvalida`.

  Rodar até T024 e T025 passarem.
- [ ] T037 [US1] Implementar `etl/src/etl/adaptadores/brutos_r2/armazem.py` (boto3 no endpoint S3 do R2, gzip, sha256, deduplicação consultando `coleta_bruta`; o registro em `coleta_bruta` é gravado em **transação própria**, como `execucao_etl`, para sobreviver ao rollback da coleta — FR-012) e um `ArmazemDeBrutosEmDisco` para testes e desenvolvimento, até T026 passar
- [ ] T038 [US1] Implementar `etl/src/etl/adaptadores/persistencia/repositorio.py`:
  - `upsert` de parlamentar (por `identificador_externo` `camara_v2`), partido (por `camara_v2_partido`) e mandato;
  - substituição dos períodos e filiações do parlamentar dentro da transação;
  - `parlamentares_armazenados()`.
- [ ] T039 [US1] Implementar `etl/src/etl/adaptadores/publicacao/github.py`: `POST /repos/{GITHUB_REPOSITORIO}/actions/workflows/publicar.yml/dispatches` com `ref=main` e `inputs.execucao_id`; erro 401/403 → `CredencialInvalida`. Teste em `etl/tests/unidade/test_publicacao.py` com transporte falso.
- [ ] T040 [US1] Implementar `etl/src/etl/pipeline/coletar.py` (etapas 1–5, 7 e 8 de `contracts/etl-cli.md`, com falha do bruto ou do disparo → `com_pendencias`) e os comandos `coletar` e `verificar-config` no `etl/src/etl/__main__.py` criado na T015, com os códigos de saída 0, 1 e 2, até T027 passar
- [ ] T041 [P] [US1] Implementar `web/src/lib/formatar-data.ts` até T028 passar
- [ ] T042 [P] [US1] Implementar `web/src/lib/dados.ts` (deputado exibido + última execução `sucesso`/`com_pendencias`, via Prisma) até T030 passar
- [ ] T043 [P] [US1] Criar os componentes `web/src/components/aviso-testes.tsx` (`role=status`), `web/src/components/fonte-oficial.tsx` (fonte, link com nome acessível "Ver registro na Câmara dos Deputados", `<time>` com `data-testid=conferido-em`) e `web/src/components/alternar-tema.tsx` (next-themes, padrão do sistema, nome acessível "Alternar tema")
- [ ] T044 [P] [US1] Criar `web/src/components/aviso-desatualizado.tsx` (componente de cliente que lê o `datetime` e mostra o aviso com `role=alert` após 48 h) até T029 passar
- [ ] T045 [US1] Criar `web/src/app/layout.tsx` e `web/src/app/page.tsx`:
  - `lang="pt-BR"`;
  - `<meta name="robots" content="noindex">`;
  - `<meta name="versao-publicada">` com `execucao` e `commit`;
  - nome como `h1` e `data-testid=partido-uf`;
  - corpo 16 px e alvos de 44 px abaixo de `lg` (D1, D2);
  - a partir de `lg` (1024 px): bloco de fonte e data ao lado do nome, conteúdo com largura máxima de 1200 px centralizado (FR-003).
- [ ] T046 [P] [US1] Criar `web/src/app/versao.json/route.ts` (`dynamic = 'force-static'`, retorna `execucao_id` e commit — FR-028) e `web/public/_headers` com `X-Robots-Tag: noindex` para `/*` (FR-005)
- [ ] T047 [US1] Criar `web/prisma/seed-e2e.sql` (um parlamentar com período aberto e uma execução `sucesso`), usado no build de teste, e rodar T031 até ficar verde localmente
- [ ] T048 [US1] Criar `web/wrangler.jsonc` (sem script; `assets.directory = "./out"`) e `.github/workflows/publicar.yml`:
  - gatilhos `workflow_dispatch` (input `execucao_id`) e `push` em `main`;
  - `concurrency: { group: publicar, cancel-in-progress: true }`;
  - ambiente `producao`;
  - passos 1–5 de `contracts/publicacao.md`.
- [ ] T049 [US1] Criar `etl/Dockerfile`, construído com **contexto na raiz do repositório** (o serviço do Railway usa a raiz como diretório de build e `dockerfilePath = etl/Dockerfile`, porque a imagem precisa de `web/prisma/`), e `.dockerignore` na raiz excluindo `web/node_modules`, `web/.next`, `web/out`, `etl/.venv`, `.git`:
  - base Python 3.14 slim;
  - `postgresql-client` na major de T001;
  - Node 24 com `web/prisma/`, `web/prisma.config.ts` e os pacotes `prisma` e `dotenv` nas versões fixadas em `web/package-lock.json` (o CLI do Prisma 7 lê o `prisma.config.ts`);
  - instalação com `uv sync --frozen`;
  - `CMD ["python", "-m", "etl", "coletar"]` provisório (o agendamento entra na US2).
- [ ] T050 [P] [US1] Escrever `docs/05-runbooks/banco-papeis.md`: criar `etl_escrita` e `site_leitura` em produção (senha gerada e guardada só nos cofres), conferir as permissões, trocar senha com `ALTER ROLE ... PASSWORD`
- [ ] T051 [US1] ⚠️ Em produção:
  - criar os papéis pelo runbook de T050;
  - criar o serviço Postgres no Railway com a imagem `ghcr.io/railwayapp-templates/postgres-ssl:18` explícita (a `:latest` é a 16 — research §11) e conferir `CREATE EXTENSION btree_gist` nele;
  - criar o serviço do ETL no Railway, com pré-deploy `prisma migrate deploy` e as variáveis de `contracts/ambientes-e-segredos.md`;
  - criar a conta e o token da Cloudflare, os buckets `fiscaldogov-brutos` e `fiscaldogov-backup` e o token do R2;
  - criar o token fine-grained do GitHub (confirmar a permissão de Actions e anotar a validade);
  - criar o ambiente `producao` com os segredos no GitHub;
  - registrar o que foi criado (sem valores de segredo) em `specs/001-fundacao-tecnica/evidencias.md`.
- [ ] T052 [US1] Validar ponta a ponta em produção (quickstart R2, R3, R3b, R9.2) e anexar a evidência — comando + saída e captura do `*.workers.dev` em 360 e 1440 px — em `specs/001-fundacao-tecnica/evidencias.md`

**Checkpoint**: a US1 funciona sozinha — coleta manual publica a página com fonte, link e data; testes de unidade, integração e E2E verdes.

---

## Phase 4: User Story 3 — Travas automáticas de qualidade (Priority: P2)

**Goal**: pre-commit e CI barram estilo, formatação, testes e build quebrados nas duas partes.

**Independent Test**: quickstart R7.

- [ ] T053 [P] [US3] Criar `web/.lintstagedrc.json` (`*.{ts,tsx}`: `eslint --fix`, `prettier --write`, `vitest related --run`; `*.{json,md,css}`: `prettier --write`)
- [ ] T054 [US3] Estender `.githooks/pre-commit`, mantendo as travas atuais:
  - com arquivos staged em `web/`: `npm --prefix web exec lint-staged`;
  - em `etl/`: `uv run --directory etl ruff format --check`, `ruff check` e `pytest -m "not integration" -q`;
  - ferramenta ausente → falha com instrução de instalação (falha fechada);
  - documentar o comportamento em `CONTRIBUTING.md`.
- [ ] T055 [US3] Escrever `etl/tests/integracao/test_contrato_schema.py`: depois de `prisma migrate deploy`, a reflection do SQLAlchemy encontra todas as tabelas e colunas que o ETL usa (lista explícita no teste), pegando divergência entre schema e ETL (ADR-0001)
- [ ] T056 [US3] Criar `.github/workflows/ci.yml` com os 7 jobs de research §9, rodando em `pull_request` e em `push` para `develop`/`main`:

  | Job | O que roda |
  |---|---|
  | `web-lint` | lint + typecheck |
  | `web-test` | Vitest |
  | `web-build` | Postgres de serviço + `scripts/dev-banco-papeis.sql` + `prisma migrate deploy` + `seed-e2e.sql` + `npm run build` |
  | `web-e2e` | Playwright com axe sobre o `out/` |
  | `etl-lint` | ruff |
  | `etl-test` | unidade + arquitetura |
  | `etl-integration` | Postgres de serviço + papéis + migrations + `pytest -m integration` |

  Regras do workflow:
  - todos os jobs de `web/` rodam `npm run db:generate` antes de lint, typecheck, teste ou build (o cliente do Prisma não é versionado — T007); no `web-lint`, o `db:generate` roda **sem** `DATABASE_URL_DONO` definida, provando que a publicação consegue gerar o cliente (T013);
  - `etl-integration` define `ETL_EXIGIR_INTEGRACAO=1` e falha se nenhum teste com o marcador `integration` for coletado;
  - o Postgres de serviço usa a major de T001, e o workflow não tem segredos.
- [ ] T057 [US3] ⚠️ Configurar a proteção de `main` e `develop` no GitHub: PR obrigatório, os 7 jobs de T056 como checks obrigatórios, sem force push; registrar a captura da regra em `specs/001-fundacao-tecnica/evidencias.md`
- [ ] T058 [US3] Executar o quickstart R7 (commits com erro de estilo, de formatação e com teste quebrado bloqueados; PR com teste falhando impedido) e anexar a evidência em `specs/001-fundacao-tecnica/evidencias.md`

**Checkpoint**: nenhuma alteração quebrada entra em `develop`/`main` (SC-004).

---

## Phase 5: User Story 4 — Acesso separado: só a coleta escreve (Priority: P2)

**Goal**: provar que `site_leitura` não escreve nem altera a estrutura, e que `etl_escrita` não altera a estrutura.

**Independent Test**: quickstart R4.

- [ ] T059 [US4] Escrever `etl/tests/integracao/test_papeis.py`:
  - com `site_leitura`, `INSERT`, `UPDATE`, `DELETE` e `CREATE TABLE` são recusados com "permission denied", e `SELECT` funciona;
  - com `etl_escrita`, DML funciona e `CREATE TABLE`/`DROP TABLE` são recusados (FR-019, SC-005).

  Corrigir os GRANTs de T014 se algum caso falhar.
- [ ] T060 [US4] Executar o quickstart R4 em produção com `site_leitura` (somente leitura: tentar `INSERT` dentro de `BEGIN … ROLLBACK`) e anexar a evidência em `specs/001-fundacao-tecnica/evidencias.md`

**Checkpoint**: o princípio V está garantido pelo banco, com teste no CI.

---

## Phase 6: User Story 2 — Atualização diária sem intervenção, resistente a falhas (Priority: P2)

**Goal**: agendamento às 03:00 com reserva às 05:00, novas tentativas, tempo limite, recusa de concorrência, alertas e recuperação.

**Independent Test**: quickstart R5, R6 e R9.3–R9.4.

### Testes da US2 (escrever primeiro, devem falhar)

- [ ] T061 [P] [US2] Escrever `etl/tests/unidade/test_tentativas.py`:
  - até 3 tentativas, com esperas de 5 s, 20 s e 60 s (relógio injetável);
  - nova tentativa só para erro de rede, tempo esgotado, HTTP 5xx e 429;
  - HTTP 4xx e `RespostaInvalida` falham na hora;
  - cada tentativa é registrada em `tentativas` (FR-013).
- [ ] T062 [P] [US2] Escrever `etl/tests/unidade/test_agenda.py`:
  - `agendado` às 06h UTC → `coletar --gatilho agendada`;
  - às 08h UTC → `reserva`;
  - `reserva` com `sucesso`/`com_pendencias` no dia de Brasília → `dispensada`;
  - `reserva` sem sucesso → coleta.
- [ ] T063 [P] [US2] Escrever `etl/tests/integracao/test_concorrencia.py`:
  - com `em_andamento` iniciada há menos de 60 min, `coletar` sai com código 3 sem gravar;
  - com uma iniciada há mais de 60 min, ela é fechada como `falha` ("interrompida") e o alerta é chamado (FR-013, FR-013a).
- [ ] T064 [P] [US2] Escrever `etl/tests/integracao/test_tempo_limite.py`: com `ETL_TEMPO_LIMITE_S=2` e uma fonte falsa que demora, a execução é interrompida, termina `falha` com motivo "tempo esgotado", nada é gravado e a próxima execução roda (FR-013a)
- [ ] T065 [P] [US2] Escrever `etl/tests/unidade/test_alertas.py`:
  - a mensagem tem tipo da falha e `execucao_id`;
  - `CredencialInvalida` aparece como "falha de autenticação: <credencial>";
  - falha no envio só é registrada no log e não altera o status (FR-029, FR-020a).
- [ ] T066 [US2] Escrever `etl/tests/integracao/test_falha_fonte.py`: fonte indisponível → 3 tentativas, `falha`, código 1, nenhum dado alterado, publicação não disparada, alerta chamado (FR-012, FR-016)

### Implementação da US2

- [ ] T067 [P] [US2] Implementar `etl/src/etl/pipeline/tentativas.py` e usá-lo em `etl/src/etl/adaptadores/camara/api_v2.py` até T061 passar
- [ ] T068 [P] [US2] Implementar `etl/src/etl/adaptadores/alertas/telegram.py` (`sendMessage` com `ALERTA_TELEGRAM_TOKEN`/`ALERTA_TELEGRAM_CHAT_ID`, uma nova tentativa, sem token nos logs) até T065 passar
- [ ] T069 [US2] Implementar `etl/src/etl/pipeline/vigia.py` (`signal.alarm` com `ETL_TEMPO_LIMITE_S`, padrão 3600; rollback; motivo "tempo esgotado") até T064 passar
- [ ] T070 [US2] Implementar em `etl/src/etl/pipeline/coletar.py` a recusa com código 3, o fechamento de `em_andamento` com mais de 60 min e o envio de alerta para `falha`/`com_pendencias` (etapa 9 de `contracts/etl-cli.md`) até T063 e T066 passarem
- [ ] T071 [US2] Implementar `etl/src/etl/pipeline/reserva.py` e os comandos `reserva` e `agendado` em `etl/src/etl/__main__.py` até T062 passar
- [ ] T072 [US2] Criar `etl/railway.json` (no serviço do Railway, apontar o caminho do arquivo de configuração para `etl/railway.json`, mantendo o diretório de build na raiz — T049):
  - `deploy.cronSchedule = "0 6,8 * * *"`;
  - `deploy.startCommand = "python -m etl agendado"`;
  - `deploy.preDeployCommand` = `prisma migrate deploy`;
  - `restartPolicyType = "NEVER"`;
  - retirar o `CMD` provisório de T049.
- [ ] T073 [US2] Acrescentar a `.github/workflows/publicar.yml` o passo final `if: failure()`, que envia o alerta (FR-029) com o link da execução do workflow e identifica falha de autenticação (FR-020a)
- [ ] T074 [P] [US2] Escrever `docs/05-runbooks/operacao-coleta.md`:
  - acionar coleta manual no Railway;
  - ler `execucao_etl` (status, tentativas, pendências);
  - entender os códigos de saída;
  - tabela de credenciais com data de expiração (FR-020a);
  - ajuste do horário se o horário de verão voltar;
  - o que fazer quando o limite rígido de gasto for atingido;
  - migration que falhou no pré-deploy: como confirmar que o deploy foi abortado e a versão anterior segue agendada, e como reverter (migration corretiva ou restauração — FR-017a).
- [ ] T075 [US2] ⚠️ Criar o bot do Telegram (BotFather), obter o `chat_id`, cadastrar `ALERTA_TELEGRAM_*` no Railway e no ambiente `producao` do GitHub; enviar mensagem de teste e registrar a captura em `specs/001-fundacao-tecnica/evidencias.md`
- [ ] T076 [US2] Executar os quickstart R5, R6, R9.4 e R9b e iniciar a observação de 5 dias do R9.3 (SC-002), anotando o horário de início de cada execução agendada (janela 03:00–03:15, FR-013) e a chegada de cada alerta (SC-010); anexar a evidência e as mensagens de alerta recebidas em `specs/001-fundacao-tecnica/evidencias.md`

**Checkpoint**: a coleta roda sozinha, se recupera de quedas e avisa o responsável quando falha.

---

## Phase 7: User Story 5 — Cópia de segurança e restauração comprovada (Priority: P3)

**Goal**: `pg_dump` conferido no R2 com retenção por ciclo de vida, e restauração testada.

**Independent Test**: quickstart R8.

- [ ] T077 [P] [US5] Escrever `etl/tests/unidade/test_backup_chaves.py`:
  - chave `diario/AAAA-MM-DD.dump` todo dia;
  - também `semanal/AAAA-MM-DD.dump` quando o dia, em Brasília, for domingo.
- [ ] T078 [US5] Escrever `etl/tests/integracao/test_backup.py`, com armazenamento falso em disco:
  - `pg_dump --format=custom` do banco de teste **com o papel `etl_escrita`** (prova que as permissões de T014 bastam);
  - o envio é conferido com `pg_restore --list`;
  - arquivo corrompido → `BackupInvalido`;
  - falha no envio ou na conferência → execução `com_pendencias` e alerta, com a publicação ainda disparada (FR-024, FR-026).
- [ ] T079 [US5] Implementar `etl/src/etl/adaptadores/backup_r2/backup.py` (o `pg_dump` usa `DATABASE_URL_ESCRITA`, papel `etl_escrita`) e ligá-lo na etapa 6 de `etl/src/etl/pipeline/coletar.py` até T077 e T078 passarem
- [ ] T080 [P] [US5] Criar `scripts/r2-ciclo-de-vida-backup.json` (`diario/` expira em 7 dias, `semanal/` em 28) e `scripts/r2-ciclo-de-vida-brutos.json` (365 dias), aplicados com `wrangler r2 bucket lifecycle set`
- [ ] T081 [P] [US5] Escrever `docs/05-runbooks/restauracao-backup.md`: baixar o objeto mais recente, criar banco vazio na mesma major, `pg_restore`, recriar papéis, comparar contagens por tabela, cronometrar
- [ ] T082 [US5] ⚠️ Aplicar os ciclos de vida de T080 nos buckets de produção e executar o quickstart R8 (restauração ≤ 30 min, contagens idênticas — SC-006); anexar a evidência em `specs/001-fundacao-tecnica/evidencias.md`

**Checkpoint**: cópias diárias conferidas, retenção automática, restauração provada.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T083 ⚠️ Configurar no Railway o alerta de gasto em US$ 10 e o limite rígido em US$ 20 (FR-031) e registrar a captura em `specs/001-fundacao-tecnica/evidencias.md`
- [ ] T084 [P] Atualizar `CLAUDE.md` (seção Comandos com os comandos reais de `web/` e `etl/`), `README.md` (como rodar localmente), `CONTRIBUTING.md` (pre-commit novo) e `docs/03-testing/estrategia-testes.md` (cobertura mínima definida para a F2)
- [ ] T085 [P] Conferir `docs/01-architecture/modelagem-dados.md` contra o `schema.prisma` final e corrigir divergências no mesmo PR
- [ ] T086 Executar o Lighthouse em perfil mobile no endereço publicado (SC-001, LCP ≤ 2,5 s; medição manual na F2 — automatizar no CI fica registrado no ROADMAP para a F3.3) e o `prisma migrate diff` contra produção (SC-008); anexar em `specs/001-fundacao-tecnica/evidencias.md`
- [ ] T087 Review por subagente com contexto limpo contra `plan.md`, `spec.md` e `tasks.md` (prompt de `../sdd-method/05-ciclo-da-feature.md` §8); corrigir os achados e reexecutar as suítes
- [ ] T088 Concluir a observação de 5 dias (R9.3, SC-002, horários de início dentro da janela de FR-013) e de custo (R10, SC-009); atualizar `CHANGELOG.md`, `docs/ROADMAP.md` (F2 ✓) e a fase em `CLAUDE.md`; abrir o PR `feature/001-fundacao-tecnica` → `develop` com a evidência

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: começa já. T001 (⚠️) só bloqueia T006 e o Postgres do CI (T056).
- **Foundational (Phase 2)**: depende do Setup e **bloqueia todas as histórias**.
- **US1 (Phase 3)**: depende só da Foundational. Precisa estar completa antes do Polish.
- **US3 (Phase 4)**: depende da Foundational. A T056 usa testes e build criados na US1 (T031, T047); se for feita antes da US1, os jobs de web começam com testes vazios.
- **US4 (Phase 5)**: depende da Foundational (T014).
- **US2 (Phase 6)**: depende da US1 (pipeline de T040 e workflow de T048).
- **US5 (Phase 7)**: depende da US1 (pipeline de T040) e usa o alertador da US2 (T068); sem a US2, o alerta de backup fica pendente.
- **Polish (Phase 8)**: depende de todas.

### Within Each User Story

- Testes antes da implementação; ver o teste falhar antes de implementar.
- Domínio → adaptadores → pipeline → comandos → infraestrutura → validação em produção.
- Tarefas ⚠️ podem ser adiantadas pelo responsável a qualquer momento (não dependem de código).

### Parallel Opportunities

- Setup: T003, T004, T005 e T007 em paralelo.
- Foundational: os testes T008–T012 em paralelo; depois T015, T016 e T019 em paralelo.
- US1: os testes T021–T026 e T028–T030 em paralelo; T032, T033 e T035 em paralelo; no lado `web/`, T041–T044 e T046 em paralelo com o lado `etl/` (T036–T040).
- US2: os testes T061–T065 em paralelo; T067 e T068 em paralelo.
- Com um único desenvolvedor, "paralelo" significa "em qualquer ordem dentro do bloco".

## Parallel Example: User Story 1

```bash
# Testes de domínio e adaptador (etl/) — todos em arquivos diferentes:
Task: "test_selecao.py — ordenação sem acento e escolha do primeiro (FR-006)"
Task: "test_historico.py — períodos e filiações da fixture 204496"
Task: "test_sanitizacao.py — remoção de cpf e afins"
Task: "test_api_v2.py — paginação, validação, FonteIncompleta"

# Lado web, independente do etl/:
Task: "formatar-data.test.ts — America/Sao_Paulo"
Task: "aviso-desatualizado.test.tsx — 47 h × 49 h"
```

## Implementation Strategy

### MVP primeiro (US1)

1. Setup + Foundational.
2. US1 até o checkpoint: coleta manual publica a página com fonte e data (quickstart R2, R3, R9.2).
3. **Parar e validar** com o responsável antes de seguir.

### Entrega incremental (ordem recomendada)

1. US1 → MVP do esqueleto no ar.
2. US3 → travas e CI obrigatório (protege o resto).
3. US4 → prova do acesso só leitura (curta).
4. US2 → agendamento, resiliência e alertas.
5. US5 → backup e restauração.
6. Polish → observação de 5 dias, custo, review, PR.

### Orçamento (ROADMAP F2: 25–40 h, revisto em 2026-10-20; checkpoint 23/11)

As tarefas ⚠️ (T001, T051, T057, T075, T082, T083) são do responsável e somam ~2–3 h de configuração nos painéis. A observação de 5 dias (SC-002) corre em paralelo ao Polish e não consome horas de desenvolvimento.

## Notes

- `[P]` = arquivos diferentes, sem dependência pendente.
- `[USn]` liga a tarefa à história para rastreabilidade.
- Toda evidência vai para `specs/001-fundacao-tecnica/evidencias.md` e é colada no PR.
- Commit por tarefa ou grupo coeso, em Conventional Commits; branch `feature/001-fundacao-tecnica`.
- Se a implementação revelar que o plano está errado: parar, registrar em `research.md`, atualizar `plan.md`/`tasks.md` e só então seguir (`../sdd-method/05-ciclo-da-feature.md` §7).
