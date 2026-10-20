# Research — 001 Fundação técnica

Decisões técnicas da feature, com alternativas descartadas. Versões verificadas em 2026-10-20 (PyPI, npm). A stack-base vem do ADR-0001; a hospedagem, do ADR-0002; a organização do ETL, do ADR-0003.

## 1. Versões e dependências

| Parte | Escolha (major fixada) | Observação |
|---|---|---|
| Node | 24 LTS | Prisma 7 exige ≥ 20.19 |
| Next.js / React | 16.4 / 19.3 | mesmas do design system |
| TypeScript | **6.x** | a 7.0 (nova implementação) já saiu, mas o design system usa a 6; trocar depois é decisão deliberada |
| Tailwind CSS | 4.3 | do design system |
| Prisma ORM | **7.x** (`prisma`, `@prisma/client`, `@prisma/adapter-pg` 7.10) | a 8.0 está em release candidate |
| ESLint / Vitest / Playwright / axe | 10 / 5 / 1.64 / `@axe-core/playwright` 4.14 | |
| Wrangler | 4.x | publicação na Cloudflare |
| Python | 3.14 | |
| SQLAlchemy / psycopg | 2.1 / 3.3 | Core + reflection (ADR-0001) |
| httpx | 0.28 | cliente HTTP com timeout explícito |
| pytest / ruff | 9.1 / 0.17 | |
| boto3 | 1.43 | R2 pela API compatível com S3 |
| Gerenciadores | npm (lockfile) · uv (`uv.lock`) | |

- **Decisão:** sem biblioteca de nova tentativa (ex.: tenacity). A regra de FR-013 cabe numa função pequena e testável.
  - **Por quê:** é uma dependência a menos, e o comportamento fica explícito no teste.
  - **Alternativa descartada:** tenacity — poderosa, mas exagerada para "3 tentativas com espera crescente".
- **Decisão:** sem pydantic na F2. Os adaptadores convertem o JSON da fonte em dataclasses do domínio, com validação explícita dos campos usados.
  - **Alternativa descartada:** pydantic — reavaliar na HU01, quando XML e HTML entram.

## 2. Prisma 7

- **Decisão:** `web/prisma.config.ts` define o schema, as migrations e a URL de conexão.
  - O `.env` é carregado explicitamente com `dotenv`.
  - Generator `prisma-client` com `output` dentro de `web/src/generated/prisma` (fora do versionamento).
  - O Client usa `@prisma/adapter-pg`. Pacote ESM (`"type": "module"`).
- **Por quê:** são as mudanças obrigatórias do Prisma 7 (driver adapter, `prisma.config.ts`, ESM, `.env` não carregado sozinho, `migrate dev` não roda `generate`).
- **Alternativa descartada:** Prisma 6 — evita as mudanças, mas nasce numa versão que já tem sucessora estável.

## 3. Quem aplica as migrations

- **Decisão:** três papéis no Postgres.
  - **dono** (o usuário administrador do Railway): só aplica migrations.
  - **`etl_escrita`:** só DML (`SELECT/INSERT/UPDATE/DELETE`), sem DDL.
  - **`site_leitura`:** só `SELECT`.
- **Como as migrations rodam:** com `prisma migrate deploy` como comando de pré-deploy do serviço do ETL no Railway. A imagem do ETL inclui Node e o CLI do Prisma só para isso.
- **Por quê:** a credencial de dono e a de escrita nunca saem do Railway (ADR-0002); o ETL nem consegue alterar a estrutura (menor privilégio, princípio V); schema e código do ETL são publicados juntos a partir de `main`.
- **Papéis e permissões:**
  - Os papéis são **criados uma vez**, pelo runbook, com senha definida no painel. Senha nunca aparece em migration.
  - As migrations só fazem `GRANT` e `ALTER DEFAULT PRIVILEGES`.
  - No CI, um script de preparo cria os papéis com senhas de teste.
- **Alternativas descartadas:**
  - *Migrations num job do GitHub Actions:* a credencial de dono ficaria no GitHub.
  - *ETL com papel de dono:* a coleta poderia apagar a estrutura.
