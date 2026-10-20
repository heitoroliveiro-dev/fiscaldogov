# Feature Specification: Fundação técnica — esqueleto ponta a ponta

**Feature Branch**: `feature/001-fundacao-tecnica`

**Created**: 2026-10-20

**Status**: Draft

**Input**: User description: "Fundação técnica do projeto (F2 do ROADMAP, checkpoint 23/11/2026): um esqueleto que anda ponta a ponta — da coleta oficial até a página publicada — com as travas de qualidade que a constituição exige. Fecha o item F2: página no ar via integração contínua; coleta grava um deputado com fonte e data."

**Origem**: ROADMAP F2 · constituição v1.0.0 (princípios I, V, VI, VII) · ADR-0001, ADR-0002, ADR-0003 · `docs/01-architecture/modelagem-dados.md` · RNF01, RNF02, RNF04, RNF05, RNF06, RNF09.

## Clarifications

### Session 2026-10-20

- Q: Em qual endereço o esqueleto é publicado, já que o nome e o domínio definitivos ainda não existem? → A: Num subdomínio gratuito e provisório do provedor de publicação até o nome definitivo; o domínio próprio entra antes do Marco 1. (FR-027)
- Q: Se a coleta das 03:00 falhar porque a fonte oficial está fora do ar, o sistema deve tentar de novo antes do prazo das 08:00? → A: Até 3 tentativas dentro da execução, com espera crescente; se ainda falhar, nova execução automática às 05:00. (FR-013, US2)
- Q: Por quanto tempo uma execução da coleta pode rodar antes de ser interrompida e registrada como falha? → A: 60 minutos. (FR-013a, US2)

### Session 2026-10-20 — revisão do checklist de confiabilidade e operação

- Q: Como o responsável fica sabendo de uma falha antes da F4? → A: Alerta no canal de mensagens do RNF07 já nesta feature, enviado pela coleta e pela publicação ao falhar. (FR-029, CHK001, CHK011)
- Q: A página avisa quando o dado está velho? → A: Sim, quando a última conferência tiver mais de 48 h, calculado no aparelho do visitante no momento da visita. (FR-002a, CHK003)
- Q: O que significa a data exibida? → A: "Conferido na fonte oficial em …": data da última coleta bem-sucedida, mesmo sem mudança no dado. (FR-002, CHK018)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Um dado oficial publicado, com fonte e data (Priority: P1)

O responsável aciona a coleta; um deputado da 57ª legislatura é obtido na fonte oficial da Câmara, guardado no armazenamento próprio do projeto e aparece numa página pública com nome, partido atual, UF, a fonte oficial, o link para o registro original e a data da última conferência na fonte.

**Why this priority**: é a prova de que todas as peças conversam — fonte oficial, coleta, armazenamento, geração e publicação. Sem esse caminho, nenhuma feature de produto (HU01) pode ser entregue.

**Independent Test**: acionar a coleta manualmente, aguardar a publicação e abrir o endereço público no celular e no computador: a página mostra o deputado, o link leva ao registro oficial correspondente e a data exibida é a da coleta.

**Acceptance Scenarios**:

1. **Given** o armazenamento vazio, **When** o responsável aciona a coleta e ela termina com sucesso, **Then** a página pública passa a exibir nome, partido atual e UF do deputado selecionado, a indicação "Fonte: Câmara dos Deputados", o link para o registro original do deputado e "Conferido na fonte oficial em" com a data e hora da coleta no horário de Brasília.
2. **Given** a página publicada, **When** um visitante a abre numa tela de 360 px e numa de 1440 px, nos temas claro e escuro, **Then** todo o conteúdo é legível, sem rolagem horizontal, e a verificação automática de acessibilidade não aponta violações.
3. **Given** a página publicada, **When** um buscador tenta indexá-la, **Then** a página informa que não deve ser indexada e se identifica como versão de testes.
4. **Given** uma versão publicada cuja última conferência foi há mais de 48 horas, **When** um visitante abre a página, **Then** ela exibe o aviso de que os dados podem estar desatualizados, junto com a data da última conferência — mesmo que nenhuma coleta ou publicação tenha rodado desde então.

---

