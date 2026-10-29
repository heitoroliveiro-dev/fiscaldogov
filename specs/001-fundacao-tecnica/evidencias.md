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