- **Corrida conhecida:** um merge em `main` dispara ao mesmo tempo o build do site (GitHub) e o deploy do ETL (Railway). Se o build ler o banco antes da migration, ele falha e a versão anterior fica no ar (FR-016). A próxima coleta bem-sucedida republica. Aceito.

## 4. Coleta da F2 (fonte: API v2 da Câmara)

- **Seleção (FR-006):**
  1. `GET /deputados` sem parâmetro de tempo, que lista os deputados **em exercício no momento da requisição**, paginado.
  2. Ordenar pelo nome parlamentar normalizado: minúsculas, sem acento (`unicodedata`, independente de locale).
  3. Escolher o primeiro.
- **Dados do selecionado:** `GET /deputados/{id}/historico` dá os períodos de exercício e as filiações (ADR-0003 §3).
- **Endpoint evitado:** **`GET /deputados/{id}` não é chamado** — ele devolve CPF, e a resposta bruta seria guardada no R2.
- **Defesa extra:** antes de guardar qualquer resposta bruta, o adaptador remove campos de uma lista de bloqueio (`cpf`, …), com teste. A resposta guardada é documentada como "bruta sanitizada".
- **Atualização dos já armazenados:** a cada execução, o ETL também atualiza o histórico de **todos os parlamentares já armazenados**. Assim, se o selecionado sai de exercício, o período dele é fechado e ele não continua aparecendo.
- **Alternativa descartada:** coletar os 513 já na F2. É o escopo da F3.1, e dobraria o tempo de coleta e de teste agora.
- **Educação com a fonte:**
  - `User-Agent` identificando o projeto e o repositório público;
  - timeout de 30 s por requisição;
  - no máximo 4 requisições simultâneas.

## 5. Transação, nova tentativa, tempo limite e reserva

- **Transação:** cada execução grava tudo numa **única transação**. Falha em qualquer etapa → `ROLLBACK` (FR-012).
- **Registro da execução:** `execucao_etl` é inserida antes, em transação separada, com status `em_andamento`, e atualizada no fim.
- **Nova tentativa (FR-013):** até 3 tentativas por requisição, com espera de 5 s, 20 s e 60 s. Vale só para falhas de rede, tempo esgotado e respostas HTTP 5xx ou 429. Resposta 4xx ou formato inesperado falha na hora.
- **Tempo limite (FR-013a):**
  - um vigia de 60 min no processo (`signal.alarm`), que desfaz a transação, marca `falha` com motivo "tempo esgotado" e encerra com código ≠ 0;
  - mais `statement_timeout` na sessão do banco;
  - a política de reinício do serviço no Railway fica em "nunca".
- **Reserva das 05:00:**
  - O cron é `0 6,8 * * *` (UTC), ou seja, 03:00 e 05:00 em Brasília.
  - A execução das 05:00 verifica se houve `sucesso` ou `com_pendencias` hoje. Se houve, registra `dispensada` e encerra. Se não, coleta.
  - Uma `em_andamento` com mais de 60 min é tratada como falha.
- **Alternativa descartada:** um segundo serviço cron só para a reserva — mais configuração para a mesma lógica.

## 6. Respostas brutas e backup no R2

- **Respostas brutas (FR-011):**
  - bucket `fiscaldogov-brutos`, chave `camara/api-v2/<caminho>/<sha256>.json.gz`;
  - só grava se o hash difere da última `coleta_bruta` da mesma URL;
  - **regra de ciclo de vida do R2** apaga após 365 dias.
- **Backup (FR-024):**
  - `pg_dump --format=custom` ao fim de cada coleta bem-sucedida;
  - bucket `fiscaldogov-backup`, prefixo `diario/` (ciclo de vida: 7 dias);
  - aos domingos, também em `semanal/` (ciclo de vida: 28 dias).
  - **A retenção é feita pelo R2, sem código de limpeza.**
