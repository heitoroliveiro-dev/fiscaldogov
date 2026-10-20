# Guia de Documentação — Transparência do Congresso

> Documentação não é tarefa do "fim do projeto" — é parte de terminar cada coisa. Este guia responde: **o quê** documentar, **onde**, e **quando**. A regra-mãe: documente a decisão e o porquê, não o óbvio do código.

---

## 1. Princípio: documente o "porquê", o código já diz o "o quê"

- O código mostra **o que** acontece. Um bom nome de função e variável já documenta isso — por isso código limpo é a primeira forma de documentação.
- A documentação escrita existe pro **porquê** e pro **contexto** que o código não consegue expressar: por que essa decisão, que alternativa foi descartada, que armadilha evitar.
- **Comentário que repete o código é ruído.** `// incrementa i` não ajuda ninguém. `// só sessões deliberativas do plenário entram no denominador (ver contexto §7, RN05)` ajuda.

Teste antes de escrever qualquer doc: *"isso ajuda alguém (inclusive eu daqui a 6 meses) a entender algo que o código não mostra?"* Se não, não escreva.

---

## 2. As camadas de documentação (cada uma tem seu lugar)

| Camada | Onde vive | Responde | Quando escrever |
|---|---|---|---|
| **Norte / produto** | `docs/00-discovery/` | O que é, pra quem, por quê | Fase 0 (em andamento). Revisa se o produto mudar |
| **Decisões** | `docs/01-architecture/adr/` | Por que decidimos assim | No momento da decisão, nunca depois |
| **Modelo de dados** | `docs/01-architecture/modelagem-dados.md` | Como o dado se estrutura | Quando o schema estabiliza; atualiza a cada mudança de schema |
| **Segurança / testes / obs.** | `docs/02` a `04` | Regras e estratégias | Preenche conforme decide; revisa por fase |
| **Runbooks** | `docs/05-runbooks/` | Como operar (backup, deploy) | Antes de precisar em produção |
| **Design** | `docs/06-design/` | Regras de UI/UX | Antes de construir tela |
| **Histórico** | `CHANGELOG.md` | O que mudou e quando | A cada merge relevante |
| **Código** | docstrings / comentários | Porquês locais e contratos | Junto com o código, no mesmo commit |
| **README** | raiz | Como rodar o projeto | Cedo; mantém sempre refletindo o estado atual |

---

## 3. ADR — o coração da documentação de arquitetura

**Quando nasce um ADR:** toda vez que você decide algo com mais de um caminho possível e custo de reverter. Exemplos típicos neste projeto: stack, banco, frequência e orquestração do ETL, modelo de domínio e adaptadores por casa, hospedagem.

**Regra prática:** se no futuro alguém (ou você) puder perguntar *"por que raios isso foi feito assim?"* — precisa de ADR agora.

Formato (template em `docs/01-architecture/adr/adr-template.md`): contexto → decisão → alternativas consideradas → consequências. **A parte que mais importa é "alternativas"** — é ela que prova que houve escolha consciente, não acaso. Um ADR sem alternativas registradas quase sempre esconde uma decisão não pensada.

**Nunca reescreva um ADR antigo.** Se a decisão mudou, crie um novo que marca o antigo como "substituído por ADR-XXXX". O histórico de por que você mudou de ideia é valioso.

---

## 4. Documentação no código (o nível mais próximo)

- **Nome > comentário.** Antes de comentar, pergunte se um nome melhor de função/variável tornaria o comentário desnecessário. Quase sempre torna.
- **Docstring em serviço/função de regra de negócio não óbvia:** o que faz, por que existe, o que assume, o que retorna nos casos de borda. Não em getter trivial.
- **Comente a armadilha, não a mecânica:** "não trocar a ordem — o mandato precisa ser resolvido antes de contar a sessão, senão suplente entra no denominador errado" vale ouro. "// salva no banco" não vale nada.
- **Contrato de API:** endpoints do backend documentados (ex.: OpenAPI/Swagger — decisão de quando adotar vira tarefa, não precisa ADR). API bem documentada é o que permite o frontend (e você no futuro) consumir sem adivinhar.
- **Referência cruzada:** quando o código implementa um requisito, cite (`// RN04`, `// RF07`). Liga o código à intenção.

---

## 5. Quando documentar (o gatilho, para não acumular dívida)

Documentar "depois" = nunca. Os gatilhos:

- **Tomou uma decisão de arquitetura** → ADR **antes** de implementar (o ato de escrever clareia a decisão).
- **Terminou uma feature** → CHANGELOG no mesmo commit; atualiza modelagem se mexeu no schema.
- **Escreveu regra de negócio não óbvia** → docstring/comentário no mesmo commit do código.
- **Mudou como se roda/opera algo** → atualiza README/runbook no mesmo PR.
- **Virou de fase** → atualiza a "Fase atual" no CLAUDE.md.

Regra única que resume tudo: **documentação faz parte do Definition of Done** (`CLAUDE.md` → Definition of Done). Tarefa sem doc atualizada não está "pronta", está "quase".

---

## 6. Como usar a IA para documentar (sem ela inventar)

A IA é ótima pra **rascunhar e formatar** doc; ruim pra **inventar o porquê** (ela não sabe sua intenção real). Padrão de uso:

- **Bom:** "documente esta função descrevendo parâmetros, retorno e casos de borda a partir do código." (ela lê o código, descreve o que existe)
- **Bom:** "formate estas minhas notas de decisão no template de ADR." (você dá o conteúdo, ela estrutura)
- **Perigoso:** "escreva o ADR dessa decisão." (ela vai inventar contexto e alternativas que talvez não sejam os seus)
- **Regra:** o **porquê** sai da sua cabeça. A IA estrutura, formata, completa lacunas óbvias. Você revisa cada porquê — se está escrito algo que você não decidiu, corte.

**Verificação:** leia toda doc gerada por IA antes de commitar, com a mesma régua do código — se afirma algo que você não decidiu ou não é verdade, é ficção, não documentação.

---

## 7. O mínimo viável de documentação (não caia no excesso)

Anti-overengineering vale pra doc também. **Não documente:**
- Código óbvio (nome bom já basta)
- Coisa que muda toda semana (vira doc desatualizada, pior que nenhuma)
- Processo que você faz uma vez só (não é runbook)

**Sempre documente:**
- Decisão de arquitetura (ADR) — inegociável
- Regra de negócio não óbvia (comentário/docstring)
- Como rodar e operar o projeto (README/runbook)
- O que mudou (CHANGELOG)

Doc desatualizada é pior que doc ausente, porque engana. Se você não vai manter, não escreva — prefira menos doc, sempre verdadeira.
