import { PrismaPg } from "@prisma/adapter-pg";

import { PrismaClient } from "@/generated/prisma/client";

// O site só lê o banco, e só no build da exportação estática: nenhuma consulta
// chega ao navegador. O papel site_leitura tem apenas SELECT (FR-019, princípio V).
// Criado na primeira consulta, para que importar este módulo não exija o banco.
let cliente: PrismaClient | undefined;

export function db(): PrismaClient {
  if (!cliente) {
    const url = process.env.DATABASE_URL_LEITURA;
    if (!url) {
      throw new Error(
        "DATABASE_URL_LEITURA não definida: o build do site lê o banco com o papel site_leitura",
      );
    }
    cliente = new PrismaClient({ adapter: new PrismaPg({ connectionString: url }) });
  }
  return cliente;
}
