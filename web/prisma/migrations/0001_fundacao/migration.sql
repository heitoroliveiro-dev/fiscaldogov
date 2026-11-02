-- Editada à mão após `prisma migrate dev --create-only`: extensão, NULLS NOT DISTINCT,
-- invariantes, cargas fixas e permissões (specs/001-fundacao-tecnica/data-model.md).
-- Os papéis etl_escrita e site_leitura precisam existir antes: em produção pelo runbook
-- docs/05-runbooks/banco-papeis.md; localmente e no CI por scripts/dev-banco-papeis.sql.

-- Exclusão de sobreposição com igualdade em coluna inteira (invariante 2)
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- CreateEnum
CREATE TYPE "sistema_identificador" AS ENUM ('camara_v2', 'camara_v2_partido');

-- CreateEnum
CREATE TYPE "condicao_exercicio" AS ENUM ('titular', 'suplente');

-- CreateEnum
CREATE TYPE "status_execucao" AS ENUM ('em_andamento', 'sucesso', 'com_pendencias', 'falha', 'dispensada');

-- CreateEnum
CREATE TYPE "gatilho_execucao" AS ENUM ('agendada', 'reserva', 'manual');

-- CreateTable
CREATE TABLE "casa_legislativa" (
    "id" SMALLSERIAL NOT NULL,
    "sigla" TEXT NOT NULL,
    "nome" TEXT NOT NULL,

    CONSTRAINT "casa_legislativa_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "legislatura" (
    "numero" SMALLINT NOT NULL,
    "inicio" DATE NOT NULL,
    "fim" DATE NOT NULL,

    CONSTRAINT "legislatura_pkey" PRIMARY KEY ("numero")
);