- **Imagem do ETL:** inclui `postgresql-client` da mesma major do servidor.
- **Alternativa descartada:** retenção calculada pelo ETL. Exigiria código e teste para uma regra que o armazenamento já oferece.
- **Falha do backup (FR-026):** a execução vira `com_pendencias`, e a publicação segue.

## 7. Publicação

- **Workflow `publicar.yml`:** disparado por `workflow_dispatch` (pelo ETL, via API do GitHub) e por `push` em `main`.
- **Concorrência:** `concurrency` com cancelamento da execução anterior em andamento.
- **Passos:** `npm ci` → `prisma generate` → `next build` (`output: 'export'`, lê com `site_leitura`) → `wrangler deploy` (Workers static assets, sem script). Se algum passo falhar, a versão anterior continua no ar.
- **Credencial do ETL para disparar:** token fine-grained restrito a este repositório. **Permissão esperada: Actions — escrita.** A documentação da API só cita o escopo dos tokens clássicos; confirmar na criação (⚠️).
- **Fora dos buscadores (FR-005):** `<meta name="robots" content="noindex">` em toda página e arquivo `_headers` com `X-Robots-Tag: noindex` (suportado pelos static assets, até 100 regras).
- **Data exibida (FR-002):** `terminada_em` da última execução com `sucesso` ou `com_pendencias` no momento do build, formatada em `America/Sao_Paulo`. Corresponde sempre à versão publicada.

## 8. Design system

- **Decisão:** adoção pela **opção B** do design system (`docs/08-uso-em-novos-projetos.md`).
  - Copiar `tokens/`, `scripts/` (geração de tokens com verificação WCAG), `src/styles/`, `src/lib/utils.ts`, `components.json` e **só os componentes usados** (Card, Badge, Button e Separator).
  - Troca de tema com `next-themes` (D3: segue o sistema, com troca manual).
- **Alternativa descartada:** opção A (clonar o template inteiro). Traz páginas de documentação e componentes sem uso que precisariam ser apagados.
- Aplicar as adaptações D1–D2 (corpo 16 px e alvos de 44 px abaixo de `lg`) já no esqueleto.

## 9. Travas locais e CI

- **pre-commit (`.githooks/pre-commit`):** mantém as travas atuais e, conforme os arquivos staged:
  - **`web/`:** `lint-staged` com ESLint, Prettier e `vitest related --run`;
  - **`etl/`:** `ruff format --check`, `ruff check` e a suíte de unidade (`pytest -m "not integration"`), que é rápida.
  - Se a ferramenta não estiver instalada, o hook **falha** com instrução (falha fechada).
- **CI (`ci.yml`), um job por check:**

| Job | Inclui |
|---|---|
| `web-lint` | lint + typecheck |
| `web-test` | Vitest |
| `web-build` | Postgres de serviço + migrations + dado de exemplo + `next build` |
| `web-e2e` | Playwright sobre o `out/` servido localmente: 360 e 1440 px, claro e escuro, axe |
| `etl-lint` | ruff |
| `etl-test` | unidade + teste de arquitetura |
| `etl-integration` | Postgres de serviço com papéis + `prisma migrate deploy` + pytest de integração: contrato schema↔ETL, papel de leitura recusado, invariantes |

- **Banco do CI:** a mesma major do Railway, num container de serviço do GitHub Actions.
- **Alternativa descartada:** Testcontainers no CI. O container de serviço é nativo do GitHub Actions; o Testcontainers fica para testes locais, se fizer falta.
- **Proteção de branches:** os 7 jobs como checks obrigatórios em `main` e `develop` (⚠️ configuração do responsável).

## 10. Pendências de verificação (⚠️, na implementação)

- Major do Postgres oferecida pelo Railway na criação do serviço; CI e `postgresql-client` acompanham.
- Extensão `btree_gist` disponível no Railway (necessária à restrição de não sobreposição dos períodos).
- Permissão exata do token fine-grained para `workflow_dispatch`.
- Geração das imagens de prévia na exportação estática fica para a F3.3 (RF10); não há prévia na F2.
