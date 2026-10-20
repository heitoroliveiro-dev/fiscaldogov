# Contexto do Projeto — Transparência do Congresso

> **Nome provisório.** O nome definitivo ainda não foi escolhido.
> **Status:** especificação em andamento (fase de entrevista — requisitos não funcionais concluídos)
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

### 2.3 Diferencial

**Cada número é verificável e se explica sozinho, no celular e no computador: de onde veio, como foi calculado e como conferir na fonte oficial.** Feature que não reforça verificabilidade ou clareza perde prioridade. Base: `docs/00-discovery/estudo-semelhantes.md`.

## 3. Público-alvo

**Perfil principal: eleitor comum.** Não tem conhecimento técnico nem de processo legislativo. Acessa majoritariamente pelo celular. Quer respostas rápidas sobre quem o representa.

Consequências para o produto:

- Linguagem simples, sem jargão legislativo sem explicação.
- Interface mobile-first.
- Termos técnicos (votação nominal, tramitação, suplente) acompanhados de explicação curta na própria tela.

## 4. Escopo

### 4.1 Dentro do escopo do MVP

- **Câmara dos Deputados** (primeira entrega).
- Dados das legislaturas 56ª e 57ª, mais a 58ª a partir de fevereiro de 2027 (RNF10).

**Marco 1 — Câmara no ar (até 31/01/2027):** HU01 (presença), RF05 (perfil), RF06–RF08 (metodologia, fonte e data de atualização), RF09 (home com gráficos), RF10 (compartilhamento), apenas a **57ª legislatura** (a 58ª entra a partir de fev/2027). A RN09 entra no M1 só com o link para a página oficial. Ficam para logo depois do M1, nesta ordem proposta: HU02, 56ª legislatura, HU03, número oficial da RN09.
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

Regras aplicáveis: RN01, RN03, RN04, RN05, RN08, RN09, RN11, RN12.

Critérios de aceite (rascunho, a validar):

- [ ] O ranking exibe a taxa de presença em percentual, não o número absoluto de faltas.
- [ ] Apenas sessões deliberativas do plenário entram no cálculo.
- [ ] Apenas sessões em que o parlamentar estava em exercício entram no denominador; ausências justificadas saem do denominador.
- [ ] A taxa aparece com "X de Y sessões".
- [ ] Só entra no ranking quem esteve em exercício em ≥ 25% das sessões do período.
- [ ] É possível filtrar por partido (partido atual).
- [ ] Cada parlamentar tem link para a metodologia do cálculo.
- [ ] O perfil mostra a taxa oficial da Câmara ao lado, com link.

### HU02 — Ranking de propostas

**Como** eleitor, **quero** ver quais parlamentares mais apresentaram propostas, **para** saber quem tem atuação legislativa.

Regras aplicáveis: RN01, RN02, RN06.

Critérios de aceite (rascunho, a validar):

- [ ] A contagem é separada por tipo de proposição (PL, PLP, PEC e PDL), pela data de apresentação.
- [ ] Autoria principal, coautoria e apoios aparecem em colunas separadas; apoios não se somam à coautoria.
- [ ] É possível filtrar por partido e por tipo de proposição.
- [ ] O ranking abre ordenado por PL (autor principal) e permite trocar o tipo e a forma de autoria.

### HU03 — Projetos em tramitação

**Como** eleitor, **quero** acompanhar os projetos em tramitação, saber quem os apresentou e como cada parlamentar votou, **para** entender o que está sendo decidido.

Regras aplicáveis: RN02, RN07.

Critérios de aceite (rascunho, a validar):

- [ ] É possível buscar projetos por tema, autor, situação e casa legislativa.
- [ ] O detalhe do projeto mostra autor principal e coautores.
- [ ] O detalhe mostra o voto de cada parlamentar nas votações nominais, na categoria oficial e com explicação de cada categoria.
- [ ] Votações simbólicas são exibidas com a explicação de que não há registro individual de voto.
- [ ] Cada casa é tratada separadamente no MVP.

## 7. Regras de negócio

