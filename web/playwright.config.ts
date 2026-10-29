import { defineConfig } from "@playwright/test";

// E2E contra o out/ já gerado por `npm run build` (com o banco semeado por
// prisma/seed-e2e.sql): testa exatamente o que seria publicado.
const PORTA = 4173;

export default defineConfig({
  testDir: "e2e",
  forbidOnly: !!process.env.CI,
  reporter: process.env.CI ? "github" : "list",
  use: { baseURL: `http://127.0.0.1:${PORTA}`, browserName: "chromium" },
  webServer: {
    command: "node scripts/servir-out.mjs out",
    url: `http://127.0.0.1:${PORTA}/`,
    env: { PORTA: String(PORTA) },
    reuseExistingServer: !process.env.CI,
  },
});
