# Contexto do Projeto — Transparência do Congresso

> **Nome provisório.** O nome definitivo ainda não foi escolhido.
> **Status:** especificação em andamento (fase de entrevista)
> **Última atualização:** 2026-10-20
> **Responsável:** Heitor Oliveiro

Este documento é a fonte de verdade sobre **o que** o projeto é e **por que** ele existe. Nenhuma decisão de código deve contrariar o que está aqui sem antes atualizar este arquivo e registrar a mudança no changelog ao final.

---

## 1. Problema

Os dados sobre a atuação de deputados federais e senadores são públicos, mas estão espalhados em portais técnicos, em formatos pensados para quem sabe programar ou ler documentos legislativos. O eleitor comum não consegue responder perguntas simples, como "meu deputado comparece às sessões?" ou "o que está sendo votado agora?".

## 2. Objetivos

### 2.1 Objetivo geral

Oferecer ao eleitor comum uma forma simples, neutra e verificável de acompanhar a atuação de deputados federais e senadores a partir dos dados oficiais das duas casas.

### 2.2 Objetivos específicos

| ID | Objetivo |
|----|----------|
| OE01 | Exibir a taxa de presença de cada parlamentar em sessões deliberativas do plenário, com filtro por partido. |
| OE02 | Exibir a produção legislativa de cada parlamentar por tipo de proposição, separando autoria principal e coautoria. |
| OE03 | Permitir buscar projetos em tramitação e ver o autor e os votos nominais de cada parlamentar. |
| OE04 | Publicar a metodologia de cada estatística e a fonte de cada dado, com link para o registro oficial. |

## 3. Público-alvo

**Perfil principal: eleitor comum.** Não tem conhecimento técnico nem de processo legislativo. Acessa majoritariamente pelo celular. Quer respostas rápidas sobre quem o representa.

Consequências para o produto:

- Linguagem simples, sem jargão legislativo sem explicação.
- Interface mobile-first.
- Termos técnicos (votação nominal, tramitação, suplente) acompanhados de explicação curta na própria tela.

## 4. Escopo

### 4.1 Dentro do escopo do MVP

- **Câmara dos Deputados** (primeira entrega).
- **Senado Federal** (sprint seguinte, reutilizando o mesmo modelo de domínio).

### 4.2 Fora do escopo do MVP

| Item | Motivo | Quando reavaliar |
|------|--------|------------------|
| Assembleias legislativas estaduais | Até 27 fontes de dados heterogêneas, algumas sem votos nominais estruturados. | Após MVP estável. Candidata inicial: ALMG. |
| Ligação de um mesmo projeto entre Câmara e Senado | Identificadores e fluxos diferentes entre as casas; alta complexidade. | Versão pós-MVP. |
| Rótulo de "viés político" (esquerda/centro/direita) | Classificação contestada que compromete a credibilidade do site. | Substituído por métricas de alinhamento derivadas de votos (ver seção 9). |
| Votações em comissões | Comissões só fazem sentido para os membros delas; distorce comparações. | Versão pós-MVP. |

## 5. Fontes de dados

| Casa | API | Autenticação | Observações |
|------|-----|--------------|-------------|
| Câmara dos Deputados | `https://dadosabertos.camara.leg.br/api/v2` | Nenhuma | REST, JSON ou XML, especificação OpenAPI. Também publica arquivos em lote (CSV/JSON por ano). |
| Senado Federal | `https://legis.senado.leg.br/dadosabertos` | Nenhuma | Documentação em `/dadosabertos/docs/`. Estrutura e identificadores diferentes da API da Câmara. |

Endpoints relevantes identificados na Câmara:

- `/deputados` e `/deputados/{id}`: perfil, redes sociais, despesas, órgãos, ocupações.
- `/votacoes`, `/votacoes/{id}/votos`, `/votacoes/{id}/orientacoes`: votações, voto individual e orientação de partidos e do governo.
- `/proposicoes`: autores, tramitação e votações de cada proposição.
- `/partidos` e `/partidos/{id}/membros`: composição das bancadas.
- Eventos e deputados presentes em cada evento: base para o cálculo de presença.

Endpoints relevantes identificados no Senado:

- `/senador`: dados biográficos, mandatos e cargos.
- `/plenario/votacao`: votações nominais e resultados.

