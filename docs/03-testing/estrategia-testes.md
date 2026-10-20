# Estratégia de Testes — Transparência do Congresso

> O objetivo não é cobertura por cobertura — é rede de segurança para refatorar sem medo e provar que a regra de negócio funciona. Aqui, a regra de negócio é uma estatística sobre uma pessoa real: erro vira acusação injusta (R01).

## Pirâmide

- **Unitários (maioria):** regras de cálculo como funções puras, sem banco nem rede. Prioridade:
  1. Taxa de presença (RN03, RN04, RN05): só sessões deliberativas do plenário; denominador = sessões em exercício; ausência justificada não conta como falta.
  2. Contagem de propostas (RN02, RN06): autoria principal × coautoria, sempre por tipo.
  3. Atribuição ao partido atual com sinalização de troca (RN01).
  4. Votos: só votações nominais entram em estatística (RN07); simbólica é exibida sem voto individual.
  5. Resolução de mandato: suplente, afastamento, retorno do titular, troca de legislatura (DA03, R03).
- **Adaptadores (contrato):** cada adaptador (Câmara, Senado) é testado contra **respostas reais gravadas** das APIs oficiais (fixtures versionadas com data da coleta). Prova que o formato da fonte vira o modelo de domínio sem perda — e detecta mudança de formato (R02).
- **Integração (meio):** ETL + banco real efêmero: carga idempotente (rodar duas vezes não duplica), fonte e data de atualização gravadas em todo registro.
- **E2E de UI (poucos):** fluxos das HUs no viewport de celular; toda tela de dado mostra fonte, link e data (RF07, RF08). Complementado pelos roteiros de `quickstart.md` de cada feature.

## Ferramentas

| Camada | Ferramenta |
|---|---|
| Unit / adaptadores / ETL | **Pendente — ADR-0001** (ETL em Python: candidato natural `pytest`) |
| Integração | Pendente — ADR-0001 (banco efêmero em container) |
| Frontend | Pendente — ADR-0001 |
| E2E UI | Pendente — ADR-0001 |

## Cobertura mínima (gate no CI)

| Camada | Mínimo |
|---|---|
| Funções de cálculo de estatística | Pendente — proposta: 100% de linhas e ramos |
| Geral | Pendente |

## Regras

1. Nenhum teste mascarado: proibido skip, `.only`, assert removido, expectativa afrouxada.
2. Todo bug corrigido ganha teste que falha antes do fix.
3. Comportamento crítico tem pelo menos um teste pelo caminho real de dados (mock só na borda de rede).
4. Toda ação de UI tem teste de interação → efeito, não só de estado.
5. Não remover teste existente sem justificativa explícita no PR.
6. Critério de sucesso checável: "deputado com 35 presenças em 40 sessões em exercício → 87,5%", não "cálculo correto".
7. Teste de cálculo usa **casos nomeados** que espelham a metodologia publicada — a página de metodologia e os testes contam a mesma história.

## Fixtures

- Factories para cada entidade do domínio (Parlamentar, Mandato, Partido, Sessão, Presença, Votação, Voto, Proposição, Autoria).
- Cenários prontos: titular + suplente no mesmo período; troca de partido no meio da legislatura; licença; sessão não deliberativa; votação simbólica.
- Respostas gravadas das APIs oficiais, com data da coleta, para os testes de adaptador.
- Banco de teste: container efêmero por execução; nunca banco compartilhado.
