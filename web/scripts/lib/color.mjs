// Conversões de cor sem dependências.
// OKLCH -> OKLab -> sRGB linear -> sRGB (Björn Ottosson, https://bottosson.github.io/posts/oklab/)
// Contraste: fórmula de luminância relativa da WCAG 2.2 (https://www.w3.org/TR/WCAG22/#dfn-contrast-ratio)

const toRad = (deg) => (deg * Math.PI) / 180;

export function oklchToLinearSrgb([l, c, h]) {
  const a = c * Math.cos(toRad(h));
  const b = c * Math.sin(toRad(h));

  const l_ = l + 0.3963377774 * a + 0.2158037573 * b;
  const m_ = l - 0.1055613458 * a - 0.0638541728 * b;
  const s_ = l - 0.0894841775 * a - 1.291485548 * b;

  const L = l_ ** 3;
  const M = m_ ** 3;
  const S = s_ ** 3;

  return [
    4.0767416621 * L - 3.3077115913 * M + 0.2309699292 * S,
    -1.2684380046 * L + 2.6097574011 * M - 0.3413193965 * S,
    -0.0041960863 * L - 0.7034186147 * M + 1.707614701 * S,
  ];
}

const encode = (x) => (x <= 0.0031308 ? 12.92 * x : 1.055 * x ** (1 / 2.4) - 0.055);

export function inSrgbGamut(oklch, eps = 1e-6) {
  return oklchToLinearSrgb(oklch).every((v) => v >= -eps && v <= 1 + eps);
}

/** Reduz o croma (mantendo L e H) até a cor caber no gamut sRGB. */
export function gamutMap([l, c, h]) {
  if (inSrgbGamut([l, c, h])) return [l, c, h];
  let lo = 0;
  let hi = c;
  for (let i = 0; i < 24; i++) {
    const mid = (lo + hi) / 2;
    if (inSrgbGamut([l, mid, h])) lo = mid;
    else hi = mid;
  }
  return [l, lo, h];
}

export function oklchToHex(oklch) {
  const rgb = oklchToLinearSrgb(oklch).map((v) => {
    const s = encode(Math.min(1, Math.max(0, v)));
    return Math.round(s * 255);
  });
  return "#" + rgb.map((v) => v.toString(16).padStart(2, "0")).join("");
}

/** Luminância relativa WCAG a partir de OKLCH (usa sRGB linear diretamente). */
export function luminance(oklch) {
  const [r, g, b] = oklchToLinearSrgb(oklch).map((v) => Math.min(1, Math.max(0, v)));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

export function contrastRatio(a, b) {
  const la = luminance(a);
  const lb = luminance(b);
  const [hi, lo] = la > lb ? [la, lb] : [lb, la];
  return (hi + 0.05) / (lo + 0.05);
}

export const round = (n, d = 4) => Math.round(n * 10 ** d) / 10 ** d;

/** Formata no padrão CSS Color 4: oklch(L C H) */
export function toCssOklch([l, c, h], alpha = 1) {
  const body = `${round(l * 100, 2)}% ${round(c, 4)} ${round(h, 2)}`;
  return alpha < 1 ? `oklch(${body} / ${round(alpha * 100, 1)}%)` : `oklch(${body})`;
}
