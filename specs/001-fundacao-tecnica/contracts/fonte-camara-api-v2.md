# Contrato — fonte: API de Dados Abertos da Câmara (v2)

Base: `https://dadosabertos.camara.leg.br/api/v2` (configurável por `CAMARA_API_URL`, para testes). Sem autenticação. Cabeçalhos enviados: `Accept: application/json` e `User-Agent: fiscaldogov-etl (+https://github.com/heitoroliveiro-dev/fiscaldogov)`.

## Endpoints consumidos na F2

| Endpoint | Para quê | Campos usados | Paginação |
|---|---|---|---|
| `GET /deputados?itens=100&pagina=N` | Deputados **em exercício no momento** (sem parâmetro de tempo) → seleção do FR-006 | `id`, `nome`, `siglaPartido`, `uriPartido`, `siglaUf`, `idLegislatura`, `urlFoto`, `uri` | Seguir `links[rel=next]` até não existir |
| `GET /deputados/{id}/historico` | Períodos de exercício, condição, filiações, UF | `dataHora`, `situacao`, `condicaoEleitoral`, `descricaoStatus`, `siglaPartido`, `uriPartido`, `siglaUf`, `idLegislatura`, `nomeEleitoral` | Sem paginação |

## Tradução para o domínio

Feita no adaptador; o domínio nunca vê o formato da API (DA02).

- `dataHora` vem sem fuso (ex.: `2023-02-01T12:05`) e é lido como horário de Brasília (`America/Sao_Paulo`). A documentação da API não informa o fuso. A leitura segue os limites de legislatura do próprio histórico (`2023-01-31T23:59` e `2023-02-01T00:00`), que só fazem sentido no calendário local. Suposição registrada em 2026-10-28.
- `situacao`: `"Exercício"` → em exercício; nula → evento só de nome ou partido (não abre nem fecha período); qualquer outra → fora de exercício.
- `condicaoEleitoral`: `Titular`/`Suplente`; nula só em evento sem situação; outro valor → `RespostaInvalida`.
- `siglaPartido = "S.PART."` → sem partido (a API a trata como partido, com URI própria; o domínio não — data-model.md).

## Endpoint proibido

- `GET /deputados/{id}` — devolve `cpf`. Não é chamado (RNF06, FR-009; research §4).

## Sanitização antes de guardar a resposta bruta

Remover recursivamente as chaves `cpf`, `dataNascimento`, `municipioNascimento`, `ufNascimento` e `escolaridade`. Isso é defesa em profundidade, caso algum endpoint passe a incluí-las. Teste de unidade com resposta contendo essas chaves.

## Registro original (RF07)

- Página humana do deputado: `https://www.camara.leg.br/deputados/{id}` — é o link exibido na página pública.
- `fonte_url` dos registros: a URL da API efetivamente consultada.

## Falhas

| Situação | Tratamento |
|---|---|
| Erro de rede, tempo esgotado (30 s), HTTP 5xx, HTTP 429 | Nova tentativa: até 3, com espera de 5 s, 20 s e 60 s |
| HTTP 4xx (exceto 429) | Falha imediata da execução |
| JSON inválido ou campo usado ausente / de tipo inesperado | Falha imediata da execução (falha fechada); a resposta bruta é guardada para diagnóstico |
| Mesmo deputado em duas páginas da lista | Falha imediata (`RespostaInvalida`): os links `next` alternam entre `ordem=ASC&ordenarPor=nome` e a ordem padrão (visto em 2026-10-28, sem repetição em 3 rodadas); repetição indicaria que outro deputado sumiu |
| Lista de deputados vazia | Falha da execução ("fonte devolveu lista vazia") |

## Fixtures de teste

Respostas reais gravadas em `etl/tests/fixtures/camara/` (com a data da coleta no nome): uma página de `/deputados` e o `/historico` do deputado 204496 (22 eventos, com licenças e reassunções).
