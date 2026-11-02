import { cache } from "react";

import { buscarDadosDaPagina } from "@/lib/dados";

// Uma consulta por build, compartilhada entre os metadados e a página.
export const dadosDaPagina = cache(() => buscarDadosDaPagina());
