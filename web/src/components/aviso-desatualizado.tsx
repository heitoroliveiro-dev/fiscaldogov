"use client";

import { useEffect, useState } from "react";

// FR-002a: a página estática pode ficar no ar dias depois do build se a coleta
// parar; por isso a idade do dado é calculada no navegador. Sem script, o aviso
// não aparece e a data da conferência continua visível.
const LIMITE_MS = 48 * 60 * 60 * 1000;

export function estaDesatualizado(conferidoEm: Date, agora: Date): boolean {
  return agora.getTime() - conferidoEm.getTime() > LIMITE_MS;
}

export function AvisoDesatualizado({ conferidoEm }: { conferidoEm: string }) {
  const [desatualizado, setDesatualizado] = useState(false);

  useEffect(() => {
    // só no navegador, depois da hidratação: o HTML do build nunca traz o aviso
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setDesatualizado(estaDesatualizado(new Date(conferidoEm), new Date()));
  }, [conferidoEm]);

  if (!desatualizado) return null;
  return (
    <p role="alert" data-testid="aviso-desatualizado" className="font-medium text-destructive">
      Atenção: os dados podem estar desatualizados.
    </p>
  );
}
