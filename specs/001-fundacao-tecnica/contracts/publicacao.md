# Contrato — publicação do site (`.github/workflows/publicar.yml`)

## Gatilhos

| Gatilho | Origem | Entrada |
|---|---|---|
| `workflow_dispatch` | ETL, ao fim de coleta com `sucesso` ou `com_pendencias` | `execucao_id` (texto, para rastreio no log) |
| `push` em `main` | Merge de release/hotfix | — |

`concurrency: { group: publicar, cancel-in-progress: true }`. Roda sempre a partir de `main`.

## Passos

1. `npm ci` em `web/`.
2. `prisma generate`.
3. `npm run build`: geração de tokens + `next build` com `output: 'export'`, lendo `DATABASE_URL_LEITURA`.
4. Conferência do resultado: `out/index.html` existe e contém `noindex`; `out/_headers` existe.
5. `wrangler deploy` (Workers static assets, `assets.directory = "./out"`, sem script).

## Garantias

- Qualquer passo falhando → nada é publicado; a versão anterior segue no ar (FR-016). Falha notificada pelo e-mail padrão do GitHub (alertas ativos: F4).
- O workflow nunca escreve no banco (só tem a credencial de leitura).
- Endereço da F2: subdomínio `*.workers.dev` da conta (FR-027).