### User Story 2 - Atualização diária sem intervenção, resistente a falhas (Priority: P2)

Todos os dias de madrugada a coleta roda sozinha e, se terminar com sucesso, o site é regenerado e publicado. Se a coleta ou a publicação falharem, o site continua no ar com a versão anterior, mostrando a data da última conferência bem-sucedida, e o responsável recebe um alerta.

**Why this priority**: garante RNF01 e RNF02 antes de existir qualquer estatística — o padrão de operação diária que todas as features vão herdar.

**Independent Test**: observar as execuções agendadas por dias seguidos e conferir a data exibida; depois provocar uma falha da coleta e uma da publicação e conferir que o site segue no ar com a data anterior, que a falha ficou registrada e que o alerta chegou.

**Acceptance Scenarios**:

1. **Given** o agendamento ativo, **When** chega 03:00 no horário de Brasília, **Then** a coleta roda, a execução é registrada com início, fim, status e contagens, e a página publicada mostra a nova data até as 08:00.
2. **Given** a fonte oficial fora do ar, **When** a coleta roda, **Then** ela tenta até 3 vezes com espera crescente; se todas falharem, a execução é registrada como falha com o erro, nenhum dado é alterado, nenhuma publicação é disparada, e o site continua exibindo a versão e a data anteriores.
3. **Given** a execução das 03:00 registrada como falha, **When** chega 05:00 no horário de Brasília, **Then** uma nova execução roda automaticamente; se ela tiver sucesso, a página mostra a nova data até as 08:00.
4. **Given** uma coleta bem-sucedida, **When** a publicação falha, **Then** o site continua no ar com a versão anterior, a falha da publicação fica registrada e o responsável é alertado; a próxima coleta bem-sucedida (ou integração em `main`) publica de novo.
5. **Given** uma execução ainda em andamento, **When** chega o horário da próxima, **Then** a nova não roda em paralelo.
6. **Given** uma execução travada, **When** ela completa 60 minutos, **Then** é interrompida, registrada como falha por tempo esgotado, e a execução seguinte roda normalmente.
7. **Given** uma execução que deixou de existir sem registrar o fim (processo encerrado à força), **When** a execução seguinte começa, **Then** a anterior é registrada como falha ("interrompida") e o responsável é alertado.
8. **Given** uma coleta em andamento, **When** o responsável aciona uma coleta manual, **Then** a manual não começa e o responsável é informado de que já há uma em andamento.

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

A cada coleta bem-sucedida (normalmente uma por dia) uma cópia de segurança do armazenamento é guardada fora do provedor principal e conferida como restaurável, com retenção de 7 cópias diárias e 4 semanais, e existe um roteiro de restauração que foi executado ao menos uma vez com sucesso.

**Why this priority**: o dado ainda é pouco nesta fase, mas o mecanismo precisa existir antes que haja dados difíceis de recriar (lacuna de 2020, histórico de números publicados).

**Independent Test**: seguir o roteiro para restaurar a cópia mais recente num ambiente vazio e comparar as contagens de registros com a origem.

**Acceptance Scenarios**:

1. **Given** uma coleta bem-sucedida, **When** ela termina, **Then** uma cópia de segurança com data é guardada no armazenamento externo.
2. **Given** mais de 7 cópias diárias, **When** uma nova é guardada, **Then** as diárias excedentes são removidas, preservando uma por semana nas últimas 4 semanas.
3. **Given** o roteiro de restauração, **When** seguido num ambiente vazio, **Then** o ambiente restaurado tem as mesmas contagens de registros da origem.
4. **Given** uma falha ao guardar a cópia, **When** a coleta termina, **Then** a execução é registrada como "com pendências", sem impedir a publicação.
5. **Given** uma cópia recém-guardada, **When** sua leitura falha na conferência de integridade, **Then** a execução é registrada como "com pendências" e o responsável é alertado.

### Edge Cases

