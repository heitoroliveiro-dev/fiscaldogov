import { AvisoDesatualizado } from "@/components/aviso-desatualizado";
import { formatarConferencia } from "@/lib/formatar-data";

// Todo dado exibido tem fonte oficial, link para o registro original e data da
// última conferência (princípio I, RF07, RF08).
export function FonteOficial({ idCamara, conferidoEm }: { idCamara: string; conferidoEm: Date }) {
  const datetime = conferidoEm.toISOString();
  return (
    <aside
      data-testid="fonte"
      className="flex flex-col gap-1 lg:max-w-sm lg:items-end lg:text-right"
    >
      <p>Fonte: Câmara dos Deputados</p>
      <a
        href={`https://www.camara.leg.br/deputados/${idCamara}`}
        target="_blank"
        rel="noopener"
        aria-describedby="aviso-nova-aba"
        className="inline-flex min-h-11 items-center font-medium text-brand-text underline underline-offset-4 lg:min-h-0"
      >
        Ver registro na Câmara dos Deputados
      </a>
      <span id="aviso-nova-aba" className="sr-only">
        Abre em nova aba
      </span>
      <p className="text-muted-foreground">
        <time dateTime={datetime} data-testid="conferido-em">
          {formatarConferencia(conferidoEm)}
        </time>
      </p>
      <AvisoDesatualizado conferidoEm={datetime} />
    </aside>
  );
}
