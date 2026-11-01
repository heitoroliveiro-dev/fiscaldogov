# Evidências — 001 Fundação técnica

Saídas de comando e capturas que comprovam os critérios de sucesso. Os roteiros formais (R1–R10) estão em `quickstart.md`; cada um entra aqui quando executado.

## 2026-10-28 — coleta local contra a API real da Câmara (prévia da T052)

Não é o roteiro R2, porque não houve R2, GitHub nem produção. Valida o adaptador e o pipeline contra a fonte real.

**Ambiente:**
- Postgres 18 local (`docker compose`), papel `etl_escrita`, migration `0001_fundacao`.
- R2 e GitHub com credenciais fictícias, para exercitar as pendências.

```
$ python -m etl coletar --gatilho manual
codigo de saida: 0
INFO  coleta iniciada   {'execucao_id': 113}
ERROR resposta bruta não guardada  (7 URLs: 6 páginas de /deputados + /deputados/204379/historico)
ERROR disparo da publicação falhou {'execucao_id': 113}
INFO  coleta terminada  {'execucao_id': 113, 'status': 'com_pendencias',
                         'contagens': {'parlamentar': 1, 'periodo_exercicio': 1, 'filiacao': 1}}
```

**Gravado no banco:**

| nome_parlamentar | nome_ordenacao | id Câmara | UF | período | partido | fonte_url |
|---|---|---|---|---|---|---|
| Acácio Favacho | acacio favacho | 204379 | AP | desde 2023-02-01 15:05 UTC (12:05 em Brasília), titular, aberto | MDB (aberta) | `.../api/v2/deputados?itens=100&pagina=1` |

**`execucao_etl.pendencias`:**

```json
[{"etapa": "brutos", "falhas": 7},
 {"etapa": "publicacao", "tipo": "CredencialInvalida",
  "mensagem": "GitHub recusou o token de publicação (HTTP 401)"}]
```

**Conferência independente da seleção (FR-006):** as 6 páginas baixadas com `curl` trazem 513 deputados únicos. Ordenados pelo nome sem acento e em minúsculas, os três primeiros são `acacio favacho` (204379, MDB, AP), `adail filho` e `adilson barroso`.

**Achado:** os links `next` da API alternam entre `ordem=ASC&ordenarPor=nome` e a ordem padrão.
- Em 3 rodadas, os 513 vieram sem repetição.
- Mesmo assim, o adaptador passou a recusar deputado repetido entre páginas (`RespostaInvalida`), e o contrato da fonte registra a regra.

As linhas da coleta foram apagadas do banco local depois da conferência.

## 2026-10-28 — E2E local da página (T031, T047)

**Ambiente:**
- Banco `fiscaldogov_e2e` (Postgres 18 local), com a migration `0001_fundacao` e o `prisma/seed-e2e.sql`, que traz dados fictícios.
- Build lendo com `site_leitura`.

```
$ DATABASE_URL_LEITURA=postgresql://site_leitura:…@localhost:55432/fiscaldogov_e2e npm run build
Route (app)
┌ ○ /
├ ○ /_not-found
└ ○ /versao.json
$ cat out/versao.json
{"execucao_id":1,"commit":"local"}
$ grep -o '<meta name="\(robots\|versao-publicada\)"[^>]*>' out/index.html
<meta name="robots" content="noindex, nofollow"/>
<meta name="versao-publicada" content="execucao=1;commit=local"/>

$ npx playwright test
  16 passed (7.4s)
```

**Cobertura:** os 16 testes passam por 360 e 1440 px, nos temas claro e escuro, e verificam:
- elementos do contrato;
- ausência de rolagem horizontal;
- zero violações do axe (WCAG 2.2 A/AA);
- troca de tema;
- 16 px e 44 px abaixo de `lg`;
- posição da fonte (FR-003);
- `noindex` e versão publicada.

**Mutação de controle:** sem `lg:flex-row` na página, o teste do FR-003 falha (`Expected: >= 471.5625, Received: 152`). Restaurado o código, os 16 voltam a passar.

## 2026-10-28 — imagem do ETL (T049)

