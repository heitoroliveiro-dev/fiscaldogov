# Quickstart — validação da 001 Fundação técnica

Roteiros checáveis: **ação → resultado esperado**. Cada um gera a evidência anexada ao PR (comando + saída, ou captura de tela). Detalhes de interface em `contracts/`; de dados, em `data-model.md`.

## Pré-requisitos locais

- Node 24, Python 3.14, uv, Docker.
- `git config core.hooksPath .githooks`
- `etl/.env` e `web/.env` copiados dos `.env.example`, apontando para o Postgres local.

## R1 — Ambiente local do zero (SC-008, FR-017)

1. Subir um Postgres local (mesma major do Railway) e criar os papéis com o script de preparo de desenvolvimento.
2. `npm --prefix web run db:migrate:deploy`
3. **Esperado:** migrations aplicadas sem erro; `\dt` lista as 10 tabelas de `data-model.md` mais a `_prisma_migrations`, que o Prisma cria; extensão `btree_gist` presente.

## R2 — Coleta manual ponta a ponta (US1, FR-006 a FR-012)

1. `uv run --directory etl python -m etl coletar --gatilho manual`
2. **Esperado:** código de saída 0; `execucao_etl` com `sucesso`, contagens preenchidas e `versao_codigo` = commit atual; um parlamentar com `fonte_url` e `coletado_em`; períodos e filiação aberta coerentes com o histórico da Câmara; nenhum campo de CPF no banco nem nos objetos do bucket de brutos local.
3. Rodar de novo. **Esperado:** nenhuma `coleta_bruta` nova (hash igual) e os mesmos registros (idempotência).

## R3 — Página gerada (US1, FR-001 a FR-005)

1. `npm --prefix web run build` e servir `web/out/` localmente.
2. **Esperado:** a página mostra aviso de testes, nome, partido · UF, "Fonte: Câmara dos Deputados", link para `https://www.camara.leg.br/deputados/{id}` e "Atualizado em … (horário de Brasília)" igual a `terminada_em` da execução do R2; HTML com `noindex`; `out/_headers` com `X-Robots-Tag: noindex`.
3. `npm --prefix web run test:e2e` **Esperado:** testes verdes em 360 px e 1440 px × claro e escuro; zero violações do axe; nenhuma rolagem horizontal (SC-007).

## R3b — Aviso de dado envelhecido e versão publicada (FR-002a, FR-028, SC-011)

1. Gerar o site com uma execução cuja `terminada_em` seja 49 h atrás e abrir a página. **Esperado:** aviso "Atenção: os dados podem estar desatualizados." visível.
2. Repetir com 47 h. **Esperado:** sem aviso.
3. Abrir `/versao.json`. **Esperado:** `execucao_id` e commit da geração.

## R4 — Acesso só leitura (US4, SC-005)

1. Com `site_leitura`, tentar `INSERT`, `UPDATE`, `DELETE` numa tabela e `CREATE TABLE`.
2. **Esperado:** todas recusadas com "permission denied"; `SELECT` funciona. (Também coberto por teste de integração no CI.)

## R5 — Falha da fonte e nova tentativa (US2, FR-012, FR-013)

1. `CAMARA_API_URL=http://127.0.0.1:9 uv run --directory etl python -m etl coletar`
2. **Esperado:** três tentativas registradas em `execucao_etl.tentativas` (esperas de 5 s, 20 s e 60 s; reduzidas por variável apenas em teste), status `falha`, código de saída 1, nenhum registro de dado alterado, nenhuma publicação disparada.
3. `python -m etl reserva` logo depois, com a fonte normal. **Esperado:** executa a coleta (não houve sucesso no dia) e termina com `sucesso`.
4. `python -m etl reserva` de novo. **Esperado:** `dispensada`.
5. Conferir o canal de alertas. **Esperado:** uma mensagem para a falha do passo 2, com o `execucao_id` (SC-010).
6. Disparar `coletar` duas vezes ao mesmo tempo. **Esperado:** a segunda termina com código 3 ("já há uma coleta em andamento").
7. Marcar manualmente uma execução como `em_andamento` iniciada há 2 h e rodar `coletar`. **Esperado:** ela é fechada como `falha` ("interrompida") e um alerta é enviado.

## R6 — Tempo esgotado (FR-013a)

1. Com um servidor local que demora a responder e `ETL_TEMPO_LIMITE_S=10`, rodar `coletar`.
2. **Esperado:** interrupção em ~10 s, status `falha` com motivo "tempo esgotado", nada gravado; a execução seguinte roda normalmente.

## R7 — Travas locais (US3, SC-004)

1. Introduzir um erro de estilo em `web/` e tentar `git commit`. **Esperado:** bloqueado pelo ESLint/Prettier.
2. Introduzir um erro de formatação em `etl/` e tentar `git commit`. **Esperado:** bloqueado pelo ruff.
3. Quebrar um teste de unidade e tentar `git commit`. **Esperado:** bloqueado.
4. Abrir um PR com um teste falhando. **Esperado:** check vermelho e merge impedido pela proteção de branch (⚠️ configurada pelo responsável).

## R8 — Backup e restauração (US5, SC-006)

1. Após uma coleta bem-sucedida, listar `fiscaldogov-backup/diario/`. **Esperado:** um objeto com a data do dia.
2. Seguir `docs/05-runbooks/restauracao-backup.md` num Postgres vazio, cronometrando.
3. **Esperado:** concluído em ≤ 30 min; contagem de linhas por tabela idêntica à origem.
4. Conferir as regras de ciclo de vida dos buckets (`wrangler r2 bucket lifecycle list`): 7 dias em `diario/`, 28 em `semanal/`, 365 nos brutos.

## R9 — Produção ponta a ponta (US1, US2, SC-001 a SC-003)

1. Merge em `main` → deploy do ETL no Railway (pré-deploy aplica migrations) e publicação do site.
2. Acionar `coletar --gatilho manual` no Railway. **Esperado:** em poucos minutos o `*.workers.dev` mostra o deputado e a nova data.
3. Por 5 dias seguidos, registrar a data exibida às 08:00. **Esperado:** sempre a do dia (SC-002).
4. Revogar temporariamente a credencial de leitura do build e acionar a publicação. **Esperado:** publicação falha, o site continua no ar com a data anterior e chega o alerta de "falha de autenticação" (SC-003, SC-010). Restaurar a credencial.
5. Lighthouse em perfil mobile no endereço publicado. **Esperado:** LCP ≤ 2,5 s (SC-001).
6. `prisma migrate diff` entre as migrations do repositório e o banco de produção (lendo com `site_leitura`). **Esperado:** sem diferenças (SC-008).

## R9b — Migration que falha (FR-017a)

1. Num banco local com as migrations atuais aplicadas, rodar o mesmo comando de pré-deploy do Railway (`prisma migrate deploy`) numa branch de teste com uma migration propositalmente inválida, usando a imagem do ETL de T049.
2. **Esperado:** `prisma migrate deploy` sai com código ≠ 0 e o banco fica sem a mudança parcial. No Railway, um código ≠ 0 no pré-deploy aborta a implantação e mantém a versão anterior ativa — conferir na primeira implantação real e registrar em `evidencias.md`.

## R10 — Custo (SC-009, FR-031)

Conferir no painel do Railway o alerta de gasto em US$ 10 e o limite rígido em US$ 20. Após 7 dias em produção, conferir o uso do Railway e da Cloudflare. **Esperado:** limites configurados; projeção mensal ≤ US$ 10.
