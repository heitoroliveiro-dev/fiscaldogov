# Contrato — ambientes, variáveis e segredos

Nenhum valor real no repositório (princípio VI). `.env.example` em `etl/` e `web/` lista os nomes, sem valores.

## Railway — serviço do ETL (cron `0 6,8 * * *`, reinício: nunca)

| Variável | Conteúdo | Segredo? |
|---|---|---|
| `DATABASE_URL_ESCRITA` | Conexão pela rede privada com o papel `etl_escrita` | sim |
| `DATABASE_URL_DONO` | Conexão com o usuário dono — usada **só** no comando de pré-deploy (`prisma migrate deploy`) | sim |
| `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` | Token do R2 restrito aos dois buckets | sim |
| `R2_BUCKET_BRUTOS`, `R2_BUCKET_BACKUP` | `fiscaldogov-brutos`, `fiscaldogov-backup` | não |
| `GITHUB_TOKEN_PUBLICACAO` | Token fine-grained: só este repositório, permissão de Actions (escrita) ⚠️ confirmar | sim |
| `GITHUB_REPOSITORIO` | `heitoroliveiro-dev/fiscaldogov` | não |
| `CAMARA_API_URL` | Padrão: URL oficial | não |
| `ETL_TEMPO_LIMITE_S` | Padrão: 3600 | não |
| `ALERTA_TELEGRAM_TOKEN`, `ALERTA_TELEGRAM_CHAT_ID` | Bot e conversa do canal de alertas (RNF07) | sim |

## Railway — Postgres

- Proxy público TCP habilitado (TLS), usado **apenas** pelo build com `site_leitura`.
- Papéis `etl_escrita` e `site_leitura` criados uma vez pelo runbook `docs/05-runbooks/banco-papeis.md`.

## GitHub Actions — ambiente `producao` (workflow `publicar.yml`)

| Segredo | Conteúdo |
|---|---|
| `DATABASE_URL_LEITURA` | Proxy público, papel `site_leitura`, `sslmode=require` |
| `CLOUDFLARE_API_TOKEN` | Token restrito a "Workers Scripts: Edit" na conta do projeto |
| `CLOUDFLARE_ACCOUNT_ID` | ID da conta |
| `ALERTA_TELEGRAM_TOKEN`, `ALERTA_TELEGRAM_CHAT_ID` | Mesmo canal de alertas |

## GitHub Actions — CI (`ci.yml`)

Sem segredos. Postgres de serviço com senhas de teste definidas no próprio workflow (banco efêmero, descartado ao fim do job).

## Validade das credenciais

`docs/05-runbooks/operacao-coleta.md` mantém uma tabela com cada credencial que expira (token do GitHub, token da Cloudflare, token do R2) e a data de expiração (FR-020a).

## Rotação

Trocar uma credencial = atualizar o valor no cofre do provedor e, para papéis do banco, `ALTER ROLE ... PASSWORD` pelo runbook. Nenhum código muda.