> Antes de implementar qualquer integração, validar os endpoints, limites e formatos na documentação oficial vigente.

## 6. Histórias de usuário

### HU01 — Ranking de faltas

**Como** eleitor, **quero** ver quais parlamentares mais faltaram, com filtro por partido, **para** avaliar o compromisso de quem me representa.

Regras aplicáveis: RN01, RN03, RN04, RN05.

Critérios de aceite (rascunho, a validar):

- [ ] O ranking exibe a taxa de presença em percentual, não o número absoluto de faltas.
- [ ] Apenas sessões deliberativas do plenário entram no cálculo.
- [ ] Apenas sessões em que o parlamentar estava em exercício entram no denominador.
- [ ] É possível filtrar por partido (partido atual).
- [ ] Cada parlamentar tem link para a metodologia do cálculo.

### HU02 — Ranking de propostas

**Como** eleitor, **quero** ver quais parlamentares mais apresentaram propostas, **para** saber quem tem atuação legislativa.

Regras aplicáveis: RN01, RN02, RN06.

Critérios de aceite (rascunho, a validar):

- [ ] A contagem é separada por tipo de proposição (PL, PEC, PLP e outros).
- [ ] Autoria principal e coautoria aparecem em colunas separadas.
- [ ] É possível filtrar por partido e por tipo de proposição.

### HU03 — Projetos em tramitação

**Como** eleitor, **quero** acompanhar os projetos em tramitação, saber quem os apresentou e como cada parlamentar votou, **para** entender o que está sendo decidido.

Regras aplicáveis: RN02, RN07.

Critérios de aceite (rascunho, a validar):

- [ ] É possível buscar projetos por tema, autor, situação e casa legislativa.
- [ ] O detalhe do projeto mostra autor principal e coautores.
- [ ] O detalhe mostra o voto de cada parlamentar nas votações nominais.
- [ ] Votações simbólicas são exibidas com a explicação de que não há registro individual de voto.
- [ ] Cada casa é tratada separadamente no MVP.

## 7. Regras de negócio

| ID | Regra | Status |
|----|-------|--------|
| RN01 | As estatísticas usam o **partido atual** do parlamentar. O perfil deve indicar se houve troca de partido no período, pois dados de quando ele estava em outra legenda aparecem sob a sigla atual. | Decidida |
| RN02 | Propostas são contadas em duas colunas, **autor principal** e **coautoria**, sempre separadas por tipo de proposição. | Decidida |
| RN03 | Apenas **ausências sem justificativa** contam como falta. Licença e missão oficial não contam. | Decidida, depende do spike SP01 |
| RN04 | A presença é expressa como **taxa percentual**, calculada sobre as sessões em que o parlamentar estava em exercício. | Proposta |
| RN05 | Apenas **sessões deliberativas do plenário** entram no cálculo de presença. | Proposta |
| RN06 | O ranking de propostas não exibe um número único consolidado; a quebra por tipo é obrigatória. | Proposta |
| RN07 | Estatísticas de voto por parlamentar consideram apenas **votações nominais**. | Proposta |

> **Decidida:** confirmada pelo responsável. **Proposta:** sugerida durante a entrevista, aguardando confirmação explícita.

## 8. Requisitos

### 8.1 Requisitos funcionais (preliminares)

| ID | Requisito | Origem |
|----|-----------|--------|
| RF01 | Listar parlamentares com taxa de presença, ordenável e filtrável por partido. | HU01 |
| RF02 | Listar parlamentares com contagem de propostas por tipo e por forma de autoria. | HU02 |
| RF03 | Buscar proposições em tramitação com filtros por tema, autor, situação e casa. | HU03 |
| RF04 | Exibir o detalhe de uma proposição com autores e votos nominais. | HU03 |
| RF05 | Exibir o perfil do parlamentar com partido atual e histórico de troca de partido. | RN01 |
| RF06 | Exibir página de metodologia com a regra de cálculo de cada estatística. | OE04 |
| RF07 | Exibir, em cada dado, a fonte oficial e link para o registro original. | OE04 |
| RF08 | Exibir a data da última atualização dos dados. | OE04 |

### 8.2 Requisitos não funcionais

**Pendente.** Próxima etapa da entrevista. Tópicos a cobrir: desempenho, disponibilidade, frequência de atualização dos dados, acessibilidade, segurança, observabilidade, custo de infraestrutura e LGPD.

