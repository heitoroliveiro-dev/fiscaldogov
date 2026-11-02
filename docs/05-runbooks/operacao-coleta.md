# Runbook — operação da coleta (ETL)

Como acompanhar, acionar e destravar a coleta diária e a publicação. Base: `specs/001-fundacao-tecnica` (US2, FR-013, FR-013a, FR-017a, FR-020a, FR-029, FR-031) e `contracts/etl-cli.md`.

## Como a coleta roda

- Serviço `etl` no Railway, configurado por `etl/railway.json`: cron `0 6,8 * * *` (UTC), sem reinício automático, pré-deploy `prisma migrate deploy`.
- O cron roda `python -m etl agendado`. Às **06h UTC (03:00 em Brasília)** ele coleta. Em **qualquer outro horário**, inclusive às 08h UTC, roda a **reserva**: coleta só se ainda não houve `sucesso` ou `com_pendencias` no dia de Brasília, e senão registra `dispensada`.
- Coleta terminada com dados gravados → dispara o `publicar.yml` (GitHub), que gera o site e publica na Cloudflare.
- `falha`, `com_pendencias`, execução interrompida e publicação com falha → alerta no Telegram (bot `fiscaldogovbot`).

## 1. Acionar a coleta fora do horário

```bash
railway cron run --service etl --yes        # enfileira; aparece em `railway cron list` em alguns minutos
railway cron list --service etl --limit 5
railway logs --service etl                  # registros em JSON, sem credenciais
```

Isto roda `agendado`, que fora das 06h UTC é a reserva: **se a coleta de hoje já deu certo, a execução é `dispensada`**.

Para forçar uma nova coleta no mesmo dia (ex.: depois de corrigir um dado na fonte):
1. Painel do Railway → serviço `etl` → *Settings* → *Custom Start Command*: `python -m etl coletar --gatilho manual`.
2. `railway cron run --service etl --yes`.
3. **Volte** o comando para `python -m etl agendado` logo depois. Esquecer isso faz o cron das 08h coletar de novo todo dia.

Não dá para rodar a coleta da sua máquina com `railway run`: a URL do banco usa a rede privada (`*.railway.internal`).

## 2. Ler o resultado (`execucao_etl`)

Como dono, com `railway connect Postgres`:

```sql
SELECT id, gatilho, status, iniciada_em AT TIME ZONE 'America/Sao_Paulo' AS inicio_brasilia,
       terminada_em - iniciada_em AS duracao, contagens, tentativas, erros, pendencias
FROM execucao_etl ORDER BY id DESC LIMIT 10;
```

| Status | Quer dizer | O que fazer |
|---|---|---|
| `sucesso` | dados gravados, brutos guardados, publicação disparada | nada |
| `com_pendencias` | dados gravados, mas falhou bruto, backup ou disparo | ver `pendencias`; a próxima coleta repete o que faltou |
| `falha` | nada gravado (rollback) | ver `erros`; a reserva das 05:00 tenta de novo |
| `dispensada` | reserva desnecessária (já houve sucesso no dia) | nada |
| `em_andamento` | rodando agora | se passar de 60 min, a próxima execução a fecha como `falha` ("interrompida") |

- `tentativas`: cada requisição à Câmara que falhou de forma passageira (rede, tempo esgotado, 5xx, 429), com o número da tentativa e a espera. São até 3 no total, com 5 s e 20 s de espera.
- `erros[].etapa = "vigia"`: `TempoEsgotado` (passou do `ETL_TEMPO_LIMITE_S`, padrão 3600 s) ou `interrompida` (processo morreu sem registrar o fim).

## 3. Códigos de saída

| Código | Significado | No painel do Railway |
|---|---|---|
| 0 | `sucesso`, `com_pendencias` ou `dispensada` | run bem-sucedido |
| 1 | `falha` | run com falha + alerta no Telegram |
| 2 | configuração inválida (variável ausente) | run com falha, **sem alerta** (o próprio canal pode ser a variável ausente); o log lista só os nomes |
| 3 | já havia uma coleta em andamento há menos de 60 min | run com falha; nada gravado. Normal se dois acionamentos se cruzarem |

Diagnóstico sem gravar nada: troque temporariamente o *Custom Start Command* para `python -m etl verificar-config` e rode `railway cron run`. Ele confere variáveis, banco, R2 e a API da Câmara.

## 4. Credenciais que expiram (FR-020a)

