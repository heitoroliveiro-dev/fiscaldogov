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
