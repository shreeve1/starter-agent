import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { editorPage, indexPage } from "./pages.mjs";

const SKIP_DIRS = new Set(["node_modules"]);

function resolveFile(dir, file) {
  if (typeof file !== "string" || !file.endsWith(".drawio")) return null;
  if (path.isAbsolute(file) || path.win32.isAbsolute(file)) return null;
  if (file.split(/[\\/]/).includes("..")) return null;
  const full = path.resolve(dir, file);
  return full.startsWith(dir + path.sep) ? full : null;
}

function mtimeOf(full) {
  try {
    return Math.round(fs.statSync(full).mtimeMs);
  } catch {
    return null;
  }
}

function listDiagrams(dir) {
  const out = [];
  const walk = (abs, rel) => {
    let entries;
    try {
      entries = fs.readdirSync(abs, { withFileTypes: true });
    } catch {
      return;
    }
    for (const e of entries) {
      const relPath = rel ? `${rel}/${e.name}` : e.name;
      if (e.isDirectory()) {
        if (!e.name.startsWith(".") && !SKIP_DIRS.has(e.name))
          walk(path.join(abs, e.name), relPath);
      } else if (e.isFile() && e.name.endsWith(".drawio")) {
        out.push({ file: relPath, mtime: mtimeOf(path.join(abs, e.name)) });
      }
    }
  };
  walk(dir, "");
  return out.sort((a, b) => (a.file < b.file ? -1 : a.file > b.file ? 1 : 0));
}

function send(res, status, body, type = "application/json") {
  const data = type === "application/json" ? JSON.stringify(body) : body;
  res.writeHead(status, { "content-type": `${type}; charset=utf-8`, "cache-control": "no-store" });
  res.end(data);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    req.on("data", (c) => chunks.push(c));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
    req.on("error", reject);
  });
}

async function handleFile(req, res, dir, url) {
  const full = resolveFile(dir, url.searchParams.get("file"));
  if (!full) return send(res, 400, { error: "invalid file" });

  if (req.method === "GET") {
    const diskMtime = mtimeOf(full);
    if (url.searchParams.get("stat") === "1") return send(res, 200, { mtime: diskMtime, dir });
    if (diskMtime === null) return send(res, 404, { mtime: null });
    return send(res, 200, { xml: fs.readFileSync(full, "utf8"), mtime: diskMtime });
  }

  if (req.method === "PUT") {
    let body;
    try {
      body = JSON.parse(await readBody(req));
    } catch {
      return send(res, 400, { error: "invalid json" });
    }
    if (typeof body.xml !== "string") return send(res, 400, { error: "xml required" });
    // Compare only once the body is in: the agent may write the file while a slow upload is in flight.
    const diskMtime = mtimeOf(full);
    if (diskMtime !== (body.baseMtime ?? null)) return send(res, 409, { mtime: diskMtime });
    fs.mkdirSync(path.dirname(full), { recursive: true });
    const tmp = `${full}.${process.pid}.tmp`;
    fs.writeFileSync(tmp, body.xml);
    fs.renameSync(tmp, full);
    return send(res, 200, { mtime: mtimeOf(full) });
  }

  return send(res, 405, { error: "method not allowed" });
}

function handleEdit(res, dir, url) {
  let file = (url.searchParams.get("file") ?? "").trim().replaceAll("\\", "/");
  if (file && !file.endsWith(".drawio")) {
    res.writeHead(302, { location: `/edit?file=${encodeURIComponent(`${file}.drawio`)}` });
    return res.end();
  }
  if (!resolveFile(dir, file)) return send(res, 400, "Invalid diagram path", "text/plain");
  return send(res, 200, editorPage(file, dir), "text/html");
}

export function createServer({ dir, idleMs, onIdle }) {
  const root = path.resolve(dir);
  let idleTimer = null;
  const touch = () => {
    if (!idleMs || !onIdle) return;
    clearTimeout(idleTimer);
    idleTimer = setTimeout(onIdle, idleMs);
    idleTimer.unref();
  };

  const server = http.createServer(async (req, res) => {
    touch();
    const url = new URL(req.url, "http://localhost");
    try {
      if (url.pathname === "/api/health")
        return send(res, 200, { ok: true, dir: root, pid: process.pid });
      if (url.pathname === "/api/list") return send(res, 200, { files: listDiagrams(root) });
      if (url.pathname === "/api/file") return await handleFile(req, res, root, url);
      if (url.pathname === "/" && url.searchParams.has("file")) {
        res.writeHead(302, { location: `/edit${url.search}` });
        return res.end();
      }
      if (url.pathname === "/")
        return send(res, 200, indexPage(root, listDiagrams(root)), "text/html");
      if (url.pathname === "/edit") return handleEdit(res, root, url);
      return send(res, 404, { error: "not found" });
    } catch (err) {
      return send(res, 500, { error: String(err?.message ?? err) });
    }
  });
  server.on("listening", touch);
  server.on("close", () => clearTimeout(idleTimer));
  return server;
}

function parseArgs(argv) {
  const opts = {};
  for (let i = 0; i < argv.length; i += 2) opts[argv[i].replace(/^--/, "")] = argv[i + 1];
  return opts;
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const args = parseArgs(process.argv.slice(2));
  const dir = path.resolve(args.dir ?? process.cwd());
  const host = args.host ?? "127.0.0.1";
  const port = Number(args.port ?? 8740);
  const idleMs = Number(args["idle-minutes"] ?? 240) * 60_000;
  const server = createServer({ dir, idleMs, onIdle: () => process.exit(0) });
  server.on("error", (err) => {
    console.error(`drawio-server-error ${err.message}`);
    process.exit(1);
  });
  server.listen(port, host, () => {
    console.log(`drawio-server-started ${JSON.stringify({ dir, host, port })}`);
  });
}
