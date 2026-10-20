# Contrato — página pública (esqueleto)

Rota única: `/`. Gerada no build (exportação estática) a partir do banco, com o papel `site_leitura`.

## Dado exibido

O parlamentar com período de exercício aberto (`fim` nulo) na 57ª legislatura, com o menor `nome_ordenacao`. Se nenhum existir, ou não houver execução bem-sucedida, o build **falha** (FR-016a) — nunca se publica uma página sem dado (FR-016 mantém a versão anterior).

## Elementos obrigatórios (verificados nos testes E2E)

| Elemento | Conteúdo | Seletor de teste |
|---|---|---|
| Aviso de testes | "Versão de testes — os dados ainda não estão completos." | `role=status` |
| Nome | `nome_parlamentar` | `role=heading`, nível 1 |
| Partido e UF | "<sigla do partido atual> · <UF>" | `data-testid=partido-uf` |
| Fonte | "Fonte: Câmara dos Deputados" | `data-testid=fonte` |
| Registro original | link para `https://www.camara.leg.br/deputados/{id}`, `rel="noopener"`, abre em nova aba com aviso acessível | `role=link`, nome acessível "Ver registro na Câmara dos Deputados" |
| Conferência | "Conferido na fonte oficial em DD/MM/AAAA às HH:MM (horário de Brasília)" — `terminada_em` da última execução `sucesso` ou `com_pendencias` | `<time datetime=...>`, `data-testid=conferido-em` |
| Dado envelhecido | "Atenção: os dados podem estar desatualizados." Exibido por script no navegador quando `agora − conferido_em > 48 h` (FR-002a); sem script, não aparece e a data continua visível | `role=alert`, `data-testid=aviso-desatualizado` |
| Troca de tema | botão claro/escuro; padrão = preferência do sistema | `role=button`, nome acessível "Alternar tema" |

## Requisitos não funcionais verificados

- `<meta name="robots" content="noindex">` no HTML e `X-Robots-Tag: noindex` no cabeçalho (arquivo `_headers`) — FR-005.
- Sem rolagem horizontal em 360 px e 1440 px, nos dois temas — FR-003.
- Zero violações do axe (regras WCAG 2.2 A/AA) nas quatro combinações — FR-004.
- Corpo de texto ≥ 16 px e alvos de toque ≥ 44 px abaixo de 1024 px (D1, D2).
- `lang="pt-BR"`.
- `<meta name="versao-publicada" content="execucao=<id>;commit=<sha>">` e o mesmo conteúdo em `/versao.json` (FR-028).
