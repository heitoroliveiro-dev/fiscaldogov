// Serve a exportação estática (out/) para o E2E, sem dependências.
// Só para teste local e CI: em produção quem serve é a Cloudflare (ADR-0002).
import { readFile, stat } from "node:fs/promises";
import { createServer } from "node:http";
import { extname, join, resolve, sep } from "node:path";

const raiz = resolve(process.argv[2] ?? "out");
const porta = Number(process.env.PORTA ?? 4173);
const tipos = {
  ".html": "text/html; charset=utf-8",
  ".json": "application/json",
  ".js": "text/javascript",
  ".css": "text/css",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
  ".txt": "text/plain; charset=utf-8",
};

async function localizar(caminho) {
  let arquivo = resolve(raiz, `.${caminho}`);
  if (arquivo !== raiz && !arquivo.startsWith(raiz + sep)) return null;
  try {
    if ((await stat(arquivo)).isDirectory()) arquivo = join(arquivo, "index.html");
  } catch {
    if (!extname(arquivo)) arquivo += ".html";
  }
  return arquivo;
}

createServer(async (pedido, resposta) => {
  const arquivo = await localizar(decodeURIComponent(new URL(pedido.url, "http://local").pathname));
  try {
    if (!arquivo) throw new Error("fora da raiz");
    const corpo = await readFile(arquivo);
    resposta.writeHead(200, { "Content-Type": tipos[extname(arquivo)] ?? "application/octet-stream" });
    resposta.end(corpo);
  } catch {
    resposta.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" }).end("não encontrado");
  }
}).listen(porta, "127.0.0.1");