- A fonte oficial fica fora do ar só por alguns minutos: as tentativas dentro da execução absorvem a queda; uma queda longa é coberta pela execução das 05:00.
- A coleta trava (ex.: a fonte para de responder no meio da transferência): ao completar 60 minutos é interrompida e registrada como falha, liberando a execução seguinte.
- A fonte oficial responde em formato diferente do esperado: a coleta falha com erro registrado, sem gravar dado parcial (falha fechada, ADR-0003).
- O deputado selecionado deixa de estar em exercício: na coleta seguinte, a regra de seleção escolhe outro deputado, e a página muda de acordo.
- A fonte devolve campos sensíveis (ex.: CPF): eles são descartados e não chegam ao armazenamento nem à página (RNF06).
- A coleta roda sem uma credencial ou configuração obrigatória: falha no início, com mensagem clara, sem efeitos parciais.
- A resposta bruta da fonte é idêntica à da última coleta: não é guardada de novo.
- A data exibida sempre corresponde à coleta que gerou a versão publicada, não à última tentativa.
- A fonte devolve lista vazia, menos de 500 deputados em exercício, ou o deputado selecionado sem histórico: a coleta falha (suspeita de fonte incompleta), sem gravar.
- O histórico vem com eventos fora de ordem: são ordenados pela data e hora do evento antes da derivação; empate mantém a ordem da fonte.
- A fonte fica fora do ar por vários dias: não há recuperação de dias perdidos nesta feature — a coleta registra o estado atual, e a primeira execução bem-sucedida atualiza tudo. O aviso de dado envelhecido (FR-002a) aparece após 48 h.
- A aplicação de uma nova estrutura de armazenamento falha na implantação: a implantação é abortada e a versão anterior da coleta continua agendada.
- O limite rígido de gasto do provedor principal é atingido: armazenamento e coleta param; o site publicado continua no ar com o aviso de dado envelhecido após 48 h; o provedor notifica o responsável por e-mail.
- Uma credencial expira (ex.: a que dispara a publicação): a etapa que a usa falha, a execução fica "com pendências" ou "falha", e o alerta identifica a credencial.

## Requirements *(mandatory)*

### Functional Requirements

**Página pública**

- **FR-001**: A página pública DEVE exibir nome parlamentar, partido atual e UF de um deputado em exercício na 57ª legislatura.
- **FR-002**: A página DEVE exibir a casa de origem como fonte, um link para o registro original do deputado na fonte oficial e "Conferido na fonte oficial em" seguido da data e hora da última coleta bem-sucedida, no horário de Brasília — mesmo que nenhum dado tenha mudado nela (RF07, RF08, princípio I).
- **FR-002a**: Quando a última conferência tiver mais de 48 horas no momento da visita, a página DEVE exibir o aviso "Atenção: os dados podem estar desatualizados". O cálculo DEVE ser feito no aparelho do visitante, para funcionar mesmo que coleta e publicação estejam paradas.
- **FR-003**: A página DEVE funcionar de 360 px a 1440 px sem rolagem horizontal, com layout próprio para telas grandes, nos temas claro e escuro (seguindo a preferência do sistema, com troca manual), usando o design system do projeto (RNF09, diretrizes de UI D1–D3).
- **FR-004**: A página DEVE passar na verificação automática de acessibilidade WCAG 2.2 AA sem violações (RNF05).
- **FR-005**: A página DEVE se identificar como versão de testes e instruir buscadores a não indexá-la até o Marco 1.
- **FR-006**: O deputado exibido DEVE ser escolhido por regra objetiva e documentada — o primeiro em ordem alfabética do nome parlamentar entre os em exercício na data da coleta — para não destacar ninguém por escolha pessoal (princípio II).

**Coleta**