Falha de autenticação chega no alerta como `falha de autenticação: <credencial>`.

| Credencial | Onde fica | Expira em | Como renovar |
|---|---|---|---|
| Cloudflare `fiscaldogov-publicar` (Workers, só o Worker `fiscaldogov`) | GitHub → ambiente `producao` → `CLOUDFLARE_API_TOKEN` | 31/10/2027 | Cloudflare → *Account API tokens* → *Roll* → atualizar o segredo |
| Cloudflare `fiscaldogov-etl-r2` (R2, *Object Read & Write* nos dois buckets) | Railway → `etl` → `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | ~01/11/2027 | R2 → *Manage API tokens* → criar outro com o mesmo escopo → trocar as duas variáveis → apagar o antigo |
| GitHub `fiscaldogov-publicacao` (fine-grained, *Actions: Read and write*, só este repositório) | Railway → `etl` → `GITHUB_TOKEN_PUBLICACAO` | 31/10/2027 | GitHub → *Settings* → *Developer settings* → *Fine-grained tokens* → *Regenerate* |
| Senhas de `etl_escrita` e `site_leitura` | Railway (`DATABASE_URL_ESCRITA`) e GitHub (`DATABASE_URL_LEITURA`) | não expiram | `docs/05-runbooks/banco-papeis.md` §3 |
| Bot do Telegram | Railway e GitHub (`ALERTA_TELEGRAM_*`) | não expira | @BotFather → `/revoke` gera outro token |

Coloque um lembrete no calendário **30 dias antes** de cada data.

## 5. Horário de verão

O cron é em UTC e o Brasil está sem horário de verão (03:00 = 06:00 UTC). Se o horário de verão voltar (UTC−2), a coleta passa a rodar às 04:00 locais, ainda antes do prazo das 08:00, e **nada quebra**. Para voltar às 03:00, mude as duas coisas no mesmo PR:
- `etl/railway.json`: `cronSchedule` para `"0 5,7 * * *"`;
- `etl/src/etl/pipeline/reserva.py`: `HORA_DA_COLETA_UTC = 5`.

Mudar só uma delas faz a coleta das 03:00 virar reserva, ou o contrário.

## 6. Limite rígido de gasto atingido (FR-031)

O Railway tem alerta em US$ 10 e limite rígido em US$ 20 (T083). Atingido o limite, **os serviços param**: a coleta não roda, o banco fica fora do ar e o site **continua no ar com o último dado**. Depois de 48 h, o aviso de dado desatualizado aparece sozinho na página (FR-002a).

1. Railway → *Usage*: ver qual serviço consumiu (o volume do Postgres e o tempo de CPU do ETL são os candidatos).
2. Corrigir a causa (ex.: coleta presa em laço, volume crescendo) **antes** de subir o limite.
3. Subir o limite em *Usage → Limits* só o necessário para o mês, e registrar o motivo no `docs/ROADMAP.md`.

## 7. Migration que falhou no pré-deploy (FR-017a)

O pré-deploy roda `prisma migrate deploy` antes de trocar a versão. Se ele sair com código ≠ 0, **a implantação é abortada e a versão anterior continua ativa e agendada**.

Confirmar:

```bash
railway deployment list --service etl     # o novo aparece como FAILED; o anterior segue SUCCESS
railway logs --service etl --deployment <id-do-que-falhou>
```

Como dono, ver em que estado a migration ficou:

```sql
SELECT migration_name, started_at, finished_at, rolled_back_at, logs
FROM _prisma_migrations ORDER BY started_at DESC LIMIT 3;
```

- `finished_at` nulo: a migration falhou no meio. O Postgres desfaz o DDL da transação, e o Prisma marca como falha. **O próximo deploy fica bloqueado** até resolver.
- **Corrigir para a frente** (preferido): conserte a migration num PR. Se ela nunca chegou a aplicar nada, marque como desfeita e deixe o próximo deploy reaplicar:

  ```bash
  # do repositório, com a URL pública do dono (painel do Railway → Postgres → Connect)
  DATABASE_URL_DONO='<url pública do dono>' npx --prefix web prisma migrate resolve --rolled-back <nome_da_migration>
  ```
- **Restaurar** (se a migration aplicou parte e deixou dado inconsistente): siga `docs/05-runbooks/restauracao-backup.md` com a cópia do dia e depois aplique a migration corrigida.

Nunca edite uma migration que já foi aplicada em produção. A correção vai numa migration nova.
