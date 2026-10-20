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
4. Guardar as respostas brutas sanitizadas cujo hash mudou (R2 `fiscaldogov-brutos`).
5. Gravar parlamentar, identificadores, mandato, períodos e filiações numa **única transação**; `COMMIT`.
6. `pg_dump` → R2 `fiscaldogov-backup/diario/` (e `semanal/` aos domingos); baixar de volta e conferir com `pg_restore --list` (FR-024).
7. Disparar a publicação (`workflow_dispatch` de `publicar.yml`, com `execucao_id`).
8. Atualizar `execucao_etl` com status, contagens e eventuais pendências.
9. Se o status for `falha` ou `com_pendencias`, enviar alerta (FR-029) com tipo e `execucao_id`; falha no envio só é registrada no log.

| Falha em | Status | Dados | Publicação |
|---|---|---|---|
| 2, 3, 5 ou vigia | `falha` | nada gravado (rollback) | não disparada |
| 4 | `com_pendencias` | gravados | disparada |
| 6 (envio ou conferência) | `com_pendencias` | gravados | disparada |
| 7 | `com_pendencias` | gravados | não ocorre (fica para o próximo sucesso ou merge em `main`) |

## Códigos de saída

| Código | Significado |
|---|---|
| 0 | `sucesso`, `com_pendencias` ou `dispensada` |
| 1 | `falha` |
| 2 | Configuração inválida (variável ausente); nada é executado |
| 3 | Coleta manual recusada: já há uma em andamento |

## Variáveis de ambiente

Ver `ambientes-e-segredos.md`.
