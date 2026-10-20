## O quê e por quê

<!-- O que muda e o motivo. Feature SDD: link para specs/NNN/spec.md e plan.md. Pendência: cite o item do ROADMAP. Base: develop (feature/bugfix/chore) ou main (release/hotfix). -->

## Como testar

<!-- Passos para validar localmente. Feature SDD: "roteiros N–M do quickstart.md". -->

## Evidência

<!-- Output de teste (com contagem), comando + retorno, screenshot. Não basta afirmar que funciona. -->

## Checklist (Definition of Done)

- [ ] Testes automatizados passando (nenhum skip/assert removido)
- [ ] Lint sem erros
- [ ] Nenhum segredo hardcoded
- [ ] Validação de entrada revisada nos pontos novos (schema/DTO + auth)
- [ ] Invariantes do domínio intactos, com teste: fonte oficial + link + data em todo dado exibido; denominador = período em exercício; nenhum rótulo ideológico
- [ ] Mudança em regra de cálculo refletida na página de metodologia
- [ ] Doc atualizada (ADR/README/runbook/CHANGELOG/contrato) quando aplicável
- [ ] Review por subagente contra o plan.md (feature SDD) — achados e correções listados abaixo
- [ ] Nada fora do escopo desta PR foi alterado

## Escopo

- [ ] Feature não trivial — passou pelo fluxo SDD completo
- [ ] Mudança trivial (bug ~1 arquivo / CRUD simples) — SDD dispensado propositalmente

## Achados de review / decisões tomadas durante a implementação

<!-- O que o analyze/review encontrou e o que foi feito. Decisões que mudaram o plano (e onde foram registradas). -->

## Gitflow

- [ ] Branch no padrão (`feature/`, `bugfix/`, `chore/` → `develop`; `release/`, `hotfix/` → `main` + `develop`)
- [ ] `release/`/`hotfix/`: CHANGELOG com a versão e data; tag `vX.Y.Z` criada após o merge em `main`
