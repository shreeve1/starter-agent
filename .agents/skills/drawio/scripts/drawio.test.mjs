import { test } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import net from "node:net";
import http from "node:http";
import { execFile, spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import { createServer } from "./server.mjs";

const XML =
  '<mxfile><diagram id="d" name="Page-1"><mxGraphModel><root><mxCell id="0"/><mxCell id="1" parent="0"/></root></mxGraphModel></diagram></mxfile>';

function tmpDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), "drawio-test-"));
}

async function serve(t, opts = {}) {
  const dir = opts.dir ?? tmpDir();
  const server = createServer({ dir, ...opts });
  await new Promise((r) => server.listen(0, "127.0.0.1", r));
  t.after(() => server.close());
  const base = `http://127.0.0.1:${server.address().port}`;
  return { dir, base };
}

const put = (base, file, body) =>
  fetch(`${base}/api/file?file=${encodeURIComponent(file)}`, {
    method: "PUT",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });

test("health returns dir", async (t) => {
  const { dir, base } = await serve(t);
  const res = await fetch(`${base}/api/health`);
  assert.equal(res.status, 200);
  const body = await res.json();
  assert.equal(body.ok, true);
  assert.equal(body.dir, path.resolve(dir));
});

test("put then get round-trips xml and mtime", async (t) => {
  const { base } = await serve(t);
  const saved = await put(base, "a.drawio", { xml: XML, baseMtime: null });
  assert.equal(saved.status, 200);
  const { mtime } = await saved.json();
  const got = await (await fetch(`${base}/api/file?file=a.drawio`)).json();
  assert.deepEqual(got, { xml: XML, mtime });
});

test("get missing file returns 404 with null mtime", async (t) => {
  const { base } = await serve(t);
  const res = await fetch(`${base}/api/file?file=nope.drawio`);
  assert.equal(res.status, 404);
  assert.deepEqual(await res.json(), { mtime: null });
});

test("put with stale baseMtime returns 409 and leaves disk unchanged", async (t) => {
  const { dir, base } = await serve(t);
  const first = await (await put(base, "a.drawio", { xml: XML, baseMtime: null })).json();
  fs.writeFileSync(path.join(dir, "a.drawio"), "agent edit");
  const future = new Date(first.mtime + 5000);
  fs.utimesSync(path.join(dir, "a.drawio"), future, future);
  const res = await put(base, "a.drawio", { xml: "browser edit", baseMtime: first.mtime });
  assert.equal(res.status, 409);
  assert.equal((await res.json()).mtime, first.mtime + 5000);
  assert.equal(fs.readFileSync(path.join(dir, "a.drawio"), "utf8"), "agent edit");
});

test("put new file with baseMtime null creates nested folders", async (t) => {
  const { dir, base } = await serve(t);
  const res = await put(base, "plans/sub/x.drawio", { xml: XML, baseMtime: null });
  assert.equal(res.status, 200);
  assert.equal(fs.readFileSync(path.join(dir, "plans/sub/x.drawio"), "utf8"), XML);
});

test("put with baseMtime null on existing file returns 409", async (t) => {
  const { dir, base } = await serve(t);
  fs.writeFileSync(path.join(dir, "a.drawio"), "existing");
  const res = await put(base, "a.drawio", { xml: XML, baseMtime: null });
  assert.equal(res.status, 409);
  assert.equal(fs.readFileSync(path.join(dir, "a.drawio"), "utf8"), "existing");
});

test("rejects traversal and non-drawio names", async (t) => {
  const { base } = await serve(t);
  for (const bad of [
    "../x.drawio",
    "/etc/x.drawio",
    "a/../../x.drawio",
    "a.txt",
    "",
    "C:\\x.drawio",
  ]) {
    const g = await fetch(`${base}/api/file?file=${encodeURIComponent(bad)}`);
    assert.equal(g.status, 400, `GET ${bad}`);
    const p = await put(base, bad, { xml: XML, baseMtime: null });
    assert.equal(p.status, 400, `PUT ${bad}`);
  }
});

