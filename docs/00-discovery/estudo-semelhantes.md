# Estudo de projetos semelhantes (R05)

- **Data:** 2026-10-20
- **Objetivo:** saber o que já existe, aprender com acertos e erros e definir o diferencial antes do lançamento (contexto §10, R05).
- **Método:** visita aos sites e repositórios, documentação pública e reportagens. Situações e datas são as observadas nesta data.

## Panorama

| Projeto | O que faz | Situação em 2026-10-20 | Relação com este projeto |
|---|---|---|---|
| **Radar do Congresso** (Congresso em Foco) | Assiduidade com faltas justificadas e não justificadas (dados da Secretaria-Geral da Mesa), índice de governismo, gastos da cota (CEAP), votações, bancadas, votos por município, discursos — Câmara e Senado | Ativo; lista de deputados indica base atualizada em 02/10/2026 | **Concorrente direto da HU01.** App renderizado no navegador (Angular); a configuração padrão do app lista assiduidade de 2023 a 2025 |
| **Ranking dos Políticos** | Nota por parlamentar, com pontos positivos e negativos definidos por um "Conselho de Leis" a partir de pilares (anticorrupção, antiprivilégios, antidesperdício); votações têm o maior peso | Ativo desde 2011; Câmara e Senado | Modelo oposto à DA04: juízo de valor sobre quais votos são bons |
| **Operação Serenata de Amor** (Rosie e Jarbas, Open Knowledge Brasil) | IA que aponta reembolsos suspeitos da cota parlamentar; Jarbas é o site de consulta | Repositório não arquivado, mas "não recebe atualizações frequentes"; esforço migrou para o Querido Diário | Outro tema (gastos). Lição de sustentabilidade de projeto cívico voluntário |
| **Basômetro** (Estadão Dados) | Taxa de governismo por parlamentar a partir das votações nominais; cada parlamentar é uma bolinha **na cor do partido** | Aparenta estar parado (dados e referências de 2011–2012) | Contraexemplo da regra de neutralidade visual |
| **Radar Parlamentar** | App de celular (iOS/Android): gastos, discursos, proposições, votações, emendas, alertas; dados coletados diariamente | Ativo (© 2026) | Cobre muitos temas; a página não explica como calcula a presença |
| **Monitora, Brasil!** | App premiado no hackathon da Câmara de 2013: assiduidade, projetos, rankings | Sem sinal de atividade nas fontes mais recentes (2022) | Mais um projeto cívico descontinuado |
| **GovTrack** (EUA) | Percentual de votações perdidas por parlamentar, com a mediana da casa como referência e quebra por trimestre | Ativo | Referência de metodologia |

## Lições

1. **Contexto evita leitura errada.** O GovTrack apresenta a taxa ao lado da mediana da casa; sem referência, o eleitor não sabe se 85% é muito ou pouco. → RN11.
2. **Período curto permite escolher a dedo.** Checagem da PolitiFact (2012) mostrou um trimestre ruim usado para pintar um parlamentar como faltoso, quando o período longo dava outra imagem. → RN12.
3. **Justificada × não justificada muda o retrato.** Análise da CalMatters (2024) mostrou ausências por luto e doença aparecendo iguais às demais num percentual bruto. → valida RN03 e RN04.
4. **Nota e cor de partido comprometem a neutralidade.** Ranking dos Políticos (nota com critérios de valor) e Basômetro (cor partidária) são exatamente o que DA04 e a regra de cores evitam.
5. **Projetos cívicos morrem por falta de manutenção.** Serenata (desacelerado), Basômetro e Monitora, Brasil! (parados). → valida ETL automático, custo baixo (RNF04) e alertas (RNF07); abrir o código (DA08) permite que outros continuem o trabalho.
6. **Explicar a regra é raro.** Dos projetos brasileiros vistos, nenhum mostra, para cada número, a conta ("X de Y sessões"), a regra e o link para o registro oficial.

## Diferencial (decidido em 2026-10-20)

> **Cada número é verificável e se explica sozinho, no celular e no computador: de onde veio, como foi calculado e como conferir na fonte oficial.**

Na prática:

- Toda taxa com "X de Y sessões", mediana da Câmara ao lado (RN11) e link para o registro oficial (RF07).
- Taxa oficial da Câmara ao lado da nossa (RN09).
- Metodologia pública com exemplos numéricos e casos de borda (RF06), e **código aberto** sob AGPL-3.0 (DA08).
- Sem nota, sem rótulo ideológico, sem cor de partido (DA04).
- Prévia de compartilhamento com fonte e data (RF10), para o número não circular sem contexto.

**Critério de priorização derivado:** feature que não reforça verificabilidade ou clareza perde prioridade.

## Fontes

- Radar do Congresso — <https://radar.congressoemfoco.com.br/parlamentares/camara>; reportagem sobre a ferramenta: <https://www.congressoemfoco.com.br/noticia/84730/quem-sao-os-parlamentares-mais-assiduos>
- Ranking dos Políticos — <https://ranking.org.br/>; InfoMoney: <https://www.infomoney.com.br/?p=237907>
- Operação Serenata de Amor — <https://github.com/okfn-brasil/serenata-de-amor>; <https://en.wikipedia.org/wiki/Operation_Serenata_de_Amor>
- Basômetro — <https://github.com/estadaoDados/basometro>
- Radar Parlamentar — <https://www.radarparlamentar.com/>
- Monitora, Brasil! — <https://olhardigital.com.br/noticia/em-quem-votar-confira-11-apps-e-sites-para-escolher-os-seus-candidatos/78749>
- GovTrack (via checagens) — <https://www.politifact.com/factchecks/2012/oct/08/dan-sebring/sebring-says-moore-most-absent-member-wisconsins-c/>
- CalMatters — <https://calmatters.org/politics/2024/10/california-legislature-absences-abstentions/>