-- CreateTable
CREATE TABLE "partido" (
    "id" SERIAL NOT NULL,
    "sigla" TEXT NOT NULL,
    "nome" TEXT,

    CONSTRAINT "partido_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "parlamentar" (
    "id" SERIAL NOT NULL,
    "nome_parlamentar" TEXT NOT NULL,
    "nome_ordenacao" TEXT NOT NULL,
    "url_foto" TEXT,
    "fonte_url" TEXT NOT NULL,
    "coletado_em" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "parlamentar_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "identificador_externo" (
    "id" SERIAL NOT NULL,
    "parlamentar_id" INTEGER,
    "partido_id" INTEGER,
    "sistema" "sistema_identificador" NOT NULL,
    "valor" TEXT NOT NULL,
    "legislatura_numero" SMALLINT,

    CONSTRAINT "identificador_externo_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "mandato" (
    "id" SERIAL NOT NULL,
    "parlamentar_id" INTEGER NOT NULL,
    "casa_id" SMALLINT NOT NULL,
    "legislatura_numero" SMALLINT NOT NULL,
    "uf" CHAR(2) NOT NULL,

    CONSTRAINT "mandato_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "periodo_exercicio" (
    "id" SERIAL NOT NULL,
    "mandato_id" INTEGER NOT NULL,
    "inicio" TIMESTAMPTZ(6) NOT NULL,
    "fim" TIMESTAMPTZ(6),
    "condicao" "condicao_exercicio" NOT NULL,
    "motivo_inicio" TEXT NOT NULL,
    "motivo_fim" TEXT,
    "fonte_url" TEXT NOT NULL,
    "coletado_em" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "periodo_exercicio_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "filiacao" (
    "id" SERIAL NOT NULL,
    "parlamentar_id" INTEGER NOT NULL,
    "partido_id" INTEGER NOT NULL,
    "inicio" TIMESTAMPTZ(6) NOT NULL,
    "fim" TIMESTAMPTZ(6),
    "fonte_url" TEXT NOT NULL,
    "coletado_em" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "filiacao_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "execucao_etl" (
    "id" SERIAL NOT NULL,
    "iniciada_em" TIMESTAMPTZ(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "terminada_em" TIMESTAMPTZ(6),
    "status" "status_execucao" NOT NULL DEFAULT 'em_andamento',
    "gatilho" "gatilho_execucao" NOT NULL,
    "tentativas" JSONB NOT NULL DEFAULT '[]',
    "contagens" JSONB NOT NULL DEFAULT '{}',
    "erros" JSONB NOT NULL DEFAULT '[]',
    "pendencias" JSONB NOT NULL DEFAULT '[]',
    "versao_codigo" TEXT NOT NULL,

    CONSTRAINT "execucao_etl_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "coleta_bruta" (
    "id" SERIAL NOT NULL,
    "execucao_id" INTEGER NOT NULL,
    "fonte" TEXT NOT NULL,
    "url" TEXT NOT NULL,
    "chave_r2" TEXT NOT NULL,
    "sha256" CHAR(64) NOT NULL,
    "bytes" INTEGER NOT NULL,
    "coletada_em" TIMESTAMPTZ(6) NOT NULL,

    CONSTRAINT "coleta_bruta_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "casa_legislativa_sigla_key" ON "casa_legislativa"("sigla");

-- CreateIndex
CREATE UNIQUE INDEX "identificador_externo_sistema_valor_legislatura_numero_key" ON "identificador_externo"("sistema", "valor", "legislatura_numero") NULLS NOT DISTINCT;

-- CreateIndex
CREATE UNIQUE INDEX "mandato_parlamentar_id_casa_id_legislatura_numero_key" ON "mandato"("parlamentar_id", "casa_id", "legislatura_numero");

-- CreateIndex
CREATE INDEX "coleta_bruta_url_coletada_em_idx" ON "coleta_bruta"("url", "coletada_em");

-- AddForeignKey
ALTER TABLE "identificador_externo" ADD CONSTRAINT "identificador_externo_parlamentar_id_fkey" FOREIGN KEY ("parlamentar_id") REFERENCES "parlamentar"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "identificador_externo" ADD CONSTRAINT "identificador_externo_partido_id_fkey" FOREIGN KEY ("partido_id") REFERENCES "partido"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "identificador_externo" ADD CONSTRAINT "identificador_externo_legislatura_numero_fkey" FOREIGN KEY ("legislatura_numero") REFERENCES "legislatura"("numero") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mandato" ADD CONSTRAINT "mandato_parlamentar_id_fkey" FOREIGN KEY ("parlamentar_id") REFERENCES "parlamentar"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mandato" ADD CONSTRAINT "mandato_casa_id_fkey" FOREIGN KEY ("casa_id") REFERENCES "casa_legislativa"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "mandato" ADD CONSTRAINT "mandato_legislatura_numero_fkey" FOREIGN KEY ("legislatura_numero") REFERENCES "legislatura"("numero") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "periodo_exercicio" ADD CONSTRAINT "periodo_exercicio_mandato_id_fkey" FOREIGN KEY ("mandato_id") REFERENCES "mandato"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "filiacao" ADD CONSTRAINT "filiacao_parlamentar_id_fkey" FOREIGN KEY ("parlamentar_id") REFERENCES "parlamentar"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "filiacao" ADD CONSTRAINT "filiacao_partido_id_fkey" FOREIGN KEY ("partido_id") REFERENCES "partido"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "coleta_bruta" ADD CONSTRAINT "coleta_bruta_execucao_id_fkey" FOREIGN KEY ("execucao_id") REFERENCES "execucao_etl"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- Invariante 1: período termina depois de começar (DA03)
ALTER TABLE "periodo_exercicio" ADD CONSTRAINT "periodo_exercicio_fim_depois_do_inicio"
    CHECK ("fim" IS NULL OR "fim" > "inicio");

-- Invariante 2: períodos do mesmo mandato não se sobrepõem (FR-018); fim nulo = sem fim
ALTER TABLE "periodo_exercicio" ADD CONSTRAINT "periodo_exercicio_sem_sobreposicao"
    EXCLUDE USING gist ("mandato_id" WITH =, tstzrange("inicio", "fim") WITH &&);

-- Invariante 3: no máximo uma filiação aberta por parlamentar (FR-018, RN01)
CREATE UNIQUE INDEX "filiacao_uma_aberta_por_parlamentar"
    ON "filiacao"("parlamentar_id") WHERE "fim" IS NULL;

-- Invariante 4: o identificador aponta para exatamente uma entidade (ADR-0003 §2)
ALTER TABLE "identificador_externo" ADD CONSTRAINT "identificador_externo_uma_entidade"
    CHECK (num_nonnulls("parlamentar_id", "partido_id") = 1);

-- Cargas fixas
INSERT INTO "casa_legislativa" ("sigla", "nome") VALUES ('CD', 'Câmara dos Deputados');
INSERT INTO "legislatura" ("numero", "inicio", "fim") VALUES (57, '2023-02-01', '2027-01-31');

-- Permissões (FR-019, princípio V). Os ALTER DEFAULT PRIVILEGES valem para os objetos
-- que o dono criar nas próximas migrations. _prisma_migrations já existe neste ponto
-- e entra nos GRANT ON ALL: o pg_dump da US5 roda com etl_escrita e precisa lê-la.
GRANT USAGE ON SCHEMA public TO etl_escrita, site_leitura;

GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO etl_escrita;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO etl_escrita;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO etl_escrita;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO etl_escrita;

GRANT SELECT ON ALL TABLES IN SCHEMA public TO site_leitura;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO site_leitura;
