# Playbook de Condução — Transparência do Congresso

> Este documento é sobre **como você dirige o projeto**, não sobre código. O objetivo é que você nunca se perca no escopo e nunca deixe a IA "tomar conta" do desenvolvimento. Leia no início de cada sessão de trabalho junto com o `CLAUDE.md`.

---

## 1. Quem decide o quê (a regra que impede a IA de tomar conta)

A IA **executa e propõe**. Você **decide e aprova**. A fronteira é clara:

| A IA pode fazer sozinha | Só VOCÊ decide |
|---|---|
| Escrever código contra um plano aprovado | O que entra no escopo (e o que fica de fora) |
| Sugerir abordagens e trade-offs | Qual abordagem seguir quando há mais de uma |
| Rodar testes, lint, mostrar evidência | Decisões de arquitetura (viram ADR) |
| Refatorar dentro de uma tarefa definida | Trocar stack, lib, padrão estabelecido |
| Apontar bug e propor correção | Aceitar ou não uma mudança de estrutura |
| Gerar boilerplate repetitivo | Priorizar o backlog |

**Sinal de alerta — a IA está tomando conta quando:**
- Ela toma uma decisão de arquitetura sem te apresentar alternativas.
- O escopo da tarefa cresceu no meio ("já que estou aqui, também fiz X") — X que você não pediu.
- Você está aprovando código que não entende. **Se você não entende, não aprova — pergunta até entender.**
- Você não sabe dizer, em uma frase, o que a sessão de hoje deve entregar.

A regra de ouro: **você deve conseguir explicar cada decisão do projeto para outra pessoa.** Se só a IA sabe por que algo foi feito de um jeito, você perdeu o controle daquele pedaço.

---

## 2. As três alturas de visão (para nunca se perder)

Trabalhe sempre sabendo em qual altura você está. Perder-se é confundir as alturas.

### Altura 1 — O Norte (raramente muda)
Uma frase: **"Dar ao eleitor comum, pelo celular, uma forma simples, neutra e verificável de saber como seus deputados e senadores atuam — sempre com o dado oficial a um clique."**
Se uma tarefa não serve a isso, questione por que ela existe. Este é o filtro anti-escopo.

### Altura 2 — A Fase atual (muda a cada semanas)
Onde você está no ciclo do projeto. Só existe UMA fase ativa por vez:
```
[ ] Fase 0 — Discovery (contexto do projeto completo)   ← você está aqui
[ ] Fase 1 — Arquitetura (ADRs, modelagem)
[ ] Fase 2 — Setup (scaffold, hooks, CI)
[ ] Fase 3 — Ciclo de features (SDD por feature)
[ ] Fase 4 — CI/CD e deploy
[ ] Fase 5 — Operação e documentação viva
```
Registre a fase atual no `CLAUDE.md` (seção "Fase atual"). Atualize ao virar.

### Altura 3 — A Tarefa de hoje (muda a cada sessão)
Uma coisa entregável, com começo e fim. Antes de abrir o Claude Code, complete a frase:
> "Hoje eu vou entregar ______ e vou saber que terminei quando ______."
Se você não consegue completar, **não comece a codar** — você ainda está na altura errada (falta plano).

---

## 3. O ritmo de uma sessão de trabalho (loop seguro)

Repita este loop. Ele mantém você no comando:

```
1. DEFINIR  → complete a frase da Altura 3. Uma tarefa, não cinco.
2. PLANEJAR → Claude em plan mode propõe COMO. Você lê e aprova/ajusta.
              (feature não trivial: fluxo SDD. Setup/bug: plan mode direto.)
3. EXECUTAR → Claude implementa contra o plano aprovado.
4. VERIFICAR→ Claude mostra EVIDÊNCIA (teste, comando+retorno). Você revisa.
5. ENTENDER → você consegue explicar o que foi feito? Se não, pergunte.
6. COMMITAR → um commit coeso. Hooks protegem. Mensagem clara.
7. REGISTRAR→ CHANGELOG e, se mudou decisão, ADR. Atualize a fase se virou.
```

