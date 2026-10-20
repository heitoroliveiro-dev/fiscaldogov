// Etapa 2 do pipeline: tokens DTCG -> CSS + tema Tailwind + relatório de contraste.
//
// Entradas:  tokens/primitives/*.tokens.json, tokens/semantic/*.tokens.json
// Saídas:    src/styles/tokens.css        variáveis CSS (primitivos por modo + semânticos via var())
//            src/styles/theme.css         @theme do Tailwind v4 (gerado a partir dos tokens)
//            tokens/build/tokens.css      CSS puro, para projetos sem Tailwind
//            tokens/build/tokens.json     valores resolvidos por modo (consumido pela documentação)
//            tokens/build/contrast-report.json
//
// Falha (exit 1) se algum par obrigatório não atingir o contraste mínimo da WCAG 2.2.

import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { contrastRatio, toCssOklch, round } from "./lib/color.mjs";

const root = new URL("../", import.meta.url);
const read = (p) => JSON.parse(readFileSync(new URL(p, root)));
const write = (p, s) => {
  mkdirSync(new URL(p.split("/").slice(0, -1).join("/") + "/", root), { recursive: true });
  writeFileSync(new URL(p, root), s);
  console.log(`✓ ${p}`);
};

const HEADER = `/* ARQUIVO GERADO por scripts/build-tokens.mjs — não edite à mão.\n   Fonte da verdade: tokens/*.tokens.json (W3C DTCG 2025.10). Rode \`npm run tokens\`. */\n`;

// ---------------------------------------------------------------------------
// Leitura e achatamento (DTCG: objetos com $value são tokens; os demais são grupos)
// ---------------------------------------------------------------------------

function flatten(node, path = [], inheritedType, out = {}) {
  const type = node.$type ?? inheritedType;
  for (const [key, child] of Object.entries(node)) {
    if (key.startsWith("$") || typeof child !== "object") continue;
    const p = [...path, key];
    if ("$value" in child) {
      out[p.join(".")] = { path: p, type: child.$type ?? type, value: child.$value, description: child.$description };
    } else {
      flatten(child, p, type, out);
    }
  }
  return out;
}

const load = (...files) => Object.assign({}, ...files.map((f) => flatten(read(f))));

const primitives = {
  dark: load("tokens/primitives/color.dark.tokens.json"),
  light: load("tokens/primitives/color.light.tokens.json"),
};
const shared = load(
  "tokens/primitives/typography.tokens.json",
  "tokens/primitives/dimension.tokens.json",
  "tokens/primitives/motion.tokens.json",
);
const semantic = {
  base: load("tokens/semantic/base.tokens.json"),
  dark: load("tokens/semantic/dark.tokens.json"),
  light: load("tokens/semantic/light.tokens.json"),
  high: load("tokens/semantic/contrast-high.tokens.json"),
};

// ---------------------------------------------------------------------------
// Nomes CSS: color.gray.1 -> --gray-1 ; color.background -> --background ; radius.md -> --radius-md
// ---------------------------------------------------------------------------

const cssName = (path) => "--" + (path[0] === "color" ? path.slice(1) : path).join("-");
const isAlias = (v) => typeof v === "string" && /^\{.+\}$/.test(v);
const aliasPath = (v) => v.slice(1, -1);

const dimToCss = (d) => `${d.value}${d.unit}`;
const colorToCss = (c) =>
  c.colorSpace === "oklch"
    ? toCssOklch(c.components, c.alpha ?? 1)
    : `rgb(${c.components.map((x) => round(x * 255, 0)).join(" ")}${(c.alpha ?? 1) < 1 ? ` / ${round(c.alpha * 100, 1)}%` : ""})`;
const shadowToCss = (v) =>
  [v]
    .flat()
    .map((s) =>
      [s.inset ? "inset" : "", dimToCss(s.offsetX), dimToCss(s.offsetY), dimToCss(s.blur), dimToCss(s.spread), colorToCss(s.color)]
        .filter(Boolean)
        .join(" "),
    )
    .join(", ");