test("list is recursive, sorted, and skips dot-dirs and node_modules", async (t) => {
  const { dir, base } = await serve(t);
  for (const f of [
    "b.drawio",
    "plans/a.drawio",
    ".git/x.drawio",
    "node_modules/y.drawio",
    "notes.md",
  ]) {
    fs.mkdirSync(path.dirname(path.join(dir, f)), { recursive: true });
    fs.writeFileSync(path.join(dir, f), XML);
  }
  const { files } = await (await fetch(`${base}/api/list`)).json();
  assert.deepEqual(
    files.map((f) => f.file),
    ["b.drawio", "plans/a.drawio"],
  );
  assert.equal(typeof files[0].mtime, "number");
});

test("index lists files with edit links and a new-diagram form", async (t) => {
  const { dir, base } = await serve(t);
  fs.mkdirSync(path.join(dir, "plans"));
  fs.writeFileSync(path.join(dir, "plans/a & 'b'.drawio"), XML);
  const res = await fetch(`${base}/`);
  assert.equal(res.status, 200);
  assert.match(res.headers.get("content-type"), /text\/html/);
  const html = await res.text();
  assert.ok(html.includes(`href="/edit?file=${encodeURIComponent("plans/a & 'b'.drawio")}"`));
  assert.ok(html.includes("plans/a &amp; &#39;b&#39;.drawio"));
  assert.ok(!html.includes("a & 'b'.drawio"));
  assert.match(html, /<form[^>]*action="\/edit"/);
});

test("edit page embeds diagrams.net and the file name", async (t) => {
  const { base } = await serve(t);
  const res = await fetch(`${base}/edit?file=${encodeURIComponent("plans/x.drawio")}`);
  assert.equal(res.status, 200);
  const html = await res.text();
  assert.ok(html.includes("https://embed.diagrams.net/?embed=1"));
  assert.ok(html.includes("proto=json"));
  assert.ok(html.includes("configure=1"));
  assert.ok(html.includes('"plans/x.drawio"'));
  assert.ok(html.includes("compressXml"));
});

test("edit page sends no referrer to the editor host", async (t) => {
  // embed.diagrams.net returns 403 to referrers on private/NetBird hosts.
  const { base } = await serve(t);
  const html = await (await fetch(`${base}/edit?file=x.drawio`)).text();
  assert.match(html, /<iframe[^>]*referrerpolicy="no-referrer"/);
});

test("edit page appends .drawio to a bare name", async (t) => {
  const { base } = await serve(t);
  const res = await fetch(`${base}/edit?file=notes`, { redirect: "manual" });
  assert.equal(res.status, 302);
  assert.equal(res.headers.get("location"), "/edit?file=notes.drawio");
});

test("edit page rejects invalid file", async (t) => {
  const { base } = await serve(t);
  const res = await fetch(`${base}/edit?file=${encodeURIComponent("../x.drawio")}`);
  assert.equal(res.status, 400);
});

test("stat=1 returns only mtime", async (t) => {
  const { base } = await serve(t);
  const { mtime } = await (await put(base, "a.drawio", { xml: XML, baseMtime: null })).json();
  const res = await fetch(`${base}/api/file?file=a.drawio&stat=1`);
  assert.equal((await res.json()).mtime, mtime);
  const missing = await fetch(`${base}/api/file?file=b.drawio&stat=1`);
  assert.equal((await missing.json()).mtime, null);
});

// --- controller CLI ---------------------------------------------------------

const CLI = fileURLToPath(new URL("./drawio.mjs", import.meta.url));

function cli(args, stateFile) {
  return new Promise((resolve) => {
    execFile(process.execPath, [CLI, ...args, "--state-file", stateFile], (err, stdout, stderr) =>
      resolve({ code: err ? err.code : 0, stdout, stderr }),
    );
  });
}

function freePort() {
  return new Promise((resolve) => {
    const s = net.createServer().listen(0, "127.0.0.1", () => {
      const { port } = s.address();
      s.close(() => resolve(port));
    });
  });
}

