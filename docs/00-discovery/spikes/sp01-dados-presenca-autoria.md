# SP01 — Dados de presença e autoria na Câmara

- **Data:** 2026-10-20
- **Escopo:** Câmara dos Deputados. O Senado fica para o SP01-B, antes da sprint do Senado (DA05).
- **Perguntas (contexto §10):** (a) a ausência informa se foi justificada? (b) como foi registrada a presença nas sessões remotas e semipresenciais? (c) qual campo identifica o primeiro signatário?
- **Método:** consultas às fontes oficiais com amostras reais. Uma sessão deliberativa por mês de fev/2019 a dez/2022, mais dias inteiros comparados sessão a sessão.

## Respostas

| # | Pergunta | Resposta | Regra afetada |
|---|---|---|---|
| a | Justificativa de ausência | **Não existe na API v2.** Existe no **webservice legado** `ListarPresencasDia`, **por dia**, com o motivo. **Lacuna de abr/2020 a mar/2021**, coberta só pela página pública do deputado (HTML). | RN03, RN04 implementáveis, com a lacuna a decidir |
| b | Presença em sessão remota/semipresencial | **Registrada normalmente** na API v2 (~500 presentes por sessão virtual). O formato semipresencial **continuou até 2023**, não só em 2020–2021. | RN05 implementável; texto precisa de ajuste |
| c | Primeiro signatário | Campo **`ordemAssinatura = 1`** em `/proposicoes/{id}/autores`. Há também o campo **`proponente`** (1 = proponente, 0 = apoiador). | RN02 implementável; uma pergunta nova |

## Fontes avaliadas

| Fonte | O que traz | Limitações |
|---|---|---|
| API v2 — `/eventos?idOrgao=180&codTipoEvento=110` | Sessões do plenário (Plenário = órgão 180) | Lista também sessões **canceladas**; existem dois códigos de "Sessão Deliberativa" (110 e 204) — todas as amostras de 2019–2023 usam 110 |
| API v2 — `/eventos/{id}/deputados` | Quem registrou presença na sessão (id v2, partido, UF, legislatura) | Sem ausências e sem justificativa. Sessão cancelada também tem lista (59610: 290 nomes) |
| Legado — `SitCamaraWS/sessoesreunioes.asmx/ListarPresencasDia?data=DD/MM/AAAA` | Os 513 deputados do dia, com `descricaoFrequenciaDia` (Presença, Ausência, Ausência justificada), `justificativa` e frequência **por sessão** | Justificativa só por dia. Identifica o deputado pela carteira, não pelo id v2. Vazio de abr/2020 a mar/2021 |
| Legado — `Deputados.asmx/ObterDeputados` | Liga `matricula` (carteira) a `ideCadastro` (= id v2) | Só os deputados em exercício hoje |
| Página pública — `camara.leg.br/deputados/{id}/presenca-plenario/{ano}` | Presença por sessão, inclusive 2020, e totais oficiais pelo **Ato da Mesa nº 191/2017** | HTML: exige raspagem e quebra se o layout mudar |
| Lote — `arquivos/eventosPresencaDeputados/csv/eventosPresencaDeputados-AAAA.csv` | O mesmo que `/eventos/{id}/deputados`, por ano (~17 MB em 2023) | Sem justificativa. Útil para a carga inicial |

## Evidência

### Justificativa no legado (09/05/2023, uma sessão)

| Situação no dia | Deputados |
|---|---|
| Presença | 462 (= 462 na API v2, evento 67950) |
| Ausência justificada | 37 — Missão Autorizada 18, Licença para Tratamento de Saúde 15, Decisão da Mesa 4 |
| Ausência | 14 |

A justificativa vale para o dia inteiro: nas amostras com duas sessões no dia (17/06/2019 e 07/07/2022), **nenhum** deputado justificado no dia esteve presente em alguma sessão desse dia.

### Cobertura do legado (uma sessão por mês)

| Período | Legado com dados? |
|---|---|
| fev/2019 – mar/2020 | Sim |
| **abr/2020 – mar/2021** | **Não** — 131 sessões deliberativas encerradas na API v2, todas virtuais |
| abr/2021 – out/2026 | Sim |

### Presença por sessão: legado × API v2

| Dia | Sessão | API v2 | Legado |
|---|---|---|---|
| 07/07/2022 | 1ª | 70 | 70 |
| 07/07/2022 | 2ª | 427 | 427 |
| 09/05/2023 | única | 462 | 462 |
| 17/06/2019 | 1ª | 270 | **294** |
| 17/06/2019 | 2ª | 406 | **424** |

