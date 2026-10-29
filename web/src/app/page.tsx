import type { Metadata } from "next";

import { AlternarTema } from "@/components/alternar-tema";
import { AvisoTestes } from "@/components/aviso-testes";
import { FonteOficial } from "@/components/fonte-oficial";
import { versaoPublicada } from "@/lib/versao";

import { dadosDaPagina } from "./dados-da-pagina";

export async function generateMetadata(): Promise<Metadata> {
  const { execucao } = await dadosDaPagina();
  return { other: { "versao-publicada": versaoPublicada(execucao.id) } };
}

export default async function Pagina() {
  const { parlamentar, execucao } = await dadosDaPagina();
  return (
    // D1/D2: 16 px (text-lg neste design system) e alvos de 44 px abaixo de lg;
    // FR-003: a partir de lg, fonte ao lado do nome e no máximo 1200 px
    <main className="mx-auto flex w-full max-w-[1200px] flex-col gap-6 px-4 py-6 text-lg lg:gap-10 lg:px-8 lg:py-10 lg:text-base">
      <div className="flex items-start justify-between gap-3">
        <AvisoTestes />
        <AlternarTema />
      </div>
      <section className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <h1 className="text-3xl font-semibold lg:text-4xl">{parlamentar.nome}</h1>
          <p data-testid="partido-uf" className="mt-2 text-muted-foreground">
            {parlamentar.siglaPartido ?? "Sem partido"} · {parlamentar.uf}
          </p>
        </div>
        <FonteOficial idCamara={parlamentar.idCamara} conferidoEm={execucao.terminadaEm} />
      </section>
    </main>
  );
}