| ID | Regra | Status |
|----|-------|--------|
| RN01 | As estatísticas usam o **partido atual** do parlamentar. O perfil deve indicar se houve troca de partido no período, pois dados de quando ele estava em outra legenda aparecem sob a sigla atual. | Decidida |
| RN02 | Propostas são contadas em colunas separadas — **autor principal**, **coautoria** e **apoios** —, sempre por tipo de proposição. **Autor principal é o primeiro signatário** (`ordemAssinatura = 1`); **coautores são os demais proponentes**; quem só apoiou (não proponente) aparece numa coluna de **apoios**, nunca somada à coautoria. Exemplo: PEC 2/2023 → 1 autoria principal, 3 coautorias e 167 apoios. | Decidida (SP01, S3) |
| RN03 | Apenas **ausências sem justificativa** contam como falta. Licença e missão oficial não contam. A justificativa registrada para o dia vale para todas as sessões desse dia. | Decidida (SP01) |
| RN04 | A presença é expressa como **taxa percentual**: presenças ÷ (sessões deliberativas em exercício − ausências justificadas). A ausência justificada não ajuda nem prejudica. A taxa sempre aparece com "X de Y sessões", e o perfil mostra separadamente presenças, ausências justificadas e faltas. Exemplo: 40 sessões em exercício, 30 presenças, 4 justificadas e 6 faltas → 30 ÷ 36 = 83,3%. | Decidida (SP01) |
| RN05 | Apenas **sessões deliberativas do plenário** entram no cálculo de presença, **incluindo as sessões deliberativas remotas e semipresenciais** (usadas de 2020 até pelo menos 2023), com nota na página de metodologia. Sessões canceladas não entram. | Decidida (SP01) |
| RN06 | O ranking de propostas considera **PL, PLP, PEC e PDL**, contados pela **data de apresentação** dentro do período filtrado. Requerimentos, indicações e demais tipos ficam de fora. Não há número único consolidado: o ranking é ordenado pelo tipo e pela forma de autoria que o eleitor escolher, com padrão **PL, autor principal**. | Decidida |
| RN07 | Estatísticas de voto por parlamentar consideram apenas **votações nominais**. O voto é exibido na **categoria oficial publicada pela casa** (Sim, Não, Abstenção, Obstrução, Art. 17, sem registro), cada uma com explicação curta. | Decidida |
| RN08 | O ranking de presença inclui apenas quem esteve em exercício em **pelo menos 25% das sessões deliberativas do período filtrado**. Abaixo disso, a taxa aparece só no perfil, com aviso de amostra pequena. | Decidida |
| RN09 | O perfil exibe, ao lado da taxa do site, a **taxa oficial publicada pela Câmara** (Ato da Mesa nº 191/2017) com link para a página oficial; a metodologia explica por que os números podem diferir. Se a taxa oficial não puder ser lida, aparece só o link. | Decidida (S2) |
| RN10 | A **taxa de presença de um partido** é a taxa agregada da bancada atual: soma das presenças ÷ soma das sessões consideradas (mesma regra da RN04) de todos os membros atuais (RN01). Partidos com menos de 5 deputados em exercício não entram em comparações entre partidos, com nota explicando o motivo. | Decidida |
| RN11 | Ao lado da taxa de cada deputado aparece a **mediana da Câmara** no mesmo período, calculada sobre os deputados que entram no ranking (RN08). | Decidida |
| RN12 | O **período padrão** do ranking, do perfil e da home é a **legislatura inteira**. O eleitor pode filtrar por ano; períodos menores que um ano exibem aviso de que poucas sessões distorcem a taxa. | Decidida |

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
| RF09 | Exibir na página inicial a busca por estado, nome e casa, a composição da Câmara por partido, a taxa de presença por partido (RN10) e os 5 deputados com menor presença. | Fluxo do usuário |
| RF10 | Permitir compartilhar o perfil do deputado com prévia que mostra nome, taxa, "X de Y sessões", data e fonte. | Fluxo do usuário |

### 8.2 Requisitos não funcionais

