#!/usr/bin/env node
/**
 * Serveur d'aperçu local reproduisant le comportement de Vercel :
 *   1. sert le fichiersystem (.vercel/output/static)
 *   2. sinon, passe la requête à l'entrée SSR (.vercel/output/functions/__server.func)
 *
 * Nécessaire parce que `srvx` traite le mode statique et le mode entrée comme
 * exclusifs, et que `vite preview` cherche `dist/server/server.js` — deux chemins
 * qui n'existent pas avec le preset nitro `vercel`.
 *
 * Usage : npm run build && node scripts/preview.mjs
 */
import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize } from "node:path";
import { fileURLToPath } from "node:url";

const OUT = fileURLToPath(new URL("../.vercel/output/", import.meta.url));
const STATIC_DIR = join(OUT, "static");
const ENTRY = join(OUT, "functions/__server.func/index.mjs");
const PORT = Number(process.env.PORT ?? 4180);

const TYPES = {
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".txt": "text/plain; charset=utf-8",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
  ".ico": "image/x-icon",
  ".woff2": "font/woff2",
};

const mod = await import(ENTRY);
const handler = mod.default ?? mod;
const ssrFetch = handler.fetch ?? handler;

async function tryStatic(pathname) {
  const rel = decodeURIComponent(pathname).replace(/^\/+/, "");
  const path = normalize(join(STATIC_DIR, rel));
  if (!path.startsWith(STATIC_DIR)) return null; // pas de traversée de chemin
  try {
    const s = await stat(path);
    if (!s.isFile()) return null;
    const body = await readFile(path);
    return {
      status: 200,
      headers: {
        "Content-Type": TYPES[extname(path)] ?? "application/octet-stream",
        "Content-Length": String(body.length),
      },
      body,
    };
  } catch {
    return null;
  }
}

async function readBody(req) {
  if (req.method === "GET" || req.method === "HEAD") return undefined;
  const chunks = [];
  for await (const c of req) chunks.push(c);
  return chunks.length ? Buffer.concat(chunks) : undefined;
}

const server = createServer(async (req, res) => {
  const url = new URL(req.url ?? "/", `http://localhost:${PORT}`);

  const file = await tryStatic(url.pathname);
  if (file) {
    res.writeHead(file.status, file.headers);
    if (req.method === "HEAD") return res.end();
    return res.end(file.body);
  }

  const body = await readBody(req);
  const headers = new Headers();
  for (const [k, v] of Object.entries(req.headers)) {
    if (typeof v === "string") headers.set(k, v);
    else if (Array.isArray(v)) headers.set(k, v.join(", "));
  }

  let response;
  try {
    response = await ssrFetch(new Request(url.href, { method: req.method, headers, body }));
  } catch (err) {
    res.writeHead(500, { "Content-Type": "text/plain; charset=utf-8" });
    return res.end("Erreur SSR : " + (err?.stack ?? err));
  }

  res.writeHead(response.status, Object.fromEntries(response.headers));
  return res.end(Buffer.from(await response.arrayBuffer()));
});

server.listen(PORT, "127.0.0.1", () => {
  console.log(`Aperçu local (statiques + SSR) -> http://127.0.0.1:${PORT}`);
});