- **FR-007**: A coleta DEVE obter, na fonte oficial da Câmara, a lista de deputados da 57ª legislatura e o histórico do deputado selecionado, e guardar parlamentar, identificador na fonte, mandato, períodos de exercício e filiações conforme `docs/01-architecture/modelagem-dados.md`. A cada execução também DEVE atualizar o histórico de todos os parlamentares já guardados.
- **FR-007a**: Executar a coleta duas vezes sem mudança na fonte DEVE produzir o mesmo estado, sem registros duplicados.
- **FR-007b**: A coleta DEVE falhar, sem gravar, se a fonte devolver lista vazia, menos de 500 deputados em exercício ou o deputado selecionado sem histórico; eventos do histórico DEVEM ser ordenados por data e hora antes da derivação.
- **FR-008**: Todo registro guardado DEVE ter a URL da fonte e a data e hora da coleta.
- **FR-009**: A coleta NÃO DEVE guardar CPF nem dados pessoais não relacionados ao mandato (RNF06).
- **FR-010**: Cada execução DEVE ser registrada com início, fim, gatilho (agendada, reserva, manual), status, contagens de registros lidos e gravados por entidade, tentativas, erros e a versão do código. Status: "em andamento"; "sucesso"; "com pendências" (dados gravados, mas falhou a guarda de resposta bruta, a cópia de segurança, a conferência da cópia ou o disparo da publicação); "falha" (nada gravado); "dispensada" (execução de reserva desnecessária).
- **FR-011**: A coleta DEVE guardar a resposta bruta de cada fonte consultada quando o conteúdo mudou desde a última versão guardada, com retenção de 12 meses (ADR-0003). Falha ao guardar a resposta bruta DEVE marcar a execução como "com pendências", sem desfazer os dados.
- **FR-012**: Se a obtenção ou a gravação dos dados falhar, nenhum dado da execução DEVE ser gravado parcialmente; a execução é registrada como falha. Respostas brutas já guardadas antes da falha permanecem, como evidência do que a fonte devolveu.
- **FR-013**: A coleta DEVE rodar automaticamente todos os dias às 03:00 no horário de Brasília, sem execuções simultâneas, e DEVE poder ser acionada manualmente pelo responsável. O início DEVE ocorrer entre 03:00 e 03:15. Uma coleta manual NÃO DEVE começar se houver outra em andamento. Diante de falha passageira de acesso à fonte (sem resposta, tempo esgotado, fonte sobrecarregada ou com erro interno), DEVE tentar até 3 vezes na mesma execução, com espera crescente entre as tentativas; falhas permanentes (pedido recusado, formato inesperado) encerram a execução sem nova tentativa; se a execução das 03:00 terminar em falha, uma nova execução automática DEVE rodar às 05:00 (e só nesse caso).
- **FR-013a**: Uma execução que ultrapassar 60 minutos DEVE ser interrompida e registrada como falha por tempo esgotado, sem gravar dados parciais, de modo que nunca impeça a execução seguinte. Uma execução encerrada à força sem registrar o fim DEVE ser registrada como falha ("interrompida") pela execução seguinte, se tiver começado há mais de 60 minutos.

**Publicação**

- **FR-014**: Ao fim de uma coleta bem-sucedida, o site DEVE ser regenerado e publicado automaticamente, com os dados disponíveis até as 08:00 (RNF01).
- **FR-015**: O site também DEVE ser regenerado e publicado a cada integração na linha principal (`main`).
- **FR-016**: Se a coleta ou a publicação falharem, a versão publicada anterior DEVE permanecer no ar, e a falha DEVE ficar registrada (RNF02). A publicação volta a ocorrer na próxima coleta bem-sucedida ou na próxima integração em `main`, sem ação manual.
- **FR-016a**: A geração do site DEVE falhar (mantendo a versão anterior no ar) se não houver deputado em exercício ou execução bem-sucedida no armazenamento — nunca se publica página sem dado.

**Armazenamento e acesso**

- **FR-017**: A estrutura do armazenamento DEVE ser criada e alterada apenas por scripts versionados; aplicá-los a um ambiente vazio DEVE produzir a mesma estrutura do ambiente de produção.
- **FR-017a**: Se a aplicação de um script de estrutura falhar na implantação, a implantação DEVE ser abortada, mantendo a versão anterior da coleta. A reversão de uma estrutura já aplicada DEVE ser feita por um novo script corretivo ou, em último caso, pela restauração da cópia de segurança (roteiro de FR-025).
- **FR-018**: As invariantes da modelagem que se aplicam às entidades desta feature DEVEM ser garantidas pelo armazenamento: períodos de exercício sem sobreposição dentro de um mandato e no máximo uma filiação aberta por parlamentar.
- **FR-019**: DEVEM existir dois perfis de acesso: escrita, usado só pela coleta, e leitura, usado só pela geração do site; o perfil de leitura NÃO DEVE conseguir inserir, alterar, apagar nem mudar a estrutura (princípio V).
- **FR-020**: Credenciais DEVEM ficar apenas nos cofres de segredos de cada provedor; a credencial de escrita só no ambiente da coleta; nenhuma no repositório (princípio VI).
- **FR-020a**: Toda credencial com validade DEVE ter a data de expiração registrada no roteiro de operação, e a falha causada por credencial expirada ou revogada DEVE gerar alerta que identifique a credencial.