| ID | Requisito | Como verificar |
|----|-----------|----------------|
| RNF01 | **Atualização diária.** O ETL roda uma vez por dia, de madrugada (horário de Brasília); dados de um dia aparecem no site até as 08:00 do dia seguinte. | Data da última atualização exibida (RF08) ≤ 08:00 do dia corrente. |
| RNF02 | **Disponibilidade de 99% ao mês** (até ~7h fora do ar). Falha do ETL não derruba o site: ele continua servindo o último dado, com a data visível. | Monitor externo a cada 5 min; relatório mensal. |
| RNF03 | **Desempenho:** conteúdo principal carrega em ≤ 2,5 s (LCP, percentil 75) em celular com 4G. | Lighthouse em perfil mobile no CI; dados de campo após o lançamento. |
| RNF04 | **Custo ≤ US$ 10/mês em uso normal, sem escalar com o acesso.** Um pico de 100× no tráfego não multiplica o custo: ≥ 95% das requisições a páginas públicas são servidas por cache/CDN. Alerta de gasto em US$ 10 e limite rígido em US$ 20 no provedor. | Painel de custo do provedor; taxa de acerto do cache. |
| RNF05 | **Acessibilidade WCAG 2.2 AA.** | Verificação automatizada (axe) no CI sem violações; contraste já verificado no build do design system. |
| RNF06 | **Privacidade (LGPD):** apenas métricas de uso agregadas, sem cookie, sem IP armazenado e sem identificar o visitante — dispensa banner de consentimento. Sobre parlamentares, só se exibe e armazena o que as casas publicam e se relaciona ao exercício do mandato (ex.: CPF não é armazenado nem exibido). | Revisão da ferramenta de métricas; teste que garante a ausência de CPF no banco e nas páginas. |
| RNF07 | **Observabilidade e alertas via Telegram.** Falha do ETL (erro ou execução que não terminou) gera alerta em até 1 h; queda do site detectada pelo monitor externo gera alerta. Cada execução do ETL registra início, fim, registros lidos e gravados por entidade e erros. | Falha simulada gera mensagem no Telegram; log de execução consultável. |
| RNF08 | **Segurança:** site público somente leitura, sem login, apenas HTTPS. Busca e filtros aceitam só parâmetros de uma allowlist e têm limite de requisições por IP (valor definido no ADR de hospedagem). | Teste de parâmetro fora da allowlist → recusado; teste de limite → resposta 429. |
| RNF09 | **Web responsivo (DA06):** toda tela funciona de 360 px a 1440 px de largura sem rolagem horizontal, com layout próprio para computador (sem ser só a versão de celular esticada). | Teste E2E nos dois extremos. |
| RNF10 | **Alcance dos dados:** legislaturas 56ª (2019–2023) e 57ª (2023–2027), e a 58ª a partir de 01/02/2027. Em duas etapas: o Marco 1 carrega a 57ª; a 56ª entra logo após. | Contagem de legislaturas carregadas no banco. |

### 8.3 Restrições

| Restrição | Valor |
|-----------|-------|
| Dedicação | 5 a 10 horas por semana; o planejamento usa **8 h/semana** (~115 h até o Marco 1). |
| Prazo | Marco 1 (Câmara no ar) antes de 01/02/2027, início da 58ª legislatura. |
| Orçamento | RNF04. Infraestrutura atual do responsável: plano Hobby do Railway (US$ 5/mês), com preferência por reutilizá-lo. A escolha final de hospedagem é um ADR. |

## 9. Decisões de produto e arquitetura (preliminares)

