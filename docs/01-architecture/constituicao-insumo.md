<!--
Insumo para /speckit-constitution. Não copie direto para .specify/memory/:
entregue este texto ao comando, adaptado, e deixe-o gerar o arquivo oficial
(com Sync Impact Report e checagem dos templates).

STATUS: PROPOSTA. Cada princípio foi derivado do contexto do projeto
(referência entre parênteses), mas a redação e a marcação NON-NEGOTIABLE
são sugestões — confirme, corte ou reescreva antes de rodar o comando.
-->

# Transparência do Congresso Constitution

## Core Principles

### I. Todo dado é rastreável à fonte oficial (NON-NEGOTIABLE)
Todo número, voto, presença ou proposição exibido ao público traz a casa de
origem, um link para o registro oficial correspondente e a data da última
atualização. Dado sem origem rastreável não é exibido. Toda tela nova tem teste
que verifica a presença de fonte, link e data.

**Rationale**: o produto só tem valor se o eleitor puder conferir; um dado
errado sobre uma pessoa real vira acusação injusta (OE04, RF07, RF08, R01).

### II. Neutralidade política (NON-NEGOTIABLE)
Nenhum parlamentar ou partido recebe rótulo ideológico (esquerda, centro,
direita ou equivalente). Posicionamento só aparece como métrica derivada de
votos, com metodologia publicada. Textos da interface descrevem o dado, nunca o
julgam. Cores de partido ou de status não são usadas para qualificar pessoas.

**Rationale**: percepção de parcialidade destrói a credibilidade do site (DA04,
R04).

### III. Estatística = regra pública + teste (NON-NEGOTIABLE)
Toda estatística exibida tem (a) a regra de cálculo descrita na página de
metodologia e (b) testes automatizados escritos antes da implementação,
cobrindo no mínimo: suplente, troca de partido no período, licença/missão
oficial, sessão não deliberativa e votação simbólica, quando aplicáveis.
Proibido skip, remoção de assert ou alteração de teste com o único propósito
de fazê-lo passar. Todo bug de cálculo ganha teste de regressão antes do fix.

**Rationale**: o cálculo é o produto; erro aqui é reputacional e jurídico (R01,
RF06).

### IV. Estatística ancorada no mandato em exercício
Toda estatística por parlamentar é calculada sobre os períodos em que ele
estava em exercício. Mandato é entidade de primeira classe; o modelo suporta
múltiplas legislaturas desde o início.

**Rationale**: suplentes, afastamentos e mandatos de 8 anos no Senado tornam
qualquer outro denominador injusto (DA03, RN04, R03).

### V. Fontes isoladas; o site nunca depende da API oficial ao vivo
O site público lê apenas do banco próprio e é somente leitura. Só o ETL escreve
no banco e só ele chama as APIs oficiais. Cada fonte (Câmara, Senado) tem seu
adaptador; o domínio não conhece o formato de nenhuma API. Falha do ETL não
derruba o site e gera alerta.

**Rationale**: volume de dados, disponibilidade das APIs e entrada futura de
novas casas sem alterar o domínio (DA01, DA02, R02).

### VI. Segurança básica
Nenhuma credencial no repositório; `.env` fora do versionamento; segredo nunca
em log. Toda interação com o banco usa query builder/ORM parametrizado;
parâmetros de ordenação e filtro passam por allowlist.

**Rationale**: segredo em histórico de git é irreversível na prática; filtros
e ordenação são a principal superfície de entrada de um site de consulta.

### VII. Definition of Done com evidência
Nada é concluído por afirmação. Critérios checáveis; evidência anexada (output
de teste, comando + retorno, screenshot). Todo diff de feature passa por review
de subagente contra o `plan.md`.

**Rationale**: revisar evidência é mais rápido e confiável que confiar em quem
implementou — inclusive um agente.

## Restrições adicionais de domínio
- **Público leigo, mobile-first**: linguagem simples; todo termo técnico
  (votação nominal, tramitação, suplente…) tem explicação curta na própria tela.
- **Partido atual**: estatísticas usam o partido atual; o perfil sinaliza troca
  de partido no período (RN01).
- **Escopo por casa**: Câmara e Senado são tratados separadamente no MVP; nenhum
  vínculo de proposição entre casas.
- **Regras "Proposta"** do contexto (RN04–RN07) não são implementadas antes de
  confirmadas.

## Fluxo de desenvolvimento
Gitflow (`CONTRIBUTING.md`). Feature não trivial: Constitution → Specify →
Clarify → Plan → Checklist → Tasks → Analyze → Implement. Trilha rápida só para
bug de ~1 arquivo ou UI trivial no padrão existente — nunca para mudança em
regra de cálculo. Mudança de arquitetura ou modelo de dados sempre passa por
plan com seção de verificação explícita.

## Governance
Esta constituição prevalece sobre convenções que a contradigam. Emendas exigem
registro do que mudou e por quê, atualização de versão e checagem de impacto
em `.specify/templates/`, `CLAUDE.md` e `plan.md` de features em andamento.

Versionamento: MAJOR = remover/afrouxar princípio; MINOR = princípio novo ou
expansão material; PATCH = redação.

Complexidade que viole um princípio exige justificativa no `plan.md`
(Complexity Tracking), não só no código.

**Version**: 1.0.0 | **Ratified**: AAAA-MM-DD | **Last Amended**: AAAA-MM-DD
