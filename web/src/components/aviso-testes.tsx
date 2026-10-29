// Linguagem simples: deixa claro que a página ainda é um esqueleto (spec 001).
export function AvisoTestes() {
  return (
    <p
      role="status"
      className="rounded-md border border-warning-border bg-warning-subtle px-4 py-3 text-warning-text"
    >
      Versão de testes — os dados ainda não estão completos.
    </p>
  );
}