```
$ docker build -f etl/Dockerfile -t fiscaldogov-etl:teste .     # contexto na raiz
Successfully tagged fiscaldogov-etl:teste
$ docker run --rm fiscaldogov-etl:teste            → código 2 (sem configuração)
$ docker run --rm fiscaldogov-etl:teste pg_dump --version
pg_dump (PostgreSQL) 18.6 (Debian 18.6-1.pgdg13+2)
$ docker run --rm fiscaldogov-etl:teste sh -c 'whoami; python --version; node --version; find / -name .env | wc -l'
etl
Python 3.14.10
v24.22.2
0
$ docker run --rm --network host -e DATABASE_URL_DONO=…/fiscaldogov_e2e fiscaldogov-etl:teste \
    sh -c 'cd /app/web && node_modules/.bin/prisma migrate deploy'
1 migration found in prisma/migrations
No pending migrations to apply.
```

**Tamanho:** 1,06 GB.
- Principais partes: CLI do Prisma 256 MB, Node 122 MB e venv 90 MB.
- Aceitável para um job agendado; reduzir fica como otimização futura.

## 2026-10-28 — produção, parte 1 (T051, passos 1 e 2)

Nenhum valor de segredo nem endereço de conexão aparece aqui: o repositório é público.

**Railway:**
- Projeto `fiscaldogov`, ambiente `production`.
- Serviço `Postgres` com a imagem `postgres-ssl:18` e TCP Proxy ativo.

```
SELECT version();
PostgreSQL 18.6 (Debian 18.6-1.pgdg13+2) on x86_64-pc-linux-gnu, …

SELECT name, default_version FROM pg_available_extensions WHERE name = 'btree_gist';
btree_gist | 1.8
```

**Papéis criados pelo runbook `docs/05-runbooks/banco-papeis.md`:**
- `CREATE ROLE … LOGIN` e `\password`;
- senhas geradas com `openssl` e guardadas só no gerenciador de senhas do responsável.

```
    papel     | faz_login | tem_senha | privilegio_admin | cria_no_schema
--------------+-----------+-----------+------------------+----------------
 etl_escrita  | t         | t         | f                | f
 site_leitura | t         | t         | f                | f
```

**Pendente:** as permissões nas tabelas chegam com a migration, no primeiro deploy do ETL (passo 5). A conferência da seção 2 do runbook roda depois disso.

## 2026-10-31 — produção, parte 2 (T051, Cloudflare e GitHub)

**Cloudflare:**
- Worker `fiscaldogov` criado com o Hello World em `fiscaldogov.heitoroliveiro-dev.workers.dev`; o primeiro deploy do `publicar.yml` o substitui pelo site.
- Token de conta `fiscaldogov-publicar`, conferido na tela de revisão antes de criar:

```
NAME        fiscaldogov-publicar
EXPIRATION  October 31, 2027 (1 year)
Permission  Workers > fiscaldogov > Individual Workers Editor
IP filter   All IP addresses allowed   (runners do GitHub não têm IP fixo)
```

O valor foi copiado pelo responsável direto para o GitHub, sem passar por arquivo nem chat.

**GitHub, ambiente `producao`** (página *Configure environment*):

```
Environment secrets
CLOUDFLARE_ACCOUNT_ID
CLOUDFLARE_API_TOKEN
```

**Pendente nesta parte:** `DATABASE_URL_LEITURA` e `ALERTA_TELEGRAM_*` no ambiente; R2 (ativação, buckets e token).

## 2026-11-01 — produção, parte 3 (T051, serviço do ETL e permissões)

**GitHub, ambiente `producao`:** *Deployment branches and tags* = `Selected branches and tags`, regra `main` ("1 branch and 0 tags allowed"). O `publicar.yml` só roda na `main`, tanto no push quanto no disparo do ETL (`ref=main`).

**Railway, serviço `etl`** (região `ams`, a mesma da Postgres), configuração lida com `railway environment config`:

```
build.builder            DOCKERFILE
build.dockerfilePath     etl/Dockerfile        (contexto na raiz — T049)
deploy.preDeployCommand  sh -c 'cd /app/web && node_modules/.bin/prisma migrate deploy'
deploy.startCommand      python -m etl verificar-config   (provisório até a T072)
deploy.restartPolicyType NEVER
```

- Variáveis sem segredo: `R2_BUCKET_*`, `GITHUB_REPOSITORIO`, `CAMARA_API_URL`, `ETL_TEMPO_LIMITE_S`.
- `DATABASE_URL_DONO` é a referência `${{Postgres.DATABASE_URL}}`: a credencial do dono não sai da Railway.
- Primeiro deploy por `railway up` a partir da branch `feature/001-fundacao-tecnica`, porque a `main` ainda não tem o código. Depois do release, o serviço passa a ser ligado ao GitHub na `main`. A partir daqui, a `0001_fundacao` está aplicada em produção e não muda mais: qualquer alteração vira migration nova.