function cliFixture(t) {
  const stateFile = path.join(tmpDir(), "state.json");
  t.after(() => cli(["stop"], stateFile));
  return stateFile;
}

const alive = (pid) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
};

test("start then status reports running url", async (t) => {
  const stateFile = cliFixture(t);
  const dir = tmpDir();
  const port = await freePort();
  const started = await cli(["start", "--dir", dir, "--port", String(port)], stateFile);
  assert.equal(started.code, 0, started.stderr);
  assert.match(started.stdout, new RegExp(`http://localhost:${port}/`));
  const state = JSON.parse(fs.readFileSync(stateFile, "utf8"));
  assert.equal(state.dir, path.resolve(dir));
  const status = await cli(["status"], stateFile);
  assert.match(status.stdout, new RegExp(`^running http://localhost:${port}/ `));
  const health = await (await fetch(`http://127.0.0.1:${port}/api/health`)).json();
  assert.equal(health.dir, path.resolve(dir));
});

test("stop then status reports not running", async (t) => {
  const stateFile = cliFixture(t);
  const port = await freePort();
  await cli(["start", "--dir", tmpDir(), "--port", String(port)], stateFile);
  const { pid } = JSON.parse(fs.readFileSync(stateFile, "utf8"));
  const stopped = await cli(["stop"], stateFile);
  assert.match(stopped.stdout, /stopped/);
  assert.equal(fs.existsSync(stateFile), false);
  assert.match((await cli(["status"], stateFile)).stdout, /not running/);
  await new Promise((r) => setTimeout(r, 200));
  assert.equal(alive(pid), false);
});

test("status with stale state file reports not running and removes it", async (t) => {
  const stateFile = cliFixture(t);
  fs.writeFileSync(stateFile, JSON.stringify({ pid: 999999, port: 1, url: "http://localhost:1/" }));
  const status = await cli(["status"], stateFile);
  assert.equal(status.code, 0);
  assert.match(status.stdout, /not running/);
  assert.equal(fs.existsSync(stateFile), false);
  const stopped = await cli(["stop"], stateFile);
  assert.equal(stopped.code, 0);
  assert.match(stopped.stdout, /not running/);
});

test("start on a busy port exits 1 and writes no state", async (t) => {
  const stateFile = cliFixture(t);
  const blocker = net.createServer();
  await new Promise((r) => blocker.listen(0, "127.0.0.1", r));
  t.after(() => blocker.close());
  const res = await cli(
    ["start", "--dir", tmpDir(), "--port", String(blocker.address().port)],
    stateFile,
  );
  assert.equal(res.code, 1);
  assert.match(res.stderr, /EADDRINUSE|in use/);
  assert.equal(fs.existsSync(stateFile), false);
});

test("start twice replaces the first server", async (t) => {
  const stateFile = cliFixture(t);
  const port = await freePort();
  await cli(["start", "--dir", tmpDir(), "--port", String(port)], stateFile);
  const first = JSON.parse(fs.readFileSync(stateFile, "utf8")).pid;
  const dir2 = tmpDir();
  const again = await cli(["start", "--dir", dir2, "--port", String(port)], stateFile);
  assert.equal(again.code, 0, again.stderr);
  const second = JSON.parse(fs.readFileSync(stateFile, "utf8"));
  assert.notEqual(second.pid, first);
  assert.equal(alive(first), false);
  assert.equal(second.dir, path.resolve(dir2));
});

test("start with a host prints that host in the url", async (t) => {
  const stateFile = cliFixture(t);
  const port = await freePort();
  const res = await cli(
    [
      "start",
      "--dir",
      tmpDir(),
      "--host",
      "127.0.0.1",
      "--url-host",
      "example.test",
      "--port",
      String(port),
    ],
    stateFile,
  );
  assert.equal(res.code, 0, res.stderr);
  assert.match(res.stdout, new RegExp(`http://example.test:${port}/`));
});

// --- final-review fixes -------------------------------------------------------