De 2021 a 2023, as duas fontes batem exatamente. **Em 2019, o legado registra 4% a 9% mais presenças que a API v2**, sem causa identificada neste spike. O horário de início difere entre as fontes (ex.: 06:30 × 06:00), então o cruzamento de sessões é feito pela **ordem da sessão no dia**.

### Ligação deputado legado → id v2

- 57ª legislatura: **513 de 513** casam por nome + UF (e `ObterDeputados` dá o mapeamento direto).
- 56ª legislatura: **512 de 513** casam por nome + UF. O restante ("José Airton Cirilo/CE") exige o histórico de nomes (`/deputados/{id}/historico`).
- `/deputados?idLegislatura=56` devolve **uma linha por período de exercício** (1.073 linhas, 613 deputados) e **precisa ser paginado** — `itens=1000` corta a lista sem aviso. Essa granularidade serve de base para o Mandato (DA03).

### Autoria (PEC 2/2023, id 2350490)

171 autores: `ordemAssinatura = 1` para exatamente um (Laura Carneiro); `proponente`: 4 proponentes e 167 apoiadores. O endpoint traz o deputado só na `uri` (`/deputados/{id}`), não num campo de id.

## Decisões que o spike levanta (do responsável)

| # | Decisão | Por quê |
|---|---|---|
| S1 | **Lacuna de abr/2020 a mar/2021:** raspar a página pública do deputado, mostrar a taxa sem distinguir justificativa nesse período (com aviso), ou excluir o período do ranking? | RN04 tira as justificadas do denominador; sem o dado, a taxa desse período usa outra regra |
| S2 | **Alinhar à regra oficial da Câmara (Ato da Mesa 191/2017)?** (Contagem rápida pela API v2 em 2020: 119 sessões deliberativas encerradas contra 133 na página oficial — **subcontagem conhecida**: a consulta omitiu os dias 31; a diferença real não foi medida.) A Câmara publica a própria taxa considerando só "sessões deliberativas com Ordem do Dia iniciada". Se nossa regra for diferente, o eleitor verá dois números diferentes para o mesmo deputado | R01 (verificabilidade). Exige confirmar se a API indica que a Ordem do Dia foi iniciada |
| S3 | **Coautoria (RN02):** todo signatário (PEC: 170 coautorias) ou só os coproponentes, com os apoiadores à parte (PEC: 3 coautorias + 167 apoios)? | O campo `proponente` permite separar quem propôs de quem só apoiou |
| S4 | **Fonte oficial de presença** quando legado e API v2 divergem (2019): qual prevalece? | Os números de 2019 dependem disso; a escolha precisa constar na metodologia |

## Decisões tomadas (2026-10-20)

| # | Decisão | Onde ficou |
|---|---|---|
| S1 | Ler a página pública de presença de cada deputado **uma única vez**, só para abr/2020–mar/2021, e gravar o resultado com a fonte. | DA07 |
| S2 | Manter a regra do site (RN04/RN05) e exibir **ao lado** a taxa oficial da Câmara, com link e explicação da diferença. Exige ler a página oficial do deputado diariamente; se falhar, mostra só o link. | RN09 |
| S3 | Coautoria = demais **proponentes**; apoiadores numa coluna de apoios, não somada. | RN02 |
| S4 | Presença vem do webservice legado; a API v2 é conferência, e divergência gera alerta. | DA07 |

## Consequências para o adaptador da Câmara (insumo do ADR de domínio)

- Sessões: `idOrgao=180`, tipo "Sessão Deliberativa", **somente situação "Encerrada…"**.
- Presença e justificativa vêm de duas fontes, cruzadas por deputado (nome + UF ou carteira) e por ordem da sessão no dia.
- O webservice legado é uma dependência frágil (tecnologia antiga, sem garantia de continuidade): o ETL precisa alertar se ele parar de responder (RNF07), e o site deve indicar quando a justificativa estiver indisponível.
- Paginação obrigatória em toda listagem da API v2.
- Ajuste de texto na RN05: "sessões remotas e semipresenciais" sem restringir a 2020–2021 (feito).
- Duas leituras de HTML oficial: a carga única do período sem justificativa (S1) e a taxa oficial diária (S2). Ambas precisam de teste contra páginas gravadas e de alerta quando o layout mudar.
