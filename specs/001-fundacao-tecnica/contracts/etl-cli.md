# Contrato — linha de comando do ETL

Ponto de entrada: `python -m etl <comando>` (pacote em `etl/src/etl/`).

## Comandos

| Comando | Uso | Comportamento |
|---|---|---|
| `coletar` | Cron das 03:00 e acionamento manual | Executa a coleta completa da F2. `--gatilho agendada\|manual` (padrão: `manual`). Se houver `em_andamento` iniciada há menos de 60 min, não começa: mensagem "já há uma coleta em andamento" e código 3. Se houver uma iniciada há mais de 60 min, registra-a como `falha` ("interrompida") e alerta antes de seguir. |
| `reserva` | Cron das 05:00 | Se já houve `sucesso` ou `com_pendencias` no dia (horário de Brasília), registra `dispensada` e sai. Senão, fecha qualquer `em_andamento` com mais de 60 min como `falha` ("interrompida") e executa `coletar --gatilho reserva`. |
| `verificar-config` | Diagnóstico | Confere variáveis obrigatórias e conectividade (banco, R2, API da Câmara) sem gravar nada. |

O cron do Railway roda `python -m etl agendado`, que decide pelo horário UTC: 06h → `coletar --gatilho agendada`, 08h → `reserva`. Assim há um único serviço com a agenda `0 6,8 * * *`.

## Etapas de `coletar` (em ordem)

1. Inserir `execucao_etl` (`em_andamento`) e armar o vigia de 60 min.
2. Coletar a lista de deputados em exercício e escolher o selecionado (FR-006). Lista vazia ou com menos de 500 → `falha` (FR-007b).
3. Coletar o histórico do selecionado e de todos os parlamentares já armazenados.
4. Guardar as respostas brutas sanitizadas cujo hash mudou (R2 `fiscaldogov-brutos`) e registrar cada uma em `coleta_bruta` numa transação própria, que não é desfeita se a etapa 5 falhar.
5. Gravar parlamentar, identificadores, mandato, períodos e filiações numa **única transação**; `COMMIT`.
6. `pg_dump` → R2 `fiscaldogov-backup/diario/` (e `semanal/` aos domingos); baixar de volta e conferir com `pg_restore --list` (FR-024).
7. Atualizar `execucao_etl` com status, contagens e eventuais pendências. Vem **antes** do disparo: o build lê a data e o `execucao_id` da última execução bem-sucedida, que tem que ser esta (FR-002, FR-028). Ordem trocada em 2026-11-01, achado do review da T087.
8. Disparar a publicação (`workflow_dispatch` de `publicar.yml`, com `execucao_id`). Se falhar, a pendência é acrescentada à execução já finalizada, que passa a `com_pendencias`.
9. Se o status for `falha` ou `com_pendencias`, enviar alerta (FR-029) com tipo e `execucao_id`; credencial recusada aparece nomeada (FR-020a); falha no envio só é registrada no log.

O vigia cobre as etapas 2 a 6. Se estourar **antes** do COMMIT da etapa 5, nada é gravado e a execução é `falha`. Se estourar **depois** (no backup), os dados já estão gravados: a execução é `com_pendencias` com a pendência do vigia, e a publicação fica para a próxima execução bem-sucedida.

Falha antes de a execução existir (banco fora do ar, senha recusada) não grava linha em `execucao_etl`, mas gera alerta "coleta não começou" e sai com código 1.

| Falha em | Status | Dados | Publicação |
|---|---|---|---|
| 2, 3, 5, ou vigia antes do COMMIT | `falha` | nada gravado (rollback) | não disparada |
| 4 | `com_pendencias` | gravados | disparada |
| 6 (envio ou conferência) | `com_pendencias` | gravados | disparada |
| vigia depois do COMMIT | `com_pendencias` | gravados | não disparada (fica para o próximo sucesso) |
| 8 | `com_pendencias` | gravados | não ocorre (fica para o próximo sucesso ou merge em `main`) |

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | `sucesso`, `com_pendencias` ou `dispensada` |
| 1 | `falha` |
| 2 | Configuração inválida (variável ausente); nada é executado |
| 3 | Coleta manual recusada: já há uma em andamento |

## Variáveis de ambiente

Ver `ambientes-e-segredos.md`.
