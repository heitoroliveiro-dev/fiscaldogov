# ADR-0003 — Modelo de domínio, adaptadores e pipeline do ETL

- **Status:** aceito
- **Data:** 2026-10-20
- **Decisores:** Heitor Oliveiro

## Contexto

O ETL em Python (ADR-0001) é o único escritor do banco e o único lugar onde as estatísticas são calculadas. Precisamos decidir como ele se organiza por dentro. As forças em jogo:

- **DA02:** um adaptador por fonte; o domínio não conhece o formato de nenhuma API. O Senado entra depois sem alterar o domínio (DA05).
- **DA03:** Mandato é entidade de primeira classe; estatística por parlamentar usa só os períodos em exercício; várias legislaturas desde o início (R03).
- **DA07 e SP01:** só a Câmara já exige três fontes (API v2 em JSON, webservice legado em XML, página pública em HTML), identificadores diferentes entre elas (id v2 e carteira, que muda a cada legislatura) e cruzamento de sessões pela ordem no dia.
- **Constituição, princípio III:** regra pública + teste; erro de dado vira acusação injusta (R01).
- **API v2 da Câmara:** `/deputados/{id}/historico` é um registro de eventos (entrada, saída, licença, reassunção) com a condição (titular/suplente) e o partido em cada momento — base para períodos de exercício e filiações.
- **Decisões do responsável (2026-10-20):** nomes do domínio em português; guardar o histórico dos números publicados quando o valor muda; guardar as respostas brutas das fontes no R2 por 12 meses.

## Decisão

### 1. Arquitetura hexagonal no ETL

```
etl/
├── dominio/          entidades e objetos de valor (dataclasses imutáveis) + cálculo das estatísticas
│                     em funções puras, sem I/O. É aqui que vive a metodologia.
├── portas/           interfaces (typing.Protocol) que o domínio e o pipeline esperam:
│                     FonteDaCasa, RepositorioDeDados, ArmazemDeBrutos, Publicador
├── adaptadores/
│   ├── camara/       api_v2 (JSON) · sitcamaraws (XML) · pagina_presenca (HTML)
│   ├── persistencia/ SQLAlchemy Core com reflection das tabelas do Prisma
│   ├── brutos_r2/    respostas brutas compactadas no R2
│   └── publicacao/   dispara o build no GitHub
├── reconciliacao/    liga identificadores entre fontes e cruza sessões (DA07)
└── pipeline/         orquestra uma execução; registra tudo em execucao_etl
```

- **Adaptadores são a camada anticorrupção:** recebem JSON/XML/HTML e devolvem tipos do domínio. Nenhum dicionário cru sai de um adaptador.
- **O domínio não importa nada de `adaptadores/`** — verificado por teste de arquitetura (import proibido).

### 2. Identidade

- Todo registro tem **chave própria** (inteiro gerado pelo banco). Identificadores das fontes ficam em `identificador_externo` (`sistema`, `valor`, legislatura quando o identificador é por legislatura, como a carteira).
- A **reconciliação** liga a carteira do webservice legado ao id v2 por `ObterDeputados` (legislatura atual) ou por nome + UF, com o histórico de nomes como desempate.
- **Falha fechada:** registro que não se reconcilia não entra no cálculo. A execução termina como "com pendências", as estatísticas dos parlamentares afetados **não são atualizadas** (fica o valor anterior) e um alerta é enviado. Número parcial nunca é publicado como completo (R01).

### 3. Mandato, exercício e filiação

- `Mandato` = parlamentar × casa × legislatura × UF.
- `PeriodoDeExercicio` = intervalo entre uma entrada e a saída seguinte no histórico, com a condição (titular/suplente) e os motivos. O denominador da presença só considera sessões dentro desses intervalos (RN04, DA03).
- `Filiacao` = parlamentar × partido × intervalo, derivada das mudanças de partido no histórico. Partido atual = filiação sem fim (RN01).

### 4. Coleta, cálculo e auditoria

- **Coleta diária** de uma janela dos últimos 30 dias, para captar correções da fonte; **coleta semanal** (domingo) da legislatura inteira.
- **Respostas brutas** compactadas no R2, guardadas **só quando o conteúdo muda** (hash igual ao da última versão da mesma URL não é regravado), com retenção de 12 meses.
- **Mudança em registro já coletado** (ex.: uma presença corrigida pela Câmara) é gravada em `alteracao_registro`.
- **Cálculo completo a cada execução:** as estatísticas são recalculadas do zero a partir das tabelas base. É determinístico e barato no volume do projeto.
- **Histórico de números publicados:** quando uma estatística muda, o valor anterior vai para `historico_estatistica` com o motivo — `novos_dados` (sessões novas), `correcao_fonte` (registro antigo mudou) ou `nova_versao_metodologia`.
- **Versão da metodologia** (SemVer) é uma constante do domínio, gravada em cada estatística e exibida na página de metodologia.

### 5. Escopo do schema

Só as entidades do Marco 1 (presença). Votação, voto, proposição e autoria entram com as suas features (HU02, HU03), em migrations próprias.

## Alternativas consideradas

- **Usar o id da Câmara como chave primária.** Mais simples hoje, mas colide com os códigos do Senado e não representa a carteira, que muda a cada legislatura.
- **Adaptador único por casa, sem separar as três fontes da Câmara.** Menos arquivos, mas mistura três formatos e três modos de falha; testar cada fonte com respostas gravadas fica mais difícil.
- **Calcular as estatísticas de forma incremental.** Menos processamento, mas o resultado passa a depender do histórico de execuções e as correções retroativas da fonte ficam difíceis de propagar. No volume do projeto (~300 mil registros de presença por legislatura), recalcular tudo é barato.
- **Publicar mesmo com registros não reconciliados.** Mantém o site sempre atualizado, mas pode publicar uma taxa calculada sobre dados incompletos — o risco central do projeto (R01).
- **Modelar votação e proposição desde já.** Antecipa trabalho de features fora do M1 e cria tabelas sem uso nem teste.

## Consequências

- **Positivas:**
  - Metodologia isolada em funções puras, testável sem banco nem rede.
  - O Senado entra como novo adaptador, sem alterar domínio nem cálculo.
  - Toda correção da fonte e todo número publicado têm rastro (`alteracao_registro`, `historico_estatistica`, respostas brutas).
- **Negativas / trade-offs:**
  - Mais estrutura de pastas do que um script único, para um desenvolvedor.
  - Com falha fechada, um problema de reconciliação deixa o número de um deputado desatualizado até ser resolvido.
  - Quem lê o código precisa conhecer os termos do domínio em português.
- **Riscos e mitigação:**
  - *A Câmara mudar o formato de uma fonte* → testes de adaptador com respostas gravadas; a execução falha com alerta em vez de gravar dado errado.
  - *Webservice legado ser desligado* → o adaptador é isolado; o impacto fica restrito à justificativa de ausência (DA07), e o site sinaliza a indisponibilidade.

## Referências

- `docs/01-architecture/modelagem-dados.md` — tabelas, chaves e invariantes.
- `docs/00-discovery/spikes/sp01-dados-presenca-autoria.md` — fontes e cruzamentos.
- API da Câmara: `/deputados/{id}/historico` (consultado em 2026-10-20: 648 deputados na 57ª, 197 com mais de um período).
