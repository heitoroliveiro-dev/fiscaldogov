# Transparência do Congresso Constitution

## Core Principles

### I. Todo dado é rastreável à fonte oficial (NON-NEGOTIABLE)
Todo número, voto, presença ou proposição exibido ao público MUST trazer a casa de origem, um link
para o registro oficial correspondente e a data da última atualização. Dado sem origem rastreável
MUST NOT ser exibido. Toda tela nova MUST ter teste que verifica a presença de fonte, link e data.

**Rationale**: o produto só tem valor se o eleitor puder conferir; um dado errado sobre uma pessoa
real vira acusação injusta (OE04, RF07, RF08, R01).

### II. Neutralidade política (NON-NEGOTIABLE)
Nenhum parlamentar ou partido MUST receber rótulo ideológico (esquerda, centro, direita ou
equivalente). Posicionamento MUST aparecer apenas como métrica derivada de votos, com metodologia
publicada. Textos da interface MUST descrever o dado, nunca julgá-lo. Cores de partido ou de status
MUST NOT ser usadas para qualificar pessoas.

**Rationale**: percepção de parcialidade destrói a credibilidade do site (DA04, R04).

### III. Estatística = regra pública + teste (NON-NEGOTIABLE)
Toda estatística exibida MUST ter (a) a regra de cálculo descrita na página de metodologia e
(b) testes automatizados escritos antes da implementação, cobrindo no mínimo, quando aplicáveis:
suplente, troca de partido no período, licença/missão oficial, sessão não deliberativa e votação
simbólica. É proibido skip, remoção de assert ou alteração de teste com o único propósito de
fazê-lo passar. Todo bug de cálculo MUST ganhar teste de regressão que falha antes do fix.

**Rationale**: o cálculo é o produto; erro aqui é reputacional e jurídico (R01, RF06).

### IV. Estatística ancorada no mandato em exercício
Toda estatística por parlamentar MUST ser calculada sobre os períodos em que ele estava em
exercício. Mandato MUST ser entidade de primeira classe, e o modelo de dados MUST suportar
múltiplas legislaturas desde o início.

**Rationale**: suplentes, afastamentos e mandatos de 8 anos no Senado tornam qualquer outro
denominador injusto (DA03, RN04, R03).

### V. Fontes isoladas; o site nunca depende da API oficial ao vivo
O site público MUST ler apenas do banco próprio e MUST ser somente leitura. Apenas o ETL escreve no
banco e apenas ele chama as APIs oficiais. Cada fonte (Câmara, Senado) MUST ter seu adaptador; o
domínio MUST NOT conhecer o formato de nenhuma API. Falha do ETL MUST NOT derrubar o site e MUST
gerar alerta.

**Rationale**: volume de dados, disponibilidade das APIs e entrada futura de novas casas sem alterar
o domínio (DA01, DA02, R02).

### VI. Segurança básica
Nenhuma credencial MUST estar no repositório; `.env` fica fora do versionamento; segredo MUST NOT
aparecer em log. Toda interação com o banco MUST usar query builder/ORM parametrizado; parâmetros de
ordenação e filtro MUST passar por allowlist.

**Rationale**: segredo em histórico de git é irreversível na prática; filtros e ordenação são a
principal superfície de entrada de um site de consulta.

### VII. Definition of Done com evidência
Nada é concluído por afirmação. Critérios MUST ser checáveis e a evidência anexada (output de teste,
comando + retorno, screenshot). Todo diff de feature MUST passar por review de subagente contra o
`plan.md`.

**Rationale**: revisar evidência é mais rápido e confiável que confiar em quem implementou —
inclusive um agente.

## Restrições adicionais de domínio

- **Web responsivo, mobile-first**: o produto é um site web responsivo, desenhado primeiro para
  consulta pelo celular; não há app nativo no MVP (DA06). Toda tela MUST funcionar a partir de
  360px de largura.
- **Público leigo**: linguagem simples; todo termo técnico (votação nominal, tramitação,
  suplente…) MUST ter explicação curta na própria tela.
- **Partido atual**: estatísticas usam o partido atual; o perfil MUST sinalizar troca de partido no
  período (RN01).
- **Escopo por casa**: Câmara e Senado são tratados separadamente no MVP; nenhum vínculo de
  proposição entre casas.
- **Regras "Proposta"** do contexto MUST NOT ser implementadas antes de confirmadas.

## Fluxo de desenvolvimento

Gitflow (`CONTRIBUTING.md`): nenhum commit direto em `main` ou `develop`. Feature não trivial:
Constitution → Specify → Clarify → Plan → Checklist → Tasks → Analyze → Implement. Trilha rápida só
para bug de ~1 arquivo ou UI trivial no padrão existente — nunca para mudança em regra de cálculo.
Mudança de arquitetura ou modelo de dados sempre passa por plan com seção de verificação explícita.

## Governance

Esta constituição prevalece sobre convenções que a contradigam. Emendas exigem registro do que
mudou e por quê, atualização de versão e checagem de impacto em `.specify/templates/`, `CLAUDE.md`
e `plan.md` de features em andamento. A lista de regras imutáveis do `CLAUDE.md` MUST ser
atualizada no mesmo commit de qualquer emenda.

Versionamento: MAJOR = remover/afrouxar princípio; MINOR = princípio novo ou expansão material;
PATCH = redação.

Todo `plan.md` MUST conter Constitution Check princípio por princípio. Complexidade que viole um
princípio exige justificativa no `plan.md` (Complexity Tracking), não só no código.

**Version**: 1.0.0 | **Ratified**: 2026-10-20 | **Last Amended**: 2026-10-20