/** Valor CSS de um token. Aliases viram var(--x) para que a troca de modo funcione em cascata. */
function toCss(token) {
  const { type, value } = token;
  if (isAlias(value)) return `var(${cssName(aliasPath(value).split("."))})`;
  switch (type) {
    case "color": return colorToCss(value);
    case "dimension": return dimToCss(value);
    case "duration": return `${value.value}${value.unit}`;
    case "cubicBezier": return `cubic-bezier(${value.join(", ")})`;
    case "fontFamily": return [value].flat().map((f) => (/\s/.test(f) && !f.includes("-apple") ? `"${f}"` : f)).join(", ");
    case "fontWeight": case "number": return String(value);
    case "shadow": return shadowToCss(value);
    default: throw new Error(`Tipo sem serializador: ${type} (${token.path.join(".")})`);
  }
}

const block = (selector, tokens, comment) =>
  `${comment ? `/* ${comment} */\n` : ""}${selector} {\n${Object.values(tokens)
    .map((t) => `  ${cssName(t.path)}: ${toCss(t)};`)
    .join("\n")}\n}\n`;

// ---------------------------------------------------------------------------
// 1) src/styles/tokens.css — cores e elevação (dependem de modo)
// ---------------------------------------------------------------------------

// :root e .dark têm a mesma especificidade; como <html class="dark"> também é :root, o bloco
// .dark precisa redeclarar o valor base de cada token que o light sobrescreve.
const darkOverrides = {
  ...Object.fromEntries(Object.keys(semantic.light).filter((k) => semantic.base[k]).map((k) => [k, semantic.base[k]])),
  ...semantic.dark,
};

const tokensCss =
  HEADER +
  "\n" +
  block(":root", primitives.light, "Primitivos — light") +
  "\n" +
  block(".dark", primitives.dark, "Primitivos — dark (padrão do sistema: <html class=\"dark\">)") +
  "\n" +
  block(":root", semantic.base, "Semânticos — compartilhados (aliases resolvem pelo modo ativo)") +
  "\n" +
  block(":root", semantic.light, "Semânticos — sobrescritas light") +
  "\n" +
  block(".dark", darkOverrides, "Semânticos — sobrescritas dark (inclui o valor base de tudo que o light sobrescreve)") +
  "\n" +
  block(":root[data-contrast=\"high\"]", semantic.high, "Alto contraste (data-contrast=\"high\")");

write("src/styles/tokens.css", tokensCss);

// ---------------------------------------------------------------------------
// 2) src/styles/theme.css — @theme do Tailwind v4 gerado a partir dos tokens
// ---------------------------------------------------------------------------

const semanticColorNames = Object.values(semantic.base)
  .filter((t) => t.type === "color")
  .map((t) => t.path.slice(1).join("-"));
const scaleNames = [...new Set(Object.values(primitives.dark).map((t) => t.path[1]))].filter((n) => !["white", "black"].includes(n));

const byGroup = (group) => Object.values(shared).filter((t) => t.path[0] === group);
const textStyles = Object.values(shared).filter((t) => t.type === "typography");