## 9. Decisões de produto e arquitetura (preliminares)

| ID | Decisão | Motivo |
|----|---------|--------|
| DA01 | O site lê de um **banco próprio**, alimentado por um **processo ETL em Python** executado periodicamente. Não consulta as APIs oficiais em tempo real. | Volume de dados (513 deputados, 81 senadores, milhares de votações) inviabiliza consulta ao vivo; evita depender da disponibilidade das APIs. |
| DA02 | Modelo de domínio próprio com **um adaptador por fonte de dados** (Câmara, Senado). | As APIs têm estruturas e identificadores diferentes. Permite adicionar novas casas sem alterar o restante do sistema (princípio Aberto/Fechado, DDD). |
| DA03 | **Mandato** é entidade de primeira classe no modelo. | Suplentes, afastamentos e mandatos de 8 anos no Senado exigem ligar cada estatística ao período em exercício. |
| DA04 | Posicionamento político é exibido por **métricas derivadas de votos** (fidelidade partidária, alinhamento com a orientação do governo, similaridade de votos), nunca por rótulos ideológicos. | Neutralidade e credibilidade; o eleitor vê o dado e tira a própria conclusão. |
| DA05 | Entrega incremental: **Câmara primeiro**, Senado na sprint seguinte. | Validar o desenho dos adaptadores com uma fonte antes de duplicar o esforço. |

Entidades de domínio identificadas: Parlamentar, Casa Legislativa, Mandato, Partido, Sessão, Presença, Votação, Voto, Proposição, Autoria.

## 10. Riscos e investigações

| ID | Item | Impacto | Ação |
|----|------|---------|------|
| SP01 | **Spike:** confirmar se as APIs da Câmara e do Senado informam se cada ausência foi justificada. | Se o dado não existir, a RN03 não pode ser implementada. | Investigação com prazo fechado antes da sprint de desenvolvimento. |
| R01 | Erro de dado vira acusação injusta contra uma pessoa real. | Alto (reputacional e jurídico). | Metodologia pública, link para a fonte oficial em cada dado, testes automatizados nos cálculos. |
| R02 | Mudança de formato ou indisponibilidade das APIs oficiais. | Médio. | ETL com tratamento de erro, retry e alerta; banco próprio mantém o site no ar. |
| R03 | Nova legislatura a partir de fevereiro de 2027. | Médio. | Modelo de dados preparado para múltiplas legislaturas desde o início. |
| R04 | Percepção de parcialidade política. | Alto. | DA04, linguagem neutra, metodologia pública. |
| R05 | Projetos semelhantes já existem (ex.: Ranking dos Políticos, Operação Serenata de Amor). | Baixo para aprendizado, médio para adoção. | Estudar o que fazem e definir diferencial antes do lançamento. |

## 11. Glossário

- **Votação nominal:** votação em que o voto de cada parlamentar é registrado individualmente.
- **Votação simbólica:** votação em que o resultado é declarado sem registro individual de voto.
- **Tramitação:** caminho que uma proposição percorre (comissões, plenário, outra casa) até ser aprovada, rejeitada ou arquivada.
- **Sessão deliberativa:** sessão do plenário em que há votação de matérias.
- **Suplente:** quem assume o mandato quando o titular se afasta.
- **Legislatura:** período de quatro anos de trabalho do Congresso.
- **Orientação de bancada:** indicação de voto que o líder do partido (ou do governo) dá aos membros.

## 12. Pendências da especificação

- [ ] Nome definitivo do projeto
- [ ] Confirmar as regras com status "Proposta" (RN04 a RN07)
- [ ] Validar critérios de aceite das HU01 a HU03
- [ ] Requisitos não funcionais
- [ ] Restrições (prazo, orçamento, tempo disponível por semana)
- [ ] Diagrama de fluxo do usuário
- [ ] Modelagem de dados
- [ ] Plano de arquitetura e descritivo das decisões
- [ ] Definição da stack
- [ ] Executar o spike SP01

---

## Changelog

| Data | Alteração |
|------|-----------|
| 2026-10-20 | Criação do documento: problema, objetivos, público, escopo, fontes de dados, HU01 a HU03, regras de negócio RN01 a RN07, requisitos funcionais preliminares, decisões DA01 a DA05, riscos e pendências. |
