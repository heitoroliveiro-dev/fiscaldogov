# Runbook — restaurar a cópia de segurança

Restaura o banco a partir do `pg_dump` guardado no R2. Base: FR-024 e SC-006 (restauração em até 30 min, com contagens idênticas) e research §6 da spec 001.

## O que existe no R2

Bucket `fiscaldogov-backup`, um `pg_dump --format=custom` por coleta bem-sucedida, já conferido com `pg_restore --list` no momento do envio:

| Prefixo | Quando | Retenção (ciclo de vida do bucket) |
|---|---|---|
| `diario/AAAA-MM-DD.dump` | toda coleta; a data é a de Brasília | 7 dias |
| `semanal/AAAA-MM-DD.dump` | coletas de domingo | 28 dias |

As regras ficam em `scripts/r2-ciclo-de-vida-backup.json` (e `-brutos.json`, 365 dias). Para conferir: `npx --prefix web wrangler r2 bucket lifecycle list fiscaldogov-backup`.

O dump **não leva os papéis** (`etl_escrita`, `site_leitura`): eles são do servidor, não do banco. Por isso os papéis são recriados antes do `pg_restore`. Os `GRANT` vêm no dump e voltam sozinhos.

## Pré-requisitos

- `pg_restore` e `psql` **da major 18**, a mesma do servidor: `postgresql-client-18`, ou os binários da imagem `postgres:18-trixie`.
- `wrangler` autenticado numa conta com acesso ao R2 (`npx --prefix web wrangler login`), ou o painel da Cloudflare.
- Cronômetro ligado no passo 1. O alvo é **≤ 30 min** (SC-006).

## 1. Baixar a cópia mais recente

Painel da Cloudflare → *R2* → `fiscaldogov-backup` → `diario/` → o objeto com a data mais recente → *Download*. Ou:

```bash
mkdir -p restauracao && cd restauracao
npx --prefix ../web wrangler r2 object get "fiscaldogov-backup/diario/AAAA-MM-DD.dump" --file banco.dump --remote
pg_restore --list banco.dump | head      # tem que listar TABLE DATA; erro aqui = cópia ruim, use a anterior
```

## 2. Criar um banco vazio na mesma major

Para ensaio (R8), use um Postgres local descartável:

```bash
docker run -d --name restauracao -e POSTGRES_PASSWORD=restauracao -p 5433:5432 postgres:18-trixie
export DESTINO=postgresql://postgres:restauracao@localhost:5433/postgres
```

Para produção, prefira **criar um serviço Postgres novo** no Railway (imagem `ghcr.io/railwayapp-templates/postgres-ssl:18`, como na T051) em vez de apagar o atual. O antigo continua lá até a troca ser conferida.

## 3. Recriar os papéis

```bash
psql "$DESTINO" -v ON_ERROR_STOP=1 -c "CREATE ROLE etl_escrita LOGIN" -c "CREATE ROLE site_leitura LOGIN"
```

No ensaio, os papéis ficam sem senha (ninguém vai conectar com eles). Em produção, defina as senhas com `\password` como em `docs/05-runbooks/banco-papeis.md` §1, e atualize as URLs nos cofres se elas mudarem.

## 4. Restaurar

```bash
pg_restore --dbname="$DESTINO" --exit-on-error banco.dump
```

`--exit-on-error` para no primeiro erro, em vez de deixar um banco pela metade com um aviso no meio da saída.

## 5. Comparar contagens por tabela

Rode **na origem** (como dono, com a URL pública do painel do Railway) e **no destino**, e compare as duas saídas:

```bash
contar() {
  psql "$1" -X -A -t -c "SELECT format('SELECT %L, count(*) FROM %I;', tablename, tablename)
                          FROM pg_tables WHERE schemaname = 'public' ORDER BY tablename" \
  | psql "$1" -X -A -t -F ' ' -f -
}
diff <(contar "$ORIGEM") <(contar "$DESTINO") && echo "contagens idênticas"
```

A origem pode ter uma coleta a mais que a cópia, se uma coleta terminou depois do backup. Nesse caso, a diferença aparece só em `execucao_etl` e `coleta_bruta`. Compare com o dump do mesmo dia e confira em `execucao_etl` o horário de cada um.

Confira também as permissões com a seção 2 de `docs/05-runbooks/banco-papeis.md`.

## 6. Parar o cronômetro e registrar

Anote em `specs/001-fundacao-tecnica/evidencias.md` (ou no incidente):
- objeto usado;
- horário de início e de fim;
- saída do `diff`;
- conferência das permissões.

## 7. (Produção) Trocar para o banco restaurado

1. Pause a coleta: painel do Railway → serviço `etl` → *Settings* → apague o *Cron Schedule* temporariamente.
2. Atualize `DATABASE_URL_DONO` (referência ao novo serviço), `DATABASE_URL_ESCRITA` (Railway) e `DATABASE_URL_LEITURA` (GitHub, ambiente `producao`).
3. Rode `python -m etl verificar-config` (ver `docs/05-runbooks/operacao-coleta.md` §3).
4. Volte o cron (`0 6,8 * * *`) e acione uma coleta (`railway cron run --service etl --yes`).
5. Com a primeira coleta e a publicação conferidas, apague o serviço Postgres antigo.

## Limpeza do ensaio

```bash
docker rm -f restauracao && rm -rf restauracao
```

O dump baixado tem os dados do banco: não deixe cópia fora do R2.