| ID | Decisão | Motivo |
|----|---------|--------|
| DA01 | O site lê de um **banco próprio**, alimentado por um **processo ETL em Python** executado periodicamente. Não consulta as APIs oficiais em tempo real. | Volume de dados (513 deputados, 81 senadores, milhares de votações) inviabiliza consulta ao vivo; evita depender da disponibilidade das APIs. |
| DA02 | Modelo de domínio próprio com **um adaptador por fonte de dados** (Câmara, Senado). | As APIs têm estruturas e identificadores diferentes. Permite adicionar novas casas sem alterar o restante do sistema (princípio Aberto/Fechado, DDD). |
| DA03 | **Mandato** é entidade de primeira classe no modelo. | Suplentes, afastamentos e mandatos de 8 anos no Senado exigem ligar cada estatística ao período em exercício. |
| DA04 | Posicionamento político é exibido por **métricas derivadas de votos** (fidelidade partidária, alinhamento com a orientação do governo, similaridade de votos), nunca por rótulos ideológicos. | Neutralidade e credibilidade; o eleitor vê o dado e tira a própria conclusão. |
| DA05 | Entrega incremental: **Câmara primeiro**, Senado na sprint seguinte. | Validar o desenho dos adaptadores com uma fonte antes de duplicar o esforço. |
| DA06 | O produto é um **site web com domínio próprio, responsivo, para computador e celular**. O desenho começa pelo celular (mobile-first), mas a experiência no computador é igualmente completa. Sem app nativo no MVP. | O público consulta majoritariamente pelo celular, e também pelo computador; web responsivo atende os dois sem custo de publicação em lojas. |
| DA07 | **Fonte da presença na Câmara:** o registro de frequência da Câmara (webservice `SitCamaraWS`, com presença, ausência e justificativa); de abr/2020 a mar/2021, onde ele não tem dados, a página pública de presença de cada deputado, lida uma única vez. A API v2 (`/eventos/{id}/deputados`) serve de conferência: divergência entre as fontes gera alerta no ETL e consta na metodologia. | Só o webservice traz justificativa (RN03); usar uma única base para presença e justificativa mantém os números coerentes (SP01, S1, S4). |
| DA08 | **Código e metodologia abertos** sob a licença **AGPL-3.0**, em repositório público. Componentes copiados do design system mantêm a licença MIT de origem. | Qualquer pessoa pode auditar como cada número é calculado (R04); a AGPL impede um fork fechado do site com regras alteradas sem aviso; o código aberto permite que outros continuem o projeto (estudo de semelhantes, lição 5). |

Entidades de domínio identificadas: Parlamentar, Casa Legislativa, Mandato, Partido, Sessão, Presença, Votação, Voto, Proposição, Autoria.

## 10. Riscos e investigações

| ID | Item | Impacto | Ação |
|----|------|---------|------|
| SP01 | **Spike:** confirmar nas APIs da Câmara e do Senado (a) se cada ausência informa se foi justificada; (b) como foi registrada a presença nas sessões deliberativas remotas e semipresenciais de 2020–2021; (c) qual campo identifica o primeiro signatário de uma proposição. | Sem (a), a RN03 e a RN04 não podem ser implementadas como decididas; (b) afeta a RN05; (c) afeta a RN02. | **Executado para a Câmara em 2026-10-20** — `docs/00-discovery/spikes/sp01-dados-presenca-autoria.md`. (a) justificativa só no webservice legado, por dia, com lacuna de abr/2020 a mar/2021; (b) presença remota registrada; (c) `ordemAssinatura`. Decisões S1–S4 tomadas (DA07, RN02, RN09). Senado: SP01-B antes da sprint do Senado. |
| R01 | Erro de dado vira acusação injusta contra uma pessoa real. | Alto (reputacional e jurídico). | Metodologia pública, link para a fonte oficial em cada dado, testes automatizados nos cálculos. |
| R02 | Mudança de formato ou indisponibilidade das APIs oficiais. | Médio. | ETL com tratamento de erro, retry e alerta; banco próprio mantém o site no ar. |
| R03 | Nova legislatura a partir de fevereiro de 2027. | Médio. | Modelo de dados preparado para múltiplas legislaturas desde o início. |
| R04 | Percepção de parcialidade política. | Alto. | DA04, linguagem neutra, metodologia pública. |
| R05 | Projetos semelhantes já existem (ex.: Ranking dos Políticos, Operação Serenata de Amor). | Baixo para aprendizado, médio para adoção. | Estudo feito em 2026-10-20 (`docs/00-discovery/estudo-semelhantes.md`); diferencial definido (§2.3). O Radar do Congresso é concorrente direto da HU01. |
| R06 | Prazo do Marco 1 apertado: ~15 semanas × 5–10 h = 75–150 h para fechar a especificação, arquitetura, fundação técnica e as features da Câmara, com duas legislaturas de dados. | Alto para o prazo. | Marco 1 mínimo definido (§4.1): estimativa de 89–140 h contra ~115 h (inclui RF09 e RF10). Checkpoints com data no ROADMAP; atraso de mais de 1 semana em um checkpoint obriga a reavaliar o escopo. |
| R07 | Tráfego viral concentrado (o site se espalha). | Alto para custo e disponibilidade se cada acesso chegar ao servidor. | RNF04: páginas públicas servidas por cache/CDN; a busca é o ponto dinâmico a proteger com cache e limite de requisições. |

