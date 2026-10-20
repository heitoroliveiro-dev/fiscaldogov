# Feature Specification: Fundação técnica — esqueleto ponta a ponta

**Feature Branch**: `feature/001-fundacao-tecnica`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Fundação técnica do projeto (F2 do ROADMAP, checkpoint 23/11/2026): um esqueleto que anda ponta a ponta — da coleta oficial até a página publicada — com as travas de qualidade que a constituição exige. Fecha o item F2: página no ar via integração contínua; coleta grava um deputado com fonte e data."

**Origem**: ROADMAP F2 · constituição v1.0.0 (princípios I, V, VI, VII) · ADR-0001, ADR-0002, ADR-0003 · `docs/01-architecture/modelagem-dados.md` · RNF01, RNF02, RNF04, RNF05, RNF06, RNF09.

## Clarifications

### Session 2026-10-20

- Q: Em qual endereço o esqueleto é publicado, já que o nome e o domínio definitivos ainda não existem? → A: Num subdomínio gratuito e provisório do provedor de publicação até o nome definitivo; o domínio próprio entra antes do Marco 1. (FR-027)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Um dado oficial publicado, com fonte e data (Priority: P1)

O responsável aciona a coleta; um deputado da 57ª legislatura é obtido na fonte oficial da Câmara, guardado no armazenamento próprio do projeto e aparece numa página pública com nome, partido atual, UF, a fonte oficial, o link para o registro original e a data da última atualização.

**Why this priority**: é a prova de que todas as peças conversam — fonte oficial, coleta, armazenamento, geração e publicação. Sem esse caminho, nenhuma feature de produto (HU01) pode ser entregue.

**Independent Test**: acionar a coleta manualmente, aguardar a publicação e abrir o endereço público no celular e no computador: a página mostra o deputado, o link leva ao registro oficial correspondente e a data exibida é a da coleta.

**Acceptance Scenarios**:

1. **Given** o armazenamento vazio, **When** o responsável aciona a coleta e ela termina com sucesso, **Then** a página pública passa a exibir nome, partido atual e UF do deputado selecionado, a indicação "Fonte: Câmara dos Deputados", o link para o registro original do deputado e a data e hora da coleta no horário de Brasília.
2. **Given** a página publicada, **When** um visitante a abre numa tela de 360 px e numa de 1440 px, nos temas claro e escuro, **Then** todo o conteúdo é legível, sem rolagem horizontal, e a verificação automática de acessibilidade não aponta violações.
3. **Given** a página publicada, **When** um buscador tenta indexá-la, **Then** a página informa que não deve ser indexada e se identifica como versão de testes.

---

### User Story 2 - Atualização diária sem intervenção, resistente a falhas (Priority: P2)

Todos os dias de madrugada a coleta roda sozinha e, se terminar com sucesso, o site é regenerado e publicado. Se a coleta ou a publicação falharem, o site continua no ar com a versão anterior, mostrando a data da última atualização bem-sucedida.

**Why this priority**: garante RNF01 e RNF02 antes de existir qualquer estatística — o padrão de operação diária que todas as features vão herdar.

**Independent Test**: observar as execuções agendadas por dias seguidos e conferir a data exibida; depois provocar uma falha da coleta e uma da publicação e conferir que o site segue no ar com a data anterior e que a falha ficou registrada.

**Acceptance Scenarios**:

1. **Given** o agendamento ativo, **When** chega 03:00 no horário de Brasília, **Then** a coleta roda, a execução é registrada com início, fim, status e contagens, e a página publicada mostra a nova data até as 08:00.
2. **Given** a fonte oficial fora do ar, **When** a coleta roda, **Then** a execução é registrada como falha com o erro, nenhum dado é alterado, nenhuma publicação é disparada, e o site continua exibindo a versão e a data anteriores.
3. **Given** uma coleta bem-sucedida, **When** a publicação falha, **Then** o site continua no ar com a versão anterior e a falha da publicação fica registrada.
4. **Given** uma execução ainda em andamento, **When** chega o horário da próxima, **Then** a nova não roda em paralelo.

---

### User Story 3 - Travas automáticas de qualidade (Priority: P2)