```
deployment 74fc02d0-… | SUCCESS
Applying migration `0001_fundacao`
All migrations have been successfully applied.
nivel="ERROR" mensagem="configuração inválida: DATABASE_URL_ESCRITA ausente; R2_ACCOUNT_ID ausente; …"
```

O erro do `verificar-config` é o esperado enquanto os segredos não estão cadastrados (código 2, só nomes, nenhum valor).

**Conferência da seção 2 de `docs/05-runbooks/banco-papeis.md`** (como dono), idêntica ao esperado:

```
    papel     | cria_no_schema | le | insere | trunca | le_migrations | privilegio_admin
 etl_escrita  | f              | t  | t      | f      | t             | f
 site_leitura | f              | t  | f      | f      | t             | f

 migration_name | concluida | sem_rollback
 0001_fundacao  | t         | t                      tabelas no schema public: 11
```

**Prova prática do papel de leitura** (`SET LOCAL ROLE site_leitura` como dono, transação desfeita):

```
 current_user = site_leitura
INSERT INTO partido (sigla) VALUES ('X');
ERROR:  permission denied for table partido
ROLLBACK
```

## 2026-11-01 — produção, parte 4 (T051, R2, segredos e conferência final)

**Cloudflare R2** (ativado pelo responsável, US$ 0/mês dentro da franquia):
- Buckets `fiscaldogov-brutos` e `fiscaldogov-backup`: localização automática com dica *Western Europe (WEUR)*, perto da Postgres em `ams`; classe *Standard*; acesso público desativado. As regras de ciclo de vida ficam para a T080.
- Token de conta `fiscaldogov-etl-r2`: *Object Read & Write* só nos dois buckets, TTL de 1 ano.

**GitHub:** token fine-grained `fiscaldogov-publicacao`. Acesso só ao repositório `fiscaldogov`, com *Actions: Read and write* e *Metadata: Read-only* (obrigatório); expira em 31/10/2027.

**Validade das credenciais** (vai para a tabela da T074):

| Credencial | Expira em |
|---|---|
| Cloudflare `fiscaldogov-publicar` (Workers) | 31/10/2027 |
| Cloudflare `fiscaldogov-etl-r2` (R2) | ~01/11/2027 (TTL de 1 ano) |
| GitHub `fiscaldogov-publicacao` | 31/10/2027 |

**Railway, serviço `etl`:** as 13 variáveis de `contracts/ambientes-e-segredos.md` estão presentes (conferidas só por nome e tamanho, sem espaço nas pontas). Deploy `02e1e580-…` com `SUCCESS`:

```
No pending migrations to apply.
conferencia="banco"         mensagem="conferência ok"   (papel etl_escrita, rede privada)
conferencia="r2"            mensagem="conferência ok"   (head_bucket nos dois buckets)
conferencia="api_da_camara" mensagem="conferência ok"
```

**Conferência só de leitura dos tokens que o `verificar-config` não cobre** (`railway run`, imprimindo só o status):

```
github: repositorio -> 200
github: actions/workflows -> 200 | workflows visiveis: []   (a develop, branch padrão, ainda não tem workflows)
telegram: getMe -> 200 | bot: fiscaldogovbot
telegram: getChat -> 200 | tipo: private
```

A escrita de Actions só é provada pelo disparo real do `publicar.yml` (T052).

