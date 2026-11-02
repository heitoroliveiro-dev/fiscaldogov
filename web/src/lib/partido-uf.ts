// contracts/pagina-publica.md: partido atual e UF. Sem filiação aberta, "Sem partido":
// nunca um partido antigo nem um espaço vazio que pareça erro.
export function partidoEUf(siglaPartido: string | null, uf: string): string {
  return `${siglaPartido ?? "Sem partido"} · ${uf}`;
}