Toda alteração passa por verificações automáticas antes de ser registrada localmente e antes de ser integrada às linhas principais: formatação, regras de estilo, testes e a geração do site, para as duas partes do projeto (site e coleta).

**Why this priority**: o princípio VII da constituição e a camada "hook é lei" do método. Com uma pessoa só desenvolvendo, as travas são a revisão que não depende de memória.

**Independent Test**: tentar registrar uma alteração com erro de estilo e outra com teste falhando (devem ser bloqueadas); abrir uma proposta de integração com teste falhando (não pode ser integrada).

**Acceptance Scenarios**:

1. **Given** uma alteração com erro de formatação ou de estilo em qualquer das duas partes, **When** o responsável tenta registrá-la, **Then** o registro é bloqueado com a indicação do erro.
2. **Given** uma alteração que quebra um teste, **When** o responsável tenta registrá-la, **Then** o registro é bloqueado.
3. **Given** uma proposta de integração para `develop` ou `main`, **When** qualquer verificação falha (estilo, testes de unidade, testes de integração, geração do site), **Then** a integração fica impedida até todas passarem.
4. **Given** os testes de integração, **When** rodam, **Then** usam um armazenamento temporário criado do zero a partir da estrutura versionada, e a coleta grava nele com sucesso.

---

### User Story 4 - Acesso separado: só a coleta escreve (Priority: P2)

Existem dois perfis de acesso ao armazenamento: um que escreve, usado só pela coleta, e um que só lê, usado só pela geração do site. Uma tentativa de alteração com o perfil de leitura é recusada.

**Why this priority**: princípio V da constituição ("o site é somente leitura"), garantido pelo armazenamento e não apenas pelo código — e pré-requisito para expor o acesso de leitura à geração do site (ADR-0002).

**Independent Test**: com o perfil de leitura, tentar inserir, alterar e apagar um registro e alterar a estrutura: todas as tentativas são recusadas; a leitura funciona.

**Acceptance Scenarios**:

1. **Given** o perfil de leitura, **When** tenta inserir, alterar ou apagar qualquer registro, **Then** a operação é recusada.
2. **Given** o perfil de leitura, **When** tenta alterar a estrutura do armazenamento, **Then** a operação é recusada.
3. **Given** o perfil de escrita, **When** a coleta grava, **Then** a gravação funciona.

---

### User Story 5 - Cópia de segurança e restauração comprovada (Priority: P3)

Todo dia uma cópia de segurança do armazenamento é guardada fora do provedor principal, com retenção de 7 cópias diárias e 4 semanais, e existe um roteiro de restauração que foi executado ao menos uma vez com sucesso.

**Why this priority**: o dado ainda é pouco nesta fase, mas o mecanismo precisa existir antes que haja dados difíceis de recriar (lacuna de 2020, histórico de números publicados).

**Independent Test**: seguir o roteiro para restaurar a cópia mais recente num ambiente vazio e comparar as contagens de registros com a origem.

**Acceptance Scenarios**:

1. **Given** uma coleta bem-sucedida, **When** ela termina, **Then** uma cópia de segurança com data é guardada no armazenamento externo.
2. **Given** mais de 7 cópias diárias, **When** uma nova é guardada, **Then** as diárias excedentes são removidas, preservando uma por semana nas últimas 4 semanas.
3. **Given** o roteiro de restauração, **When** seguido num ambiente vazio, **Then** o ambiente restaurado tem as mesmas contagens de registros da origem.
4. **Given** uma falha ao guardar a cópia, **When** a coleta termina, **Then** a execução é registrada como "com pendências", sem impedir a publicação.

### Edge Cases

- A fonte oficial responde em formato diferente do esperado: a coleta falha com erro registrado, sem gravar dado parcial (falha fechada, ADR-0003).
- O deputado selecionado deixa de estar em exercício: na coleta seguinte, a regra de seleção escolhe outro deputado, e a página muda de acordo.
- A fonte devolve campos sensíveis (ex.: CPF): eles são descartados e não chegam ao armazenamento nem à página (RNF06).
- A coleta roda sem uma credencial ou configuração obrigatória: falha no início, com mensagem clara, sem efeitos parciais.
- A resposta bruta da fonte é idêntica à da última coleta: não é guardada de novo.
- A data exibida sempre corresponde à coleta que gerou a versão publicada, não à última tentativa.