**GitHub, ambiente `producao`:** segredos `ALERTA_TELEGRAM_CHAT_ID`, `ALERTA_TELEGRAM_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `CLOUDFLARE_API_TOKEN` e `DATABASE_URL_LEITURA`; regra de branch `main`. O `DATABASE_URL_LEITURA` é provado no primeiro build do `publicar.yml` (T052).

## 2026-11-01 — travas de qualidade (US3: T053–T056)

**pre-commit (T053, T054)**, testado com arquivos temporários staged, sem commit:

| Caso | Resultado |
|---|---|
| `web/`: `export const   valorTeste=1` | código 0; corrigido para `export const valorTeste = 1;` e reposto no stage |
| `web/`: `export const valor: any = 1;` | código 1 — `error  Unexpected any … no-explicit-any` |
| `web/`: `formatar-data.ts` quebrado | código 1 — `tests/formatar-data.test.ts (3 tests \| 3 failed)` |
| `web/`: arquivo sem teste relacionado | `vitest related`: "No affected test files found", código 0 |
| `etl/`: `x   =  1` | código 1 — `1 file would be reformatted` |
| `etl/`: `x = 1` | código 0 — `126 passed, 37 deselected` |
| `etl/` com `PATH` sem `uv` | código 1 — `BLOQUEADO: uv não encontrado. Instale: …` |

Aviso de lint (ex.: variável não usada) não bloqueia, como no `npm run lint` do CI.

**Contrato schema ↔ ETL (T055):** `39 passed` na integração local. Num banco descartável com `ALTER TABLE parlamentar RENAME COLUMN url_foto TO foto`, o teste falha com `AssertionError: assert {'parlamentar': ['url_foto']} == {}`.

**CI (T056)**, PR #8 (rascunho, `feature/001-fundacao-tecnica` → `develop`):
- `actionlint` 1.7.12 sem achados em `ci.yml` e `publicar.yml`.
- Primeira execução: os 3 jobs do ETL falharam com ``Unable to resolve action `astral-sh/setup-uv@v10` `` (a action não publica tag flutuante). Corrigido em `0ebf4c9`, fixando `v10.3.0`.
- Execução `41335769946` no commit `0ebf4c9`: os 7 jobs com `success`.

```
web-lint         success   lint + typecheck + format:check; prisma generate sem DATABASE_URL_DONO
web-test         success   Test Files 3 passed (3) · Tests 11 passed (11)   (dados.test.ts com o banco: 5)
web-build        success   Postgres 18 + papéis + migrate deploy + seed-e2e + next build → artefato out/
web-e2e          success   Playwright + axe sobre o out/ do web-build
etl-lint         success   ruff format --check + ruff check
etl-test         success   pytest -m "not integration"
etl-integration  success   39 passed, 126 deselected   (ETL_EXIGIR_INTEGRACAO=1)
```

O `web-test` ganhou Postgres de serviço: sem ele, o `dados.test.ts` seria pulado em silêncio (`1 skipped`, `5 skipped` sem o banco).

## 2026-11-01 — proteção de `main` e `develop` (T057)

Ruleset `protecao-main-develop` (id 26321483): *Active*, lista de exceções vazia (nem o administrador passa), alvos `main` e `develop`. Regras em vigor, lidas da API pública (`GET /repos/heitoroliveiro-dev/fiscaldogov/rules/branches/{main,develop}`), iguais nas duas branches:

```
deletion                       (proíbe apagar a branch)
non_fast_forward               (proíbe force push)
pull_request (aprovacoes=0)    (PR obrigatório; 0 aprovações porque o autor não aprova o próprio PR)
required_status_checks web-lint,web-test,web-build,web-e2e,etl-lint,etl-test,etl-integration (strict=False)
```

## 2026-11-01 — quickstart R7 (T058)

**Passos 1–3**, com `git commit` de verdade na `feature/001-fundacao-tecnica`. Os três commits foram recusados e o HEAD ficou em `807b1cc`:

```
1. web/: export const valor: any = 1;      → git commit saída 1
   1:21  error  Unexpected any. Specify a different type  @typescript-eslint/no-explicit-any
2. etl/: x   =  1                          → git commit saída 1
   1 file would be reformatted, 43 files already formatted
3. etl/: teste de unidade assert 1 == 2   → git commit saída 1
   FAILED tests/unidade/test_config.py::test_r7_quebrado - assert 1 == 2
   1 failed, 126 passed, 39 deselected
```

**Passo 4**, PR #9 (`chore/r7-pr-com-teste-falhando` → `develop`, não rascunho). O teste `etl/tests/unidade/test_r7_ci.py` falha só com `CI=true`: passa no pre-commit, então não precisou de `--no-verify`, e fica vermelho no Actions.
- Checks no commit `5bcf6e2`: `etl-test` com `failure`; os outros 6 com `success`. Todos marcados como *Required*.
- Caixa de merge: "Some checks were not successful — 1 failing, 6 successful checks", com o botão **Merge pull request desabilitado** ("Merging is blocked due to failing merge requirements").
- PR #9 fechado sem merge. A branch `chore/r7-pr-com-teste-falhando` continua no remoto, aguardando confirmação para ser apagada.
