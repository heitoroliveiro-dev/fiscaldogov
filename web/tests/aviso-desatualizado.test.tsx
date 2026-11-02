// @vitest-environment jsdom
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AvisoDesatualizado, estaDesatualizado } from "@/components/aviso-desatualizado";

const AGORA = new Date("2026-10-28T12:00:00Z");
const HORA = 60 * 60 * 1000;
const MENSAGEM = "Atenção: os dados podem estar desatualizados.";

function horasAtras(horas: number): string {
  return new Date(AGORA.getTime() - horas * HORA).toISOString();
}

// FR-002a, SC-011: o aviso é calculado no navegador, porque a página estática
// pode ficar no ar dias depois do build se a coleta parar.
describe("AvisoDesatualizado", () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ["Date"] });
    vi.setSystemTime(AGORA);
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("aparece com conferência de 49 h atrás", async () => {
    render(<AvisoDesatualizado conferidoEm={horasAtras(49)} />);

    const aviso = await screen.findByRole("alert");
    expect(aviso.textContent).toBe(MENSAGEM);
    expect(aviso.dataset.testid).toBe("aviso-desatualizado");
  });

  it("não aparece com conferência de 47 h atrás", () => {
    render(<AvisoDesatualizado conferidoEm={horasAtras(47)} />);

    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("vale só depois de passar de 48 h", () => {
    expect(estaDesatualizado(new Date(horasAtras(48)), AGORA)).toBe(false);
    expect(estaDesatualizado(new Date(AGORA.getTime() - 48 * HORA - 1), AGORA)).toBe(true);
  });
});