## Requirements *(mandatory)*

### Functional Requirements

**Página pública**

- **FR-001**: A página pública DEVE exibir nome parlamentar, partido atual e UF de um deputado em exercício na 57ª legislatura.
- **FR-002**: A página DEVE exibir a casa de origem como fonte, um link para o registro original do deputado na fonte oficial e a data e hora da última atualização no horário de Brasília (RF07, RF08, princípio I).
- **FR-003**: A página DEVE funcionar de 360 px a 1440 px sem rolagem horizontal, com layout próprio para telas grandes, nos temas claro e escuro (seguindo a preferência do sistema, com troca manual), usando o design system do projeto (RNF09, diretrizes de UI D1–D3).
- **FR-004**: A página DEVE passar na verificação automática de acessibilidade WCAG 2.2 AA sem violações (RNF05).
- **FR-005**: A página DEVE se identificar como versão de testes e instruir buscadores a não indexá-la até o Marco 1.
- **FR-006**: O deputado exibido DEVE ser escolhido por regra objetiva e documentada — o primeiro em ordem alfabética do nome parlamentar entre os em exercício na data da coleta — para não destacar ninguém por escolha pessoal (princípio II).

**Coleta**

- **FR-007**: A coleta DEVE obter, na fonte oficial da Câmara, a lista de deputados da 57ª legislatura e o histórico do deputado selecionado, e guardar parlamentar, identificador na fonte, mandato, períodos de exercício e filiações conforme `docs/01-architecture/modelagem-dados.md`.
- **FR-008**: Todo registro guardado DEVE ter a URL da fonte e a data e hora da coleta.
- **FR-009**: A coleta NÃO DEVE guardar CPF nem dados pessoais não relacionados ao mandato (RNF06).
- **FR-010**: Cada execução DEVE ser registrada com início, fim, status (sucesso, com pendências, falha), contagens de registros lidos e gravados por entidade, erros e a versão do código.
- **FR-011**: A coleta DEVE guardar a resposta bruta de cada fonte consultada quando o conteúdo mudou desde a última versão guardada, com retenção de 12 meses (ADR-0003).
- **FR-012**: Se qualquer etapa da coleta falhar, nenhum dado da execução DEVE ser gravado parcialmente; a execução é registrada como falha.
- **FR-013**: A coleta DEVE rodar automaticamente todos os dias às 03:00 no horário de Brasília, sem execuções simultâneas, e DEVE poder ser acionada manualmente pelo responsável.

**Publicação**

- **FR-014**: Ao fim de uma coleta bem-sucedida, o site DEVE ser regenerado e publicado automaticamente, com os dados disponíveis até as 08:00 (RNF01).
- **FR-015**: O site também DEVE ser regenerado e publicado a cada integração na linha principal (`main`).
- **FR-016**: Se a coleta ou a publicação falharem, a versão publicada anterior DEVE permanecer no ar, e a falha DEVE ficar registrada (RNF02).

**Armazenamento e acesso**

- **FR-017**: A estrutura do armazenamento DEVE ser criada e alterada apenas por scripts versionados; aplicá-los a um ambiente vazio DEVE produzir a mesma estrutura do ambiente de produção.
- **FR-018**: As invariantes da modelagem que se aplicam às entidades desta feature DEVEM ser garantidas pelo armazenamento: períodos de exercício sem sobreposição dentro de um mandato e no máximo uma filiação aberta por parlamentar.
- **FR-019**: DEVEM existir dois perfis de acesso: escrita, usado só pela coleta, e leitura, usado só pela geração do site; o perfil de leitura NÃO DEVE conseguir inserir, alterar, apagar nem mudar a estrutura (princípio V).
- **FR-020**: Credenciais DEVEM ficar apenas nos cofres de segredos de cada provedor; a credencial de escrita só no ambiente da coleta; nenhuma no repositório (princípio VI).

**Travas de qualidade**

