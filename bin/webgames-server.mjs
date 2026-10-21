// Tiny dependency-free static server for the WebGames production build.
// - Serves webgames/dist on localhost:5310 (127.0.0.1 and ::1 only).
// - SPA fallback: extension-less GET/HEAD paths return index.html (deep routes work).
// - Stubs the app's same-origin analytics endpoints (/api/record-view, /api/record-completion)
//   with {"success":true} so nothing 404s and no Cloudflare/D1 backend is needed.
//   Each analytics POST is logged to stdout as one JSON line ({"event":"view"|"completion",...}),
//   which a harness can use as a server-side "task actually completed" signal.
// - Fails fast (exit 1) if the port is taken (strictPort semantics).
import { createServer } from "node:http";
import { createReadStream, statSync } from "node:fs";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const PORT = Number(process.env.WEBGAMES_PORT || 5310);
const ROOT = resolve(
  process.env.WEBGAMES_DIST ||
    join(fileURLToPath(new URL(".", import.meta.url)), "..", "webgames", "dist")
);
const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".ico": "image/x-icon",
  ".wasm": "application/wasm",
  ".txt": "text/plain; charset=utf-8",
  ".woff2": "font/woff2",
};

try {
  statSync(join(ROOT, "index.html"));
} catch {
  console.error(`[webgames] ${ROOT}/index.html not found - run bin/build-webgames.sh first`);
  process.exit(1);
}

function fileAt(p) {
  try {
    const st = statSync(p);
    return st.isFile() ? st : null;
  } catch {
    return null;
  }
}

function send(res, status, body, type = "text/plain; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(body);
}

function handler(req, res) {
  const url = new URL(req.url, "http://localhost");
  let pathname;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    return send(res, 400, "bad request");
  }

  if (pathname.startsWith("/api/")) {
    let body = "";
    req.on("data", (c) => {
      if (body.length < 65536) body += c;
    });
    req.on("end", () => {
      let data = null;
      try {
        data = JSON.parse(body);
      } catch {
        /* ignore */
      }
      const event = pathname.endsWith("record-completion")
        ? "completion"
        : pathname.endsWith("record-view")
          ? "view"
          : pathname;
      console.log(JSON.stringify({ ts: new Date().toISOString(), event, taskId: data?.taskId ?? null, url: data?.url ?? null }));
      send(res, 200, JSON.stringify({ success: true }), "application/json");
    });
    return;
  }

  if (req.method !== "GET" && req.method !== "HEAD") return send(res, 405, "method not allowed");

  const target = normalize(join(ROOT, pathname));
  if (!target.startsWith(ROOT)) return send(res, 403, "forbidden");

  let file = target;
  let st = fileAt(file);
  if (!st && pathname.endsWith("/")) {
    file = join(target, "index.html");
    st = fileAt(file);
  }
  if (!st) {
    if (extname(pathname)) return send(res, 404, "not found");
    file = join(ROOT, "index.html"); // SPA fallback
    st = fileAt(file);
  }
  res.writeHead(200, {
    "Content-Type": TYPES[extname(file).toLowerCase()] || "application/octet-stream",
    "Content-Length": st.size,
    "Cache-Control": "no-store",
  });
  if (req.method === "HEAD") return res.end();
  createReadStream(file).pipe(res);
}

const servers = [];
function listen(host, required) {
  const s = createServer(handler);
  s.on("error", (err) => {
    if (required) {
      console.error(`[webgames] cannot listen on ${host}:${PORT}: ${err.code || err.message}`);
      process.exit(1);
    }
    console.error(`[webgames] skipping ${host}:${PORT}: ${err.code || err.message}`);
  });
  s.listen(PORT, host, () => console.error(`[webgames] serving ${ROOT} on http://${host.includes(":") ? `[${host}]` : host}:${PORT}`));
  servers.push(s);
}
listen("127.0.0.1", true);
listen("::1", false);

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    for (const s of servers) s.close();
    process.exit(0);
  });
}
