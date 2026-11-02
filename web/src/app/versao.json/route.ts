import { COMMIT } from "@/lib/versao";

import { dadosDaPagina } from "../dados-da-pagina";

// FR-028: gerado no build da exportação estática, como out/versao.json.
export const dynamic = "force-static";

export async function GET() {
  const { execucao } = await dadosDaPagina();
  return Response.json({ execucao_id: execucao.id, commit: COMMIT });
}