- **FR-021**: Antes de registrar uma alteração localmente, DEVEM rodar formatação, regras de estilo e testes relacionados das partes alteradas (site e coleta), além das travas já existentes (segredos, padrão de branch, padrão de mensagem).
- **FR-022**: Cada proposta de integração para `develop` ou `main` DEVE rodar regras de estilo, testes de unidade, testes de integração contra armazenamento temporário criado a partir da estrutura versionada, e a geração do site; todas obrigatórias para a integração.
- **FR-023**: DEVE existir teste automatizado que impede as regras de negócio da coleta de depender diretamente do código que lê cada fonte (ADR-0003).

**Cópia de segurança**

- **FR-024**: Ao fim de cada coleta bem-sucedida, DEVE ser guardada uma cópia de segurança completa fora do provedor principal, com retenção de 7 diárias e 4 semanais.
- **FR-025**: DEVE existir um roteiro de restauração escrito, executado ao menos uma vez nesta feature, com a evidência anexada.
- **FR-026**: Falha ao guardar a cópia DEVE marcar a execução como "com pendências", sem impedir a publicação.

**Endereço público**

- **FR-027**: A página DEVE estar publicada num subdomínio gratuito e provisório do provedor de publicação, até que o nome e o domínio definitivos existam (antes do Marco 1). Trocar o endereço depois não pode exigir mudança além de configuração.

### Key Entities *(include if feature involves data)*

- **Casa legislativa** e **Legislatura**: referência fixa (Câmara; 57ª legislatura).
- **Parlamentar**: pessoa, com nome parlamentar e foto; sem CPF.
- **Identificador externo**: como cada fonte identifica o parlamentar.
- **Mandato**: parlamentar × casa × legislatura × UF.
- **Período de exercício**: intervalo em que o parlamentar exerceu o mandato, com a condição (titular ou suplente).
- **Partido** e **Filiação**: partido do parlamentar em cada intervalo; a filiação sem fim é o partido atual.
- **Execução da coleta**: registro de cada execução, com status, contagens e erros.
- **Coleta bruta**: referência à resposta original de uma fonte, guardada fora do armazenamento principal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em celular com rede 4G, o conteúdo principal da página aparece em até 2,5 segundos (RNF03).
- **SC-002**: Em 5 dias seguidos, a data exibida na página é atualizada até as 08:00 sem nenhuma ação manual.
- **SC-003**: Com uma falha provocada na coleta e outra na publicação, a página continua disponível nas duas situações e exibe a data anterior.
- **SC-004**: 100% das tentativas de registrar alteração com erro de estilo ou teste falhando são bloqueadas, e nenhuma proposta com verificação falhando consegue ser integrada.
- **SC-005**: 100% das tentativas de escrita com o perfil de leitura são recusadas.
- **SC-006**: A restauração de uma cópia de segurança num ambiente vazio termina em até 30 minutos, com contagens de registros idênticas às da origem.
- **SC-007**: A página tem zero violações na verificação automática de acessibilidade e zero rolagem horizontal em 360 px e em 1440 px.
- **SC-008**: Um ambiente vazio construído só a partir dos scripts versionados tem estrutura idêntica à de produção (comparação sem diferenças).
- **SC-009**: O custo mensal total do projeto continua em até US$ 10 (RNF04).

## Assumptions

- O deputado é escolhido pela regra de FR-006 para evitar destaque pessoal; a página é de testes e fica fora dos buscadores até o Marco 1.
- Alertas ativos (mensagem no celular, monitor externo) ficam para a F4; nesta feature as falhas ficam registradas na execução e nas notificações padrão dos provedores.
- "Testes relacionados" no registro local significa os testes das partes alteradas; a suíte completa roda na integração contínua.
- A estrutura criada nesta feature cobre só as entidades listadas acima; sessões, presença e estatísticas entram com a HU01.
- Horário de Brasília sem horário de verão (03:00 = 06:00 UTC).
- **Dependências humanas (⚠️, do responsável; provedores definidos no ADR-0002):**
  - criar a conta e as credenciais do provedor de publicação e do armazenamento externo de cópias;
  - criar uma credencial do repositório de código com permissão apenas para disparar a publicação;
  - criar no provedor principal o armazenamento e a coleta agendada, e cadastrar os segredos;
  - configurar no repositório de código a proteção de `main` e `develop` exigindo as verificações (FR-022).