**Nunca pule o passo 5.** É ele que impede você de virar passageiro. Código que entra sem você entender é dívida que você não sabe que tem.

---

## 4. Regras de escopo (anti-overengineering, o seu risco #1)

- **Uma tarefa por vez.** Terminou, commitou, então pega a próxima. Não emende cinco tarefas num fôlego só.
- **"Precisamos disso hoje?"** — a pergunta que mata overengineering. Abstração, generalização, "e se um dia" → só se resolve problema real de agora.
- **O que está fora é tão importante quanto o que está dentro.** O contexto do projeto tem a lista "Fora do escopo do MVP" (§4.2). Ela existe pra você poder dizer "isso é v2" sem culpa.
- **Feature nova que não estava no plano** não entra no meio de outra tarefa. Anota no backlog, termina o que está fazendo, decide depois com cabeça fria.

---

## 5. Quando parar e pensar (freios de mão)

Pare a IA e reassuma o volante quando:

- **Vai mexer em estrutura que já funciona.** Exija: qual o impacto? é reversível? tem plano de rollback? (Sua preferência: nunca refatoração grande sem playbook + rollback.)
- **Apareceu uma decisão com mais de um caminho.** Isso é ADR. Não deixa a IA escolher sozinha — ela te apresenta as opções, você decide e registra o porquê.
- **O diff está grande demais pra revisar.** Se você não consegue ler e entender o diff inteiro, ele está grande demais. Peça pra quebrar.
- **Você está com pressa e tentado a aprovar sem ler.** É exatamente aí que o bug entra. Pressa é o momento de ir mais devagar na revisão, não mais rápido.

---

## 6. O mapa do projeto (onde cada coisa vive)

Para nunca procurar "onde estava aquilo":

| Pergunta | Onde responder |
|---|---|
| Qual o norte / o que é o produto? | `docs/00-discovery/contexto-projeto.md` |
| O que construir, em qual ordem? | `docs/ROADMAP.md` |
| Em que fase estou? | `CLAUDE.md` → Rastreamento de fase |
| Por que decidimos X? | `docs/01-architecture/adr/` |
| Quais as regras invioláveis? | `CLAUDE.md` + `.specify/memory/constitution.md` |
| O que já foi feito? | `CHANGELOG.md` |
| Como documento? | `docs/GUIA-DOCUMENTACAO.md` |
| Como conduzo o projeto? | este arquivo |

---

## 7. Checklist de início e fim de sessão

**Ao começar (2 min):**
- [ ] Li a fase atual no CLAUDE.md — sei onde estou
- [ ] Completei a frase da Altura 3 — sei o que entrego hoje
- [ ] A tarefa serve ao Norte? (se não, por que estou fazendo?)

**Ao terminar (2 min):**
- [ ] Entendo tudo que foi feito (passo 5 do loop)
- [ ] CHANGELOG atualizado
- [ ] Decisão nova virou ADR?
- [ ] Fase mudou? Atualizei o CLAUDE.md?
- [ ] Sei qual é a próxima tarefa (mesmo que não comece agora)

---

## 8. Triagem de demanda nova

Toda demanda passa pela árvore de `../sdd-method/06-triagem-e-trilha-rapida.md` antes de qualquer código. O primeiro "sim" decide:

- Muda modelo de dados, contrato, **regra de cálculo de estatística**, permissão? → **SDD** (`feature/NNN-nome`)
- Tem trade-off real, ou o "pronto" não cabe numa frase checável? → **SDD**
- Bug de ~1 arquivo ou UI no padrão existente? → **trilha rápida** (`bugfix/<nome>` ou `feature/<nome>`)
- Dúvida → **SDD**

Neste projeto, qualquer mudança na forma de calcular ou exibir uma estatística sobre uma pessoa real é SDD — mesmo que o diff seja pequeno (R01).