**Travas de qualidade**

- **FR-021**: Antes de registrar uma alteração localmente, DEVEM rodar formatação, regras de estilo e testes relacionados das partes alteradas (site e coleta), além das travas já existentes (segredos, padrão de branch, padrão de mensagem).
- **FR-022**: Cada proposta de integração para `develop` ou `main` DEVE rodar regras de estilo, testes de unidade, testes de integração contra armazenamento temporário criado a partir da estrutura versionada, e a geração do site; todas obrigatórias para a integração.
- **FR-023**: DEVE existir teste automatizado que impede as regras de negócio da coleta de depender diretamente do código que lê cada fonte (ADR-0003).

**Cópia de segurança**

- **FR-024**: Ao fim de cada coleta bem-sucedida, DEVE ser guardada uma cópia de segurança completa fora do provedor principal, com retenção de 7 diárias e 4 semanais, e DEVE ser conferida como legível logo após ser guardada. Perda máxima aceitável de dados (RPO): os dados desde a última coleta bem-sucedida — até cerca de 1 dia, e todos recriáveis a partir da fonte nesta feature.
- **FR-025**: DEVEM existir roteiros escritos para: restauração da cópia de segurança (executado ao menos uma vez nesta feature, com evidência), acionamento manual da coleta e leitura do status de uma execução, e troca de credenciais (incluindo os perfis de acesso ao armazenamento).
- **FR-026**: Falha ao guardar ou conferir a cópia DEVE marcar a execução como "com pendências", sem impedir a publicação.

**Endereço público**

- **FR-027**: A página DEVE estar publicada num subdomínio gratuito e provisório do provedor de publicação, até que o nome e o domínio definitivos existam (antes do Marco 1). Trocar o endereço depois não pode exigir mudança além de configuração.

**Operação e alertas**

- **FR-028**: Cada versão publicada DEVE identificar, de forma legível por máquina, a execução da coleta e a versão do código que a geraram.
- **FR-029**: Falha da coleta, execução "com pendências", execução interrompida e falha da publicação DEVEM gerar alerta no canal de mensagens do responsável definido no RNF07 em até 1 hora, com o tipo da falha e o identificador da execução. Falha ao enviar o alerta NÃO DEVE alterar o resultado da execução.
- **FR-030**: Coleta e publicação DEVEM produzir registros de operação (início, etapas, tentativas, erros) retidos pelo período padrão de cada provedor; registros NÃO DEVEM conter credenciais, tokens nem endereços de conexão com senha (princípio VI).
- **FR-031**: O alerta de gasto em US$ 10 e o limite rígido de US$ 20 do provedor principal (RNF04) DEVEM estar configurados ao fim desta feature.

### Key Entities *(include if feature involves data)*

