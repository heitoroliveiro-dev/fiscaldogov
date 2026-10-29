// FR-002: a data é sempre a de Brasília, qualquer que seja o fuso da máquina do build.
const FORMATO = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
  hourCycle: "h23",
});

export function formatarConferencia(data: Date): string {
  const partes = Object.fromEntries(
    FORMATO.formatToParts(data).map(({ type, value }) => [type, value]),
  );
  return (
    `Conferido na fonte oficial em ${partes.day}/${partes.month}/${partes.year} ` +
    `às ${partes.hour}:${partes.minute} (horário de Brasília)`
  );
}
