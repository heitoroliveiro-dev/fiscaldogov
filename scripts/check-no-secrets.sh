#!/usr/bin/env bash
set -euo pipefail

STAGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR)"

if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

FAIL=0

# 1) Bloqueia arquivo .env staged (exceto exemplos explícitos)
while IFS= read -r file; do
  base="$(basename "$file")"
  case "$base" in
    .env|.env.*)
      case "$base" in
        .env.example|.env.sample|*.env.example|*.env.sample) ;;
        *)
          echo "BLOQUEADO: arquivo de ambiente staged: $file"
          FAIL=1
          ;;
      esac
      ;;
  esac
done <<< "$STAGED_FILES"

# 2) Escaneia conteúdo staged por padrões de segredo (chave AWS, private key, tokens comuns, assignment de secret/token/senha)
SECRET_PATTERN='(AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[baprs]-[0-9A-Za-z-]{10,}|gh[pousr]_[A-Za-z0-9]{36}|(api[_-]?key|secret|token|senha|password|passwd)[[:space:]]*[:=][[:space:]]*["'"'"'][^"'"'"']{8,}["'"'"'])'

while IFS= read -r file; do
  [ -f "$file" ] || continue
  hits="$(git show ":$file" 2>/dev/null | grep -EIn "$SECRET_PATTERN" || true)"
  if [ -n "$hits" ]; then
    echo "BLOQUEADO: possível segredo em $file:"
    echo "$hits"
    FAIL=1
  fi
done <<< "$STAGED_FILES"

if [ "$FAIL" -eq 1 ]; then
  echo ""
  echo "Commit bloqueado. Remova o segredo ou tire do stage (git restore --staged <arquivo>) antes de tentar de novo."
  exit 1
fi

exit 0
