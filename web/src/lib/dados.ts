import type { Prisma } from "@/generated/prisma/client";
import { db } from "@/lib/db";

// Lido só no build. Sem deputado em exercício ou sem execução bem-sucedida,
// lança erro: o build falha e a versão anterior continua no ar (FR-016, FR-016a).
const LEGISLATURA = 57;
const CASA = "CD";

export type DadosDaPagina = {
  parlamentar: { nome: string; idCamara: string; siglaPartido: string | null; uf: string };
  execucao: { id: number; terminadaEm: Date };
};

export async function buscarDadosDaPagina(
  cliente: Prisma.TransactionClient = db(),
): Promise<DadosDaPagina> {
  // FR-006: entre os em exercício na 57ª, o de menor nome de ordenação
  const periodo = await cliente.periodoExercicio.findFirst({
    where: { fim: null, mandato: { legislaturaNumero: LEGISLATURA, casa: { sigla: CASA } } },
    orderBy: [{ mandato: { parlamentar: { nomeOrdenacao: "asc" } } }, { id: "asc" }],
    select: {
      mandato: {
        select: {
          uf: true,
          parlamentar: {
            select: {
              nomeParlamentar: true,
              identificadores: { where: { sistema: "camara_v2" }, select: { valor: true } },
              filiacoes: { where: { fim: null }, select: { partido: { select: { sigla: true } } } },
            },
          },
        },
      },
    },
  });
  if (!periodo) {
    throw new Error(`nenhum deputado em exercício na ${LEGISLATURA}ª legislatura no banco`);
  }

  // mesma ordem do ETL (ultima_bem_sucedida): a data exibida é a da versão publicada
  const execucao = await cliente.execucaoEtl.findFirst({
    where: { status: { in: ["sucesso", "com_pendencias"] }, terminadaEm: { not: null } },
    orderBy: [{ iniciadaEm: "desc" }, { id: "desc" }],
    select: { id: true, terminadaEm: true },
  });
  if (!execucao?.terminadaEm) {
    throw new Error("nenhuma execução bem-sucedida da coleta no banco");
  }

  const { parlamentar, uf } = periodo.mandato;
  const [identificador] = parlamentar.identificadores;
  if (!identificador) {
    throw new Error(`parlamentar ${parlamentar.nomeParlamentar} sem identificador da Câmara`);
  }
  return {
    parlamentar: {
      nome: parlamentar.nomeParlamentar,
      idCamara: identificador.valor,
      siglaPartido: parlamentar.filiacoes[0]?.partido.sigla ?? null,
      uf,
    },
    execucao: { id: execucao.id, terminadaEm: execucao.terminadaEm },
  };
}
