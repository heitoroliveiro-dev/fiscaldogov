import { PrismaPg } from "@prisma/adapter-pg";
import { afterAll, describe, expect, it } from "vitest";

import { PrismaClient, type Prisma } from "@/generated/prisma/client";
import { buscarDadosDaPagina } from "@/lib/dados";

// Contra o Postgres das migrations, com o papel dono (para preparar os dados).
// Cada caso roda numa transação desfeita ao fim. Sem DATABASE_URL_TESTE o
// arquivo é pulado; com ETL_EXIGIR_INTEGRACAO=1 (o CI define), a falta é erro.
const URL_TESTE = process.env.DATABASE_URL_TESTE;
if (!URL_TESTE && process.env.ETL_EXIGIR_INTEGRACAO === "1") {
  throw new Error("DATABASE_URL_TESTE não definida e ETL_EXIGIR_INTEGRACAO=1 proíbe pular");
}

const FONTE = "https://dadosabertos.camara.leg.br/api/v2/deputados/1/historico";
const COLETADO_EM = new Date("2026-10-28T06:00:00Z");
const DESFAZER = Symbol("desfazer");

type Tx = Prisma.TransactionClient;

describe.skipIf(!URL_TESTE)("buscarDadosDaPagina (FR-001, FR-016a)", () => {
  const cliente = new PrismaClient({ adapter: new PrismaPg({ connectionString: URL_TESTE }) });

  afterAll(() => cliente.$disconnect());

  async function emTransacaoDesfeita(caso: (tx: Tx) => Promise<void>): Promise<void> {
    try {
      await cliente.$transaction(async (tx) => {
        await caso(tx);
        throw DESFAZER;
      });
    } catch (erro) {
      if (erro !== DESFAZER) throw erro;
    }
  }

  async function parlamentar(
    tx: Tx,
    dados: { nome: string; idCamara: string; uf: string; sigla?: string; emExercicio?: boolean },
  ) {
    const casa = await tx.casaLegislativa.findUniqueOrThrow({ where: { sigla: "CD" } });
    const partido = dados.sigla ? await tx.partido.create({ data: { sigla: dados.sigla } }) : null;
    const origem = { fonteUrl: FONTE, coletadoEm: COLETADO_EM };
    return tx.parlamentar.create({
      data: {
        nomeParlamentar: dados.nome,
        nomeOrdenacao: dados.nome
          .normalize("NFKD")
          .replace(/\p{Mn}/gu, "")
          .toLowerCase(),
        ...origem,
        identificadores: { create: { sistema: "camara_v2", valor: dados.idCamara } },
        mandatos: {
          create: {
            casaId: casa.id,
            legislaturaNumero: 57,
            uf: dados.uf,
            periodos: {
              create: {
                inicio: new Date("2023-02-01T15:05:00Z"),
                fim: dados.emExercicio === false ? new Date("2024-01-01T00:00:00Z") : null,
                condicao: "titular",
                motivoInicio: "Posse",
                ...origem,
              },
            },
          },
        },
        filiacoes: partido
          ? {
              create: {
                partidoId: partido.id,
                inicio: new Date("2023-02-01T03:00:00Z"),
                ...origem,
              },
            }
          : undefined,
      },
    });
  }

  async function execucao(tx: Tx, status: "sucesso" | "com_pendencias" | "falha", minuto: number) {
    const iniciadaEm = new Date(Date.UTC(2026, 9, 28, 6, minuto));
    return tx.execucaoEtl.create({
      data: {
        status,
        gatilho: "agendada",
        versaoCodigo: "teste",
        iniciadaEm,
        terminadaEm: new Date(iniciadaEm.getTime() + 30_000),
      },
    });
  }

  it("mostra o em exercício com menor nome de ordenação, com partido atual e UF", async () => {
    await emTransacaoDesfeita(async (tx) => {
      await parlamentar(tx, { nome: "Bruno Farias", idCamara: "1", uf: "MG", sigla: "AVANTE" });
      await parlamentar(tx, { nome: "Átila Lira", idCamara: "2", uf: "PI", sigla: "PP" });
      // menor nome, mas fora de exercício
      await parlamentar(tx, {
        nome: "Aaron",
        idCamara: "3",
        uf: "SP",
        sigla: "PL",
        emExercicio: false,
      });
      await execucao(tx, "sucesso", 0);

      const dados = await buscarDadosDaPagina(tx);

      expect(dados.parlamentar).toEqual({
        nome: "Átila Lira",
        idCamara: "2",
        siglaPartido: "PP",
        uf: "PI",
      });
    });
  });

  it("sem filiação aberta, o partido é nulo", async () => {
    await emTransacaoDesfeita(async (tx) => {
      await parlamentar(tx, { nome: "Fulano Sem Partido", idCamara: "4", uf: "RJ" });
      await execucao(tx, "sucesso", 0);

      expect((await buscarDadosDaPagina(tx)).parlamentar.siglaPartido).toBeNull();
    });
  });

  it("a conferência é a da última execução com sucesso ou com pendências", async () => {
    await emTransacaoDesfeita(async (tx) => {
      await parlamentar(tx, { nome: "Fulano", idCamara: "5", uf: "SP", sigla: "PT" });
      await execucao(tx, "sucesso", 0);
      const comPendencias = await execucao(tx, "com_pendencias", 10);
      await execucao(tx, "falha", 20);

      const dados = await buscarDadosDaPagina(tx);

      expect(dados.execucao).toEqual({
        id: comPendencias.id,
        terminadaEm: comPendencias.terminadaEm,
      });
    });
  });

  it("sem deputado em exercício, falha e o build não publica", async () => {
    await emTransacaoDesfeita(async (tx) => {
      await parlamentar(tx, { nome: "Fulano", idCamara: "6", uf: "SP", emExercicio: false });
      await execucao(tx, "sucesso", 0);

      await expect(buscarDadosDaPagina(tx)).rejects.toThrow(/nenhum deputado em exercício/);
    });
  });

  it("sem execução bem-sucedida, falha e o build não publica", async () => {
    await emTransacaoDesfeita(async (tx) => {
      await parlamentar(tx, { nome: "Fulano", idCamara: "7", uf: "SP", sigla: "PT" });
      await execucao(tx, "falha", 0);

      await expect(buscarDadosDaPagina(tx)).rejects.toThrow(/nenhuma execução bem-sucedida/);
    });
  });
});