test("health reports the server pid", async (t) => {
  const { base } = await serve(t);
  const health = await (await fetch(`${base}/api/health`)).json();
  assert.equal(health.pid, process.pid);
});

test("start fails when a foreign http server already answers on the port", async (t) => {
  const stateFile = cliFixture(t);
  const foreign = http.createServer((_, res) => res.end("{}"));
  await new Promise((r) => foreign.listen(0, "127.0.0.1", r));
  t.after(() => foreign.close());
  const res = await cli(
    ["start", "--dir", tmpDir(), "--port", String(foreign.address().port)],
    stateFile,
  );
  assert.equal(res.code, 1);
  assert.equal(fs.existsSync(stateFile), false);
});

test("stop never kills an unrelated process named in a stale state file", async (t) => {
  const stateFile = cliFixture(t);
  const victim = spawn(process.execPath, ["-e", "setTimeout(()=>{}, 30000)"]);
  t.after(() => victim.kill());
  const port = await freePort();
  fs.writeFileSync(
    stateFile,
    JSON.stringify({ pid: victim.pid, host: "127.0.0.1", port, url: `http://localhost:${port}/` }),
  );
  const res = await cli(["stop"], stateFile);
  assert.equal(res.code, 0);
  assert.equal(alive(victim.pid), true);
  assert.equal(fs.existsSync(stateFile), false);
});

test("status keeps the state file when the pid is alive but not answering", async (t) => {
  const stateFile = cliFixture(t);
  const victim = spawn(process.execPath, ["-e", "setTimeout(()=>{}, 30000)"]);
  t.after(() => victim.kill());
  const port = await freePort();
  fs.writeFileSync(
    stateFile,
    JSON.stringify({ pid: victim.pid, host: "127.0.0.1", port, url: `http://localhost:${port}/` }),
  );
  const res = await cli(["status"], stateFile);
  assert.match(res.stdout, /not responding/);
  assert.equal(fs.existsSync(stateFile), true);
});

test("edit page escapes a script-breaking file name", async (t) => {
  const { base } = await serve(t);
  const bad = "</script><script>alert(1)</script>.drawio";
  const res = await fetch(`${base}/edit?file=${encodeURIComponent(bad)}`);
  const html = await res.text();
  assert.ok(!html.includes("<script>alert(1)"));
});

test("put compares mtime after the body arrives", async (t) => {
  const { dir, base } = await serve(t);
  const first = await (await put(base, "a.drawio", { xml: XML, baseMtime: null })).json();
  const body = JSON.stringify({ xml: "browser edit", baseMtime: first.mtime });
  const { port } = new URL(base);
  const status = await new Promise((resolve) => {
    const req = http.request(
      {
        host: "127.0.0.1",
        port,
        method: "PUT",
        path: "/api/file?file=a.drawio",
        headers: { "content-length": Buffer.byteLength(body) },
      },
      (res) => resolve(res.statusCode),
    );
    req.write(body.slice(0, 10));
    setTimeout(() => {
      fs.writeFileSync(path.join(dir, "a.drawio"), "agent edit");
      const future = new Date(first.mtime + 5000);
      fs.utimesSync(path.join(dir, "a.drawio"), future, future);
      req.end(body.slice(10));
    }, 100);
  });
  assert.equal(status, 409);
  assert.equal(fs.readFileSync(path.join(dir, "a.drawio"), "utf8"), "agent edit");
});

test("stat=1 and the edit page carry the served dir", async (t) => {
  const { dir, base } = await serve(t);
  const stat = await (await fetch(`${base}/api/file?file=a.drawio&stat=1`)).json();
  assert.equal(stat.dir, path.resolve(dir));
  const html = await (await fetch(`${base}/edit?file=a.drawio`)).text();
  assert.ok(html.includes(JSON.stringify(path.resolve(dir)).replace(/</g, "\\u003c")));
});

test("idle timeout calls onIdle", async (t) => {
  let idle = false;
  await serve(t, { idleMs: 200, onIdle: () => (idle = true) });
  await new Promise((r) => setTimeout(r, 400));
  assert.equal(idle, true);
});