const themeCss = `${HEADER}
/* Cores: o tema padrão do Tailwind é removido. Use apenas tokens semânticos (bg-background,
   text-muted-foreground…) ou, em casos excepcionais, a escala primitiva (bg-gray-3, text-brand-11). */
@theme inline {
  --color-*: initial;
  --color-white: var(--white);
  --color-black: var(--black);
  --color-transparent: transparent;
  --color-current: currentColor;

${semanticColorNames.map((n) => `  --color-${n}: var(--${n});`).join("\n")}

${scaleNames.map((s) => Array.from({ length: 12 }, (_, i) => `  --color-${s}-${i + 1}: var(--${s}-${i + 1});`).join("\n")).join("\n\n")}

  /* Elevação: nomes do Tailwind/shadcn apontam para os tokens de elevação (mudam por modo) */
  --shadow-raised: var(--elevation-raised);
  --shadow-overlay: var(--elevation-overlay);
  --shadow-modal: var(--elevation-modal);
  --shadow-xs: var(--elevation-raised);
  --shadow-sm: var(--elevation-raised);
  --shadow-md: var(--elevation-overlay);
  --shadow-lg: var(--elevation-overlay);
  --shadow-xl: var(--elevation-modal);
  --shadow-2xl: var(--elevation-modal);
}

@theme static {
  /* Tipografia */
  --font-sans: var(--font-face-sans, Inter), ${toCss(shared["font.family.sans"]).replace(/^Inter, /, "")};
  --font-mono: var(--font-face-mono, "Geist Mono"), ${toCss(shared["font.family.mono"]).replace(/^"Geist Mono", /, "")};
${byGroup("font").filter((t) => t.type === "fontWeight").map((t) => `  --font-weight-${t.path.at(-1)}: ${toCss(t)};`).join("\n")}

${textStyles
  .map((t) => {
    const n = t.path.at(-1);
    const v = t.value;
    return [
      `  --text-${n}: ${dimToCss(v.fontSize)};`,
      `  --text-${n}--line-height: ${v.lineHeight};`,
      `  --text-${n}--letter-spacing: ${dimToCss(v.letterSpacing)};`,
      `  --text-${n}--font-weight: ${v.fontWeight};`,
    ].join("\n");
  })
  .join("\n")}

  /* Raio */
  --radius: ${toCss(shared["radius.md"])};
${byGroup("radius").map((t) => `  --radius-${t.path.at(-1)}: ${toCss(t)};`).join("\n")}

  /* Movimento — use com duration-(--duration-fast) ease-standard */
${byGroup("duration").map((t) => `  --duration-${t.path.at(-1)}: ${toCss(t)};`).join("\n")}
${byGroup("ease").map((t) => `  --ease-${t.path.at(-1)}: ${toCss(t)};`).join("\n")}
}
`;

write("src/styles/theme.css", themeCss);

// ---------------------------------------------------------------------------
// 3) tokens/build/tokens.css — CSS puro para qualquer stack (sem Tailwind)
// ---------------------------------------------------------------------------

const plainShared = Object.fromEntries(Object.entries(shared).filter(([, t]) => t.type !== "typography"));
write(
  "tokens/build/tokens.css",
  tokensCss + "\n" + block(":root", plainShared, "Tipografia, espaçamento, raio e movimento"),
);

// ---------------------------------------------------------------------------
// 4) Resolução por modo + verificação de contraste WCAG 2.2
// ---------------------------------------------------------------------------

function resolveMode(mode, contrast) {
  const sem = { ...semantic.base, ...semantic[mode], ...(contrast === "high" ? semantic.high : {}) };
  const prim = primitives[mode];
  const resolve = (v, seen = new Set()) => {
    if (!isAlias(v)) return v;
    const p = aliasPath(v);
    if (seen.has(p)) throw new Error(`Referência circular: ${p}`);
    seen.add(p);
    const t = prim[p] ?? sem[p];
    if (!t) throw new Error(`Alias não encontrado: {${p}}`);
    return resolve(t.value, seen);
  };
  const out = {};
  for (const t of Object.values(sem)) if (t.type === "color") out[t.path.slice(1).join("-")] = resolve(t.value);
  return out;
}

