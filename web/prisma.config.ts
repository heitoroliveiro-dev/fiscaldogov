import "dotenv/config";
import { defineConfig } from "prisma/config";

// A URL do dono só é exigida pelos comandos de migration. O `env()` do Prisma 7
// lança erro com a variável ausente, o que quebraria o `prisma generate` do
// build do site (roda sem ela); por isso a leitura direta de `process.env`.
export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: { path: "prisma/migrations" },
  datasource: { url: process.env.DATABASE_URL_DONO },
});
