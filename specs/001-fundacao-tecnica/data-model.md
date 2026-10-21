# Data model — 001 Fundação técnica

Subconjunto de `docs/01-architecture/modelagem-dados.md` necessário a esta feature. Nomes no banco em `snake_case` (via `@@map` no Prisma); datas e horas em `timestamptz`.

## Entidades desta feature

| Tabela | Campos | Regras |
|---|---|---|
| `casa_legislativa` | `id` smallint PK · `sigla` text único · `nome` text | Carga fixa na migration: (`CD`, Câmara dos Deputados). |
| `legislatura` | `numero` smallint PK · `inicio` date · `fim` date | Carga fixa: 57 (2023-02-01 a 2027-01-31). |
| `partido` | `id` PK · `sigla` text · `nome` text nulo | Ligado à fonte por `identificador_externo` (`sistema = camara_v2_partido`). |
| `parlamentar` | `id` PK · `nome_parlamentar` text · `nome_ordenacao` text · `url_foto` text nulo · `fonte_url` text · `coletado_em` timestamptz | `nome_ordenacao` = nome parlamentar em minúsculas e sem acento, gravado pelo ETL (FR-006). **Sem CPF e sem nome civil** (FR-009). |
| `identificador_externo` | `id` PK · `parlamentar_id` FK nulo · `partido_id` FK nulo · `sistema` enum (`camara_v2`, `camara_v2_partido`) · `valor` text · `legislatura_numero` FK nulo | Único (`sistema`, `valor`, `legislatura_numero`) com `NULLS NOT DISTINCT`: sem legislatura, o mesmo identificador não se repete. Exatamente um entre `parlamentar_id` e `partido_id` preenchido (CHECK). Chaves estrangeiras com `ON DELETE RESTRICT`, como nas demais tabelas. |
| `mandato` | `id` PK · `parlamentar_id` FK · `casa_id` FK · `legislatura_numero` FK · `uf` char(2) | Único (parlamentar, casa, legislatura). |
| `periodo_exercicio` | `id` PK · `mandato_id` FK · `inicio` timestamptz · `fim` timestamptz nulo · `condicao` enum (`titular`, `suplente`) · `motivo_inicio` text · `motivo_fim` text nulo · `fonte_url` text · `coletado_em` timestamptz | `fim` nulo = em exercício. Invariantes 1 e 2 abaixo. |
| `filiacao` | `id` PK · `parlamentar_id` FK · `partido_id` FK · `inicio` timestamptz · `fim` timestamptz nulo · `fonte_url` text · `coletado_em` timestamptz | Invariante 3. |
| `execucao_etl` | `id` PK · `iniciada_em` · `terminada_em` nulo · `status` enum (`em_andamento`, `sucesso`, `com_pendencias`, `falha`, `dispensada`) · `gatilho` enum (`agendada`, `reserva`, `manual`) · `tentativas` jsonb · `contagens` jsonb · `erros` jsonb · `pendencias` jsonb · `versao_codigo` text | FR-010. Ver transições abaixo. |
| `coleta_bruta` | `id` PK · `execucao_id` FK · `fonte` text · `url` text · `chave_r2` text · `sha256` char(64) · `bytes` int · `coletada_em` | Só inserida quando o `sha256` difere da última da mesma `url` (FR-011). |

**Mudança na modelagem geral** (registrar em `docs/01-architecture/modelagem-dados.md`):
- `parlamentar.nome_civil` sai do M1, porque só vem do endpoint que traz CPF (research §4);
- entram `parlamentar.nome_ordenacao` e o enum `execucao_etl.gatilho`;
- o enum `execucao_etl.status` ganha os estados `em_andamento` e `dispensada`.

## Invariantes garantidas pelo banco

| # | Invariante | Mecanismo | Origem |
|---|---|---|---|
| 1 | `periodo_exercicio.fim > inicio` quando `fim` não é nulo | CHECK | DA03 |
| 2 | Períodos do mesmo mandato não se sobrepõem | `EXCLUDE USING gist (mandato_id WITH =, tstzrange(inicio, fim) WITH &&)` + extensão `btree_gist` | FR-018 |
| 3 | No máximo uma filiação aberta por parlamentar | índice único parcial `(parlamentar_id) WHERE fim IS NULL` | FR-018, RN01 |
| 4 | `identificador_externo` aponta para exatamente uma entidade | CHECK `num_nonnulls(parlamentar_id, partido_id) = 1` | ADR-0003 §2 |
| 5 | Papéis: `etl_escrita` só DML; `site_leitura` só `SELECT`; nenhum dos dois com DDL | `GRANT` + `ALTER DEFAULT PRIVILEGES` na migration; papéis criados pelo runbook | FR-019 |

O Prisma não expressa 1–5 no `schema.prisma`: entram como SQL na migration (`prisma migrate dev --create-only` e edição), cada uma com teste de integração.

## Derivação a partir do histórico da Câmara

`GET /deputados/{id}/historico` devolve eventos com `dataHora`, `situacao`, `condicaoEleitoral`, `siglaPartido`, `idLegislatura`, `descricaoStatus`.

- **Período de exercício:**
  - abre num evento com `situacao = "Exercício"`;
  - fecha no próximo evento com `situacao` diferente de "Exercício" (ex.: "Licença", "Afastado", "Fim de Mandato");
  - `condicao` vem de `condicaoEleitoral` (Titular → `titular`, Suplente → `suplente`);
  - os motivos vêm de `descricaoStatus`.
- **Filiação:** abre na primeira ocorrência de uma `siglaPartido` e fecha quando a sigla muda. O evento inicial "Partido no início da legislatura" (com `situacao` nula) define a primeira filiação.
- **UF do mandato:** `siglaUf` do primeiro evento da legislatura.
- A derivação é **função pura no domínio**, testada com o histórico real gravado: deputado 204496, 22 eventos com licenças e reassunções.

## Transições de `execucao_etl.status`

```
em_andamento ──► sucesso
             ├─► com_pendencias   (coleta gravada; backup ou envio de bruto falhou)
             ├─► falha            (erro, 3 tentativas esgotadas ou tempo de 60 min)
             └─► dispensada       (só gatilho reserva: já houve sucesso no dia)
```

Uma `em_andamento` iniciada há mais de 60 minutos é considerada `falha` pela execução seguinte, que a fecha com o motivo "interrompida".

## Migration

- **Subida:** uma migration inicial (`0001_fundacao`) com tabelas, enums, cargas fixas, extensão, invariantes e permissões.
- **Reversão:** o Prisma Migrate só aplica migrations para frente.
  - **Fora de produção:** `prisma migrate reset`.
  - **Em produção:** uma nova migration corretiva, ou restauração do backup (runbook).
  - Como esta é a primeira migration e o dado é recriável a partir da fonte, o risco é baixo.
- **Efeito sobre dados existentes:** nenhum; o banco está vazio.
