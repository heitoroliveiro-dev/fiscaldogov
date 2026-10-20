#!/usr/bin/env bash
# Hook UserPromptSubmit do Claude Code: injeta um lembrete curto das regras a cada prompt.
# É reforço, não fonte — a fonte é o CLAUDE.md e a constituição. Mantenha < 10 linhas.
cat << 'MSG'
[LEMBRETE DO PROJETO — Transparência do Congresso]
- Stack (ADR-0001): Next.js 16 + Tailwind v4 + Radix (só lê, Prisma, papel SELECT) · Postgres + Prisma Migrate · ETL Python (SQLAlchemy Core). Estatística só no Python. Site estático na Cloudflare (ADR-0002): nada dinâmico.
- Invariantes: todo dado com fonte oficial + link + data; neutralidade (sem rótulo ideológico); estatística com regra pública + teste; denominador = período em exercício.
- Regras imutáveis: sem segredo commitado; sem SQL concatenado; gitflow — sem commit direto/force push em main/develop.
- Fluxo SDD: specify -> clarify -> plan -> checklist -> tasks -> analyze -> implement. Bug de 1 arquivo / CRUD trivial pode ir direto.
- DoD: testes + lint + sem segredo + validação + doc + review por subagente contra plan.md + EVIDÊNCIA (não afirmação).
MSG
exit 0
