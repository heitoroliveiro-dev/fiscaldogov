import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";

// contracts/pagina-publica.md, com os dados de prisma/seed-e2e.sql.
const LARGURAS = [360, 1440] as const;
const TEMAS = ["light", "dark"] as const;
const REGRAS_WCAG = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa", "wcag22a", "wcag22aa"];

async function abrir(page: Page, largura: number, tema: (typeof TEMAS)[number]) {
  await page.setViewportSize({ width: largura, height: 900 });
  await page.emulateMedia({ colorScheme: tema });
  await page.goto("/");
}

for (const largura of LARGURAS) {
  for (const tema of TEMAS) {
    test.describe(`${largura}px, tema ${tema}`, () => {
      test.beforeEach(async ({ page }) => abrir(page, largura, tema));

      test("mostra todos os elementos do contrato", async ({ page }) => {
        await expect(page.getByRole("status")).toHaveText(
          "Versão de testes — os dados ainda não estão completos.",
        );
        await expect(page.getByRole("heading", { level: 1 })).toHaveText("Parlamentar de Teste");
        await expect(page.getByTestId("partido-uf")).toHaveText("TESTE · DF");
        await expect(page.getByTestId("fonte")).toContainText("Fonte: Câmara dos Deputados");

        const registro = page.getByRole("link", { name: "Ver registro na Câmara dos Deputados" });
        await expect(registro).toHaveAttribute(
          "href",
          "https://www.camara.leg.br/deputados/999001",
        );
        await expect(registro).toHaveAttribute("target", "_blank");
        await expect(registro).toHaveAttribute("rel", /noopener/);
        await expect(registro).toHaveAccessibleDescription(/nova aba/);

        const conferido = page.getByTestId("conferido-em");
        await expect(conferido).toHaveAttribute("datetime", /^\d{4}-\d{2}-\d{2}T/);
        await expect(conferido).toHaveText(
          /^Conferido na fonte oficial em \d{2}\/\d{2}\/\d{4} às \d{2}:\d{2} \(horário de Brasília\)$/,
        );
        // o seed acabou de rodar: o dado não está velho
        await expect(page.getByTestId("aviso-desatualizado")).toHaveCount(0);
        await expect(page.getByRole("button", { name: "Alternar tema" })).toBeVisible();
      });

      test("não tem rolagem horizontal", async ({ page }) => {
        const excesso = await page.evaluate(
          () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
        );
        expect(excesso).toBeLessThanOrEqual(0);
      });

      test("não tem violações do axe (WCAG 2.2 A/AA)", async ({ page }) => {
        const resultado = await new AxeBuilder({ page }).withTags(REGRAS_WCAG).analyze();
        expect(resultado.violations).toEqual([]);
      });
    });
  }
}

test("segue o tema do sistema e troca pelo botão", async ({ page }) => {
  await abrir(page, 360, "dark");
  await expect(page.locator("html")).toHaveClass(/dark/);

  await page.getByRole("button", { name: "Alternar tema" }).click();

  await expect(page.locator("html")).not.toHaveClass(/dark/);
});

test("abaixo de 1024 px: texto de 16 px e alvos de 44 px (D1, D2)", async ({ page }) => {
  await abrir(page, 360, "light");

  const corpo = await page
    .getByTestId("partido-uf")
    .evaluate((elemento) => parseFloat(getComputedStyle(elemento).fontSize));
  expect(corpo).toBeGreaterThanOrEqual(16);

  for (const alvo of [
    page.getByRole("link", { name: "Ver registro na Câmara dos Deputados" }),
    page.getByRole("button", { name: "Alternar tema" }),
  ]) {
    const caixa = await alvo.boundingBox();
    expect(caixa?.height).toBeGreaterThanOrEqual(44);
    expect(caixa?.width).toBeGreaterThanOrEqual(44);
  }
});

test("fonte ao lado do nome em 1440 px e abaixo dele em 360 px (FR-003)", async ({ page }) => {
  await abrir(page, 1440, "light");
  const nome = (await page.getByRole("heading", { level: 1 }).boundingBox())!;
  const fonte = (await page.getByTestId("fonte").boundingBox())!;
  expect(fonte.x).toBeGreaterThanOrEqual(nome.x + nome.width);
  expect(fonte.y).toBeLessThan(nome.y + nome.height);

  const conteudo = (await page.getByRole("main").boundingBox())!;
  expect(conteudo.width).toBeLessThanOrEqual(1200);

  await abrir(page, 360, "light");
  const nomeCelular = (await page.getByRole("heading", { level: 1 }).boundingBox())!;
  const fonteCelular = (await page.getByTestId("fonte").boundingBox())!;
  expect(fonteCelular.y).toBeGreaterThanOrEqual(nomeCelular.y + nomeCelular.height);
});

test("fora dos buscadores e com a versão publicada identificada (FR-005, FR-028)", async ({
  page,
  request,
}) => {
  await page.goto("/");
  await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex/);
  await expect(page.locator("html")).toHaveAttribute("lang", "pt-BR");

  const versao = await request.get("/versao.json");
  expect(versao.ok()).toBe(true);
  const { execucao_id, commit } = await versao.json();
  expect(execucao_id).toEqual(expect.any(Number));
  expect(commit).toEqual(expect.any(String));
  await expect(page.locator('meta[name="versao-publicada"]')).toHaveAttribute(
    "content",
    `execucao=${execucao_id};commit=${commit}`,
  );
});