// [primeiro plano, fundo, mínimo, critério]
const TEXT = 4.5; // WCAG 1.4.3 (AA)
const UI = 3; // WCAG 1.4.11 / 2.4.13
const pairs = [
  ...["background", "card", "popover"].flatMap((bg) => [
    ["foreground", bg, TEXT, "1.4.3"],
    ["muted-foreground", bg, TEXT, "1.4.3"],
    ["brand-text", bg, TEXT, "1.4.3"],
    ["danger-text", bg, TEXT, "1.4.3"],
    ["success-text", bg, TEXT, "1.4.3"],
    ["warning-text", bg, TEXT, "1.4.3"],
    ["info-text", bg, TEXT, "1.4.3"],
    ["ring", bg, UI, "2.4.13"],
  ]),
  ["subtle-foreground", "background", TEXT, "1.4.3"],
  ["subtle-foreground", "card", TEXT, "1.4.3"],
  ["muted-foreground", "muted", TEXT, "1.4.3"],
  ["accent-foreground", "accent", TEXT, "1.4.3"],
  ["secondary-foreground", "secondary", TEXT, "1.4.3"],
  ["primary-foreground", "primary", TEXT, "1.4.3"],
  ["primary-foreground", "primary-hover", TEXT, "1.4.3"],
  ["destructive-foreground", "destructive", TEXT, "1.4.3"],
  ["brand-text", "brand-subtle", TEXT, "1.4.3"],
  ["danger-text", "danger-subtle", TEXT, "1.4.3"],
  ["success-text", "success-subtle", TEXT, "1.4.3"],
  ["warning-text", "warning-subtle", TEXT, "1.4.3"],
  ["info-text", "info-subtle", TEXT, "1.4.3"],
  ["sidebar-foreground", "sidebar", TEXT, "1.4.3"],
  ["sidebar-accent-foreground", "sidebar-accent", TEXT, "1.4.3"],
  ["primary", "background", UI, "1.4.11"],
  ["success", "background", UI, "1.4.11"],
  ["info", "background", UI, "1.4.11"],
  ["destructive", "background", UI, "1.4.11"],
];
// Informativo (não reprova no modo padrão; reprova em alto contraste)
const informative = [["input", "background", UI, "1.4.11"], ["input", "card", UI, "1.4.11"], ["border-strong", "background", UI, "1.4.11"]];

const report = { generatedBy: "scripts/build-tokens.mjs", modes: {} };
const resolved = {};
let failures = 0;

for (const mode of ["dark", "light"]) {
  for (const contrast of ["default", "high"]) {
    const key = contrast === "high" ? `${mode}-high` : mode;
    const colors = resolveMode(mode, contrast);
    resolved[key] = Object.fromEntries(
      Object.entries(colors).map(([n, c]) => [n, { css: colorToCss(c), hex: c.hex ?? null }]),
    );
    const rows = [];
    const check = (list, enforce) => {
      for (const [fg, bg, min, sc] of list) {
        const ratio = round(contrastRatio(colors[fg].components, colors[bg].components), 2);
        const pass = ratio >= min;
        rows.push({ fg, bg, ratio, min, criterion: sc, pass, enforced: enforce });
        if (!pass && enforce) {
          failures++;
          console.error(`✗ [${key}] ${fg} sobre ${bg}: ${ratio}:1 (mínimo ${min}:1, WCAG ${sc})`);
        }
      }
    };
    check(pairs, true);
    check(informative, contrast === "high");
    report.modes[key] = rows;
  }
}

write("tokens/build/contrast-report.json", JSON.stringify(report, null, 2) + "\n");
write(
  "tokens/build/tokens.json",
  JSON.stringify(
    {
      colors: resolved,
      scales: Object.fromEntries(
        ["dark", "light"].map((m) => [
          m,
          Object.fromEntries(
            scaleNames.map((s) => [s, Array.from({ length: 12 }, (_, i) => primitives[m][`color.${s}.${i + 1}`].value.hex)]),
          ),
        ]),
      ),
      descriptions: Object.fromEntries(
        Object.values({ ...semantic.base, ...shared })
          .filter((t) => t.description)
          .map((t) => [t.path.join("."), t.description]),
      ),
    },
    null,
    2,
  ) + "\n",
);

if (failures) {
  console.error(`\n${failures} par(es) abaixo do contraste mínimo. Ajuste tokens/theme.config.json ou os aliases semânticos.`);
  process.exit(1);
}
console.log("✓ Contraste WCAG 2.2 AA: todos os pares obrigatórios aprovados.");
