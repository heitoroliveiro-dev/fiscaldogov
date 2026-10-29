# syntax=docker/dockerfile:1
# Imagem do ETL no Railway (research §3, §6; T049).
# Contexto de build: a RAIZ do repositório (dockerfilePath = etl/Dockerfile),
# porque o comando de pré-deploy aplica as migrations de web/prisma/.

# --- CLI do Prisma: só prisma e dotenv, nas versões do web/package-lock.json --
FROM node:24-trixie-slim AS prisma
WORKDIR /prisma
COPY web/package-lock.json ./
RUN versoes="$(node -p "const p = require('./package-lock.json').packages; \
      ['prisma', 'dotenv'].map((n) => n + '@' + p['node_modules/' + n].version).join(' ')")" \
 && npm install --no-save --no-audit --no-fund $versoes

# --- imagem final --------------------------------------------------------------
FROM python:3.14-slim-trixie

# pg_dump/pg_restore na mesma major do servidor (18, T001); o Debian trixie traz a 17
RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates curl \
 && install -d /usr/share/postgresql-common/pgdg \
 && curl -fsSL -o /usr/share/postgresql-common/pgdg/apt.postgresql.org.asc \
      https://www.postgresql.org/media/keys/ACCC4CF8.asc \
 && echo "deb [signed-by=/usr/share/postgresql-common/pgdg/apt.postgresql.org.asc] https://apt.postgresql.org/pub/repos/apt trixie-pgdg main" \
      > /etc/apt/sources.list.d/pgdg.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends postgresql-client-18 \
 && apt-get purge -y curl \
 && apt-get autoremove -y \
 && rm -rf /var/lib/apt/lists/*

COPY --from=node:24-trixie-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=ghcr.io/astral-sh/uv:0.13.4 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    PYTHONUNBUFFERED=1 \
    PATH=/app/etl/.venv/bin:$PATH

WORKDIR /app

# migrations (pré-deploy: cd /app/web && node_modules/.bin/prisma migrate deploy)
COPY --from=prisma /prisma/node_modules web/node_modules
COPY web/prisma web/prisma
COPY web/prisma.config.ts web/

# dependências antes do código, para aproveitar o cache das camadas
COPY etl/pyproject.toml etl/uv.lock etl/.python-version etl/
RUN cd etl && uv sync --frozen --no-dev --no-install-project
COPY etl/src etl/src
RUN cd etl && uv sync --frozen --no-dev

RUN useradd --system --uid 10001 --no-create-home etl
USER etl
WORKDIR /app/etl

# provisório: o agendamento (comando agendado) entra na US2 (T071)
CMD ["python", "-m", "etl", "coletar"]
