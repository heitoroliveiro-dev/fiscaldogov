import { describe, expect, it } from "vitest";

import { partidoEUf } from "@/lib/partido-uf";

// contracts/pagina-publica.md: partido atual e UF; sem filiação aberta, "Sem partido".
describe("partidoEUf", () => {
  it("mostra a sigla do partido atual e a UF", () => {
    expect(partidoEUf("PDT", "PA")).toBe("PDT · PA");
  });

  it("sem filiação aberta, mostra Sem partido", () => {
    expect(partidoEUf(null, "RJ")).toBe("Sem partido · RJ");
  });
});
