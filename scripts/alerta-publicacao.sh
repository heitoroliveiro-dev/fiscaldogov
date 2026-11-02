#!/usr/bin/env bash
# Alerta de falha da publicação no Telegram (FR-029, FR-020a, T073).
# Chamado pelo passo `if: failure()` do publicar.yml. Lê os logs do build e do
# deploy para nomear a credencial recusada. Sem ALERTA_TELEGRAM_TOKEN, só
# imprime a mensagem (é assim que se testa localmente). Falha no envio vira só
# aviso no log: nunca muda o resultado do workflow, que já falhou.
set -uo pipefail

logs="${1:?uso: alerta-publicacao.sh <pasta dos logs>}"
link="${LINK_DA_EXECUCAO:-}"
execucao="${EXECUCAO_ID:-}"

causa=""
if grep -qsiE 'password authentication failed|role "site_leitura" does not exist' "$logs/build.log"; then
  causa="falha de autenticação: DATABASE_URL_LEITURA (papel site_leitura)"
elif grep -qsiE 'Authentication error|Invalid API Token|\[code: (10000|9106)\]|status code 401|403 Forbidden' "$logs/deploy.log"; then
  causa="falha de autenticação: CLOUDFLARE_API_TOKEN"
fi

mensagem="fiscaldogov: publicação com falha"
[ -n "$execucao" ] && mensagem+=$'\n'"execução $execucao"
[ -n "$causa" ] && mensagem+=$'\n'"- $causa"
[ -n "$link" ] && mensagem+=$'\n'"$link"

if [ -z "${ALERTA_TELEGRAM_TOKEN:-}" ]; then
  printf '%s\n' "$mensagem"
  exit 0
fi

# o token vai na URL da API: --silent e sem -v, para não aparecer no log
for tentativa in 1 2; do
  if curl --silent --show-error --fail --max-time 15 -o /dev/null \
    "https://api.telegram.org/bot${ALERTA_TELEGRAM_TOKEN}/sendMessage" \
    --data-urlencode "chat_id=${ALERTA_TELEGRAM_CHAT_ID:-}" \
    --data-urlencode "text=${mensagem}" 2>/dev/null; then
    echo "alerta enviado"
    exit 0
  fi
  [ "$tentativa" -eq 1 ] && sleep 5
done
echo "::warning::alerta não enviado (Telegram não respondeu)"
exit 0
