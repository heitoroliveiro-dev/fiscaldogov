// Etapa 1 do pipeline: sementes (tokens/theme.config.json) -> primitivos DTCG.
// Gera escalas de 12 passos em OKLCH para os modos dark e light, com gamut mapping para sRGB.
// Saída: tokens/primitives/color.{dark,light}.tokens.json (formato W3C DTCG 2025.10)

import { readFileSync, writeFileSync } from "node:fs";
import { gamutMap, oklchToHex, round } from "./lib/color.mjs";

const config = JSON.parse(readFileSync(new URL("../tokens/theme.config.json", import.meta.url)));
const MODES = ["dark", "light"];
const SOLID_HOVER_DELTA = { dark: 0.03, light: -0.05 };

function buildScale({ hue, chroma, solid }, mode) {
  const lightness = config.lightness[mode];
  const curve = config.chromaCurve[mode];
  const steps = {};

  for (let i = 0; i < 12; i++) {
    let l = lightness[i];
    if (i === 8) l = solid;
    if (i === 9) l = solid + SOLID_HOVER_DELTA[mode];
    const [L, C, H] = gamutMap([l, chroma * curve[i], hue]);
    const components = [round(L), round(C), round(H, 2)];
    steps[String(i + 1)] = {
      $value: { colorSpace: "oklch", components, alpha: 1, hex: oklchToHex(components) },
    };
  }
  return steps;
}

for (const mode of MODES) {
  const scales = {
    gray: buildScale(
      { ...config.neutral, solid: config.neutralSolidLightness[mode] },
      mode,
    ),
    brand: buildScale({ ...config.brand, solid: config.brand.solidLightness }, mode),
  };
  for (const [name, s] of Object.entries(config.status)) {
    scales[name] = buildScale({ ...s, solid: s.solidLightness }, mode);
  }

  const doc = {
    $description: `Primitivos de cor (modo ${mode}). ARQUIVO GERADO por scripts/generate-scales.mjs — edite tokens/theme.config.json.`,
    color: {
      $type: "color",
      ...scales,
      white: { $value: { colorSpace: "oklch", components: [1, 0, 0], alpha: 1, hex: "#ffffff" } },
      black: { $value: { colorSpace: "oklch", components: [0, 0, 0], alpha: 1, hex: "#000000" } },
    },
  };

  const file = new URL(`../tokens/primitives/color.${mode}.tokens.json`, import.meta.url);
  writeFileSync(file, JSON.stringify(doc, null, 2) + "\n");
  console.log(`✓ tokens/primitives/color.${mode}.tokens.json`);
}