## 11. Glossário

- **Votação nominal:** votação em que o voto de cada parlamentar é registrado individualmente.
- **Votação simbólica:** votação em que o resultado é declarado sem registro individual de voto.
- **Tramitação:** caminho que uma proposição percorre (comissões, plenário, outra casa) até ser aprovada, rejeitada ou arquivada.
- **Sessão deliberativa:** sessão do plenário em que há votação de matérias.
- **Suplente:** quem assume o mandato quando o titular se afasta.
- **Legislatura:** período de quatro anos de trabalho do Congresso.
- **Orientação de bancada:** indicação de voto que o líder do partido (ou do governo) dá aos membros.
- **Primeiro signatário:** quem assina primeiro uma proposição; neste projeto, o autor principal (RN02).
- **Proponente e apoiador:** pelo regimento, todos que assinam são autores; a Câmara distingue quem propôs (proponente) de quem assinou em apoio (apoiador), por exemplo para alcançar as 171 assinaturas de uma PEC.
- **Obstrução:** recurso regimental em que o parlamentar, presente, deixa de votar para tentar impedir que a votação atinja o quórum. É um ato político, não uma ausência.
- **Art. 17:** registro do presidente da Câmara, que pelo regimento não vota em votações comuns.
- **PL, PLP, PEC, PDL:** projeto de lei, projeto de lei complementar, proposta de emenda à Constituição e projeto de decreto legislativo.

## 12. Pendências da especificação

- [ ] Nome definitivo do projeto
- [x] Confirmar as regras com status "Proposta" (RN04 a RN07)
- [ ] Validar critérios de aceite das HU01 a HU03
- [x] Requisitos não funcionais
- [x] Restrições (prazo, orçamento, tempo disponível por semana)
- [x] Definir o escopo mínimo do Marco 1 (R06)
- [x] Diagrama de fluxo do usuário (`docs/00-discovery/fluxo-usuario.md`)
- [ ] Modelagem de dados
- [ ] Plano de arquitetura e descritivo das decisões
- [x] Definição da stack (ADR-0001)
- [x] Executar o spike SP01 (Câmara)
- [x] Decidir S1–S4 do SP01
- [ ] SP01-B: mesmo spike para o Senado, antes da sprint do Senado

---

## Changelog

| Data | Alteração |
|------|-----------|
| 2026-10-20 | Hospedagem, publicação diária, agendamento e backup definidos no ADR-0002. |
| 2026-10-20 | Stack definida no ADR-0001. |
| 2026-10-20 | Estudo de projetos semelhantes; diferencial (§2.3); DA06 explicita computador e celular; DA08 (código aberto, AGPL-3.0); RN11 (mediana) e RN12 (período padrão). |
| 2026-10-20 | Fluxo do usuário do Marco 1; RF09 (home com gráficos), RF10 (compartilhamento) e RN10 (taxa do partido) entram no M1. |
| 2026-10-20 | Escopo do Marco 1 (§4.1): presença, perfil e metodologia, só 57ª legislatura; RN09 só com link; planejamento a 8 h/semana. |
| 2026-10-20 | Decisões S1–S4 do SP01: DA07 (fonte da presença), RN02 com coautoria só de proponentes e coluna de apoios, nova RN09 (taxa oficial ao lado), RN03 e RN05 detalhadas. |
| 2026-10-20 | SP01 executado para a Câmara; decisões S1–S4 abertas. |
| 2026-10-20 | RN04 a RN07 decididas e detalhadas; RN02 define autor principal como primeiro signatário; nova RN08 (mínimo de 25% das sessões para o ranking); critérios das HUs, SP01 e glossário atualizados. |
| 2026-10-20 | Requisitos não funcionais RNF01 a RNF10, restrições (§8.3), alcance das legislaturas no escopo, riscos R06 e R07. |
| 2026-10-20 | DA06: web responsivo, mobile-first, sem app nativo no MVP. |
| 2026-10-20 | Criação do documento: problema, objetivos, público, escopo, fontes de dados, HU01 a HU03, regras de negócio RN01 a RN07, requisitos funcionais preliminares, decisões DA01 a DA05, riscos e pendências. |
