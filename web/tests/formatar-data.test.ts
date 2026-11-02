import { describe, expect, it } from "vitest";

import { formatarConferencia } from "@/lib/formatar-data";

// FR-002: a data da conferência é sempre mostrada no horário de Brasília,
// qualquer que seja o fuso da máquina que gera o site.
describe("formatarConferencia", () => {
  it("formata em America/Sao_Paulo", () => {
    expect(formatarConferencia(new Date("2026-10-28T06:00:00Z"))).toBe(
      "Conferido na fonte oficial em 28/10/2026 às 03:00 (horário de Brasília)",
    );
  });

  it("volta para o dia anterior quando o horário UTC ainda é madrugada", () => {
    expect(formatarConferencia(new Date("2026-10-28T01:30:00Z"))).toBe(
      "Conferido na fonte oficial em 27/10/2026 às 22:30 (horário de Brasília)",
    );
  });

  it("mostra meia-noite como 00, nunca 24", () => {
    expect(formatarConferencia(new Date("2026-03-01T03:05:00Z"))).toBe(
      "Conferido na fonte oficial em 01/03/2026 às 00:05 (horário de Brasília)",
    );
  });
});