- **Casa legislativa** e **Legislatura**: referência fixa (Câmara; 57ª legislatura).
- **Parlamentar**: pessoa, com nome parlamentar e foto; sem CPF.
- **Identificador externo**: como cada fonte identifica o parlamentar.
- **Mandato**: parlamentar × casa × legislatura × UF.
- **Período de exercício**: intervalo em que o parlamentar exerceu o mandato, com a condição (titular ou suplente).
- **Partido** e **Filiação**: partido do parlamentar em cada intervalo; a filiação sem fim é o partido atual.
- **Execução da coleta**: registro de cada execução, com gatilho, status, tentativas, contagens, erros e pendências.
- **Coleta bruta**: referência à resposta original de uma fonte, guardada fora do armazenamento principal.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em celular com rede 4G, o conteúdo principal da página aparece em até 2,5 segundos (RNF03).
- **SC-002**: Em 5 dias seguidos, a data exibida na página é atualizada até as 08:00 sem nenhuma ação manual. Dia coberto pela execução de reserva conta como atendido; dia sem atualização até as 08:00 reinicia a contagem.
- **SC-003**: Com uma falha provocada na coleta (fonte apontada para um endereço inexistente) e outra na publicação (credencial de leitura inválida), a página continua disponível nas duas situações, exibe a data anterior, e cada falha gera um alerta.
- **SC-004**: 100% das tentativas de registrar alteração com erro de estilo ou teste falhando são bloqueadas, e nenhuma proposta com verificação falhando consegue ser integrada.
- **SC-005**: 100% das tentativas de escrita com o perfil de leitura são recusadas.
- **SC-006**: A restauração da cópia de segurança mais recente de produção num ambiente vazio da mesma versão termina em até 30 minutos, com contagens de registros idênticas às da origem (meta revista quando o volume crescer na HU01).
- **SC-007**: A página tem zero violações na verificação automática de acessibilidade e zero rolagem horizontal em 360 px e em 1440 px.
- **SC-008**: Um ambiente vazio construído só a partir dos scripts versionados tem estrutura idêntica à de produção (comparação sem diferenças).
- **SC-009**: O custo mensal total do projeto continua em até US$ 10 (RNF04).
- **SC-010**: Em 100% das falhas provocadas no SC-003 e de uma execução interrompida à força, o alerta chega ao responsável em até 1 hora.
- **SC-011**: Uma versão publicada com última conferência simulada de 49 horas atrás exibe o aviso de dado envelhecido; com 47 horas, não exibe.

## Assumptions

- O deputado é escolhido pela regra de FR-006 para evitar destaque pessoal; a página é de testes e fica fora dos buscadores até o Marco 1.
- O alerta de falha (FR-029) foi antecipado da F4 para esta feature; ficam na F4 o monitor externo de disponibilidade e o sinal periódico de vida da coleta.
- "Testes relacionados" no registro local significa os testes das partes alteradas; a suíte completa roda na integração contínua.
- A estrutura criada nesta feature cobre só as entidades listadas acima; sessões, presença e estatísticas entram com a HU01.
- Horário de Brasília sem horário de verão (03:00 = 06:00 UTC). Se o horário de verão voltar, o agendamento passa a rodar às 04:00 locais — ainda antes do prazo das 08:00 —, e o ajuste fica no roteiro de operação.
- Um merge em `main` pode gerar o site antes de uma nova estrutura de armazenamento estar aplicada; nesse caso a geração falha, a versão anterior fica no ar (FR-016) e a próxima coleta bem-sucedida republica (risco aceito no plano).
- Limites gratuitos usados (ADR-0002): até 20 mil arquivos publicados por versão (esta feature publica poucos), espaço gratuito de 10 GB no armazenamento de brutos e cópias, minutos de geração gratuitos para repositório público, US$ 5 de uso incluídos no provedor principal. Estourar qualquer um: a etapa correspondente falha ou passa a ser cobrada, o que dispara o alerta (FR-029) ou o alerta de gasto (FR-031).
- **Dependências humanas (⚠️, do responsável; provedores definidos no ADR-0002):**

| Dependência | Pronta quando | Desbloqueia |
|---|---|---|
| Conta e credenciais do provedor de publicação e do armazenamento de brutos e cópias | Credencial restrita criada e cadastrada como segredo | Publicação (FR-014), brutos (FR-011), cópias (FR-024) |
| Credencial do repositório de código só para disparar a publicação, com data de expiração anotada | Cadastrada no ambiente da coleta | Publicação automática após a coleta (FR-014, FR-020a) |
| Armazenamento e coleta agendada criados no provedor principal, perfis de acesso criados pelo roteiro | Coleta manual roda com sucesso no ambiente de produção | US1 e US2 em produção |
| Canal de alertas (bot de mensagens) criado | Mensagem de teste recebida | FR-029 |
| Alerta de gasto e limite rígido configurados | Valores visíveis no painel do provedor | FR-031 |
| Proteção de `main` e `develop` exigindo as verificações | Proposta com verificação falhando não pode ser integrada | FR-022, SC-004 |
