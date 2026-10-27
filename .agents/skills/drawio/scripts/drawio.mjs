#!/usr/bin/env node
// Start, stop, or check the drawio diagram server. Works on Linux and native Windows.
//   node drawio.mjs start [--dir D] [--host H] [--url-host N] [--port 8740] [--idle-minutes 240]
//   node drawio.mjs stop
//   node drawio.mjs status
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const SERVER = path.join(HERE, "server.mjs");

function parseArgs(argv) {
  const [cmd, ...rest] = argv;
  const opts = {};
  for (let i = 0; i < rest.length; i += 2) opts[rest[i].replace(/^--/, "")] = rest[i + 1];
  return { cmd, opts };
}

const readState = (file) => {
  try {
    return JSON.parse(fs.readFileSync(file, "utf8"));
  } catch {
    return null;
  }
};

const alive = (pid) => {
  try {
    process.kill(pid, 0);
    return true;
  } catch (err) {
    return err.code === "EPERM";
  }
};

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// Returns the pid the server on host:port reports, or null when nothing drawio answers.
async function serverPid(port, host) {
  const target = host === "0.0.0.0" || host === "::" ? "127.0.0.1" : host;
  try {
    const res = await fetch(
      `http://${target.includes(":") ? `[${target}]` : target}:${port}/api/health`,
      {
        signal: AbortSignal.timeout(1000),
      },
    );
    if (!res.ok) return null;
    const body = await res.json();
    return Number.isInteger(body.pid) ? body.pid : null;
  } catch {
    return null;
  }
}

// Kill only a server we can confirm is ours: a recorded pid can be reused by
// any process after a crash or reboot.
async function stop(stateFile, { quiet = false } = {}) {
  const state = readState(stateFile);
  fs.rmSync(stateFile, { force: true });
  const confirmed = state?.pid && (await serverPid(state.port, state.host)) === state.pid;
  if (!confirmed) {
    if (!quiet) console.log("not running");
    return;
  }
  try {
    process.kill(state.pid);
  } catch {}
  for (let i = 0; i < 30 && alive(state.pid); i++) await sleep(100);
  if (!quiet) console.log("stopped");
}

async function status(stateFile) {
  const state = readState(stateFile);
  if (state?.pid && (await serverPid(state.port, state.host)) === state.pid) {
    console.log(`running ${state.url} ${state.dir}`);
    return;
  }
  if (state?.pid && alive(state.pid)) {
    console.log(
      `not responding: pid ${state.pid} is alive but ${state.url} does not answer as that server; state kept`,
    );
    return;
  }
  fs.rmSync(stateFile, { force: true });
  console.log("not running");
}

async function start(stateFile, opts) {
  await stop(stateFile, { quiet: true });

  const dir = path.resolve(opts.dir ?? process.cwd());
  const host = opts.host ?? "127.0.0.1";
  const port = Number(opts.port ?? 8740);
  const idle = String(opts["idle-minutes"] ?? 240);
  const urlHost =
    opts["url-host"] ?? (host === "127.0.0.1" || host === "0.0.0.0" ? "localhost" : host);
  const url = `http://${urlHost}:${port}/`;
  const logFile = `${stateFile.replace(/\.json$/, "")}.log`;

  fs.mkdirSync(dir, { recursive: true });
  const log = fs.openSync(logFile, "w");
  const child = spawn(
    process.execPath,
    [SERVER, "--dir", dir, "--host", host, "--port", String(port), "--idle-minutes", idle],
    { detached: true, stdio: ["ignore", log, log], windowsHide: true },
  );
  child.unref();
  fs.closeSync(log);

  for (let i = 0; i < 50; i++) {
    await sleep(100);
    if (child.exitCode !== null || !alive(child.pid)) break;
    if ((await serverPid(port, host)) === child.pid) {
      const state = { pid: child.pid, host, port, dir, url, started: new Date().toISOString() };
      fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
      console.log(`url  ${url}`);
      console.log(`dir  ${dir}`);
      return;
    }
  }

  try {
    process.kill(child.pid);
  } catch {}
  const tail = fs.existsSync(logFile)
    ? fs.readFileSync(logFile, "utf8").trim().split("\n").slice(-5).join("\n")
    : "";
  console.error(`drawio server failed to start on ${host}:${port}`);
  if (tail) console.error(tail);
  process.exitCode = 1;
}

const { cmd, opts } = parseArgs(process.argv.slice(2));
const stateFile = opts["state-file"] ?? path.join(os.homedir(), ".drawio-server.json");

if (cmd === "start") await start(stateFile, opts);
else if (cmd === "stop") await stop(stateFile);
else if (cmd === "status") await status(stateFile);
else {
  console.error(
    "usage: node drawio.mjs start|stop|status [--dir D] [--host H] [--url-host N] [--port P] [--idle-minutes M]",
  );
  process.exitCode = 2;
}
