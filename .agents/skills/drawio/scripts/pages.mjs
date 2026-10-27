const EMBED_URL =
  "https://embed.diagrams.net/?embed=1&proto=json&spin=1&configure=1&saveAndExit=0&noExitBtn=1&libraries=1&ui=atlas";

const escapeHtml = (s) =>
  s.replace(
    /[&<>"']/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c],
  );

const STYLE = `
  body { font: 15px/1.5 system-ui, sans-serif; margin: 0; color: #1d1d1f; background: #fafafa; }
  main { max-width: 44rem; margin: 2.5rem auto; padding: 0 1.25rem; }
  h1 { font-size: 1.4rem; margin: 0 0 .25rem; }
  .dir { color: #555; font-family: ui-monospace, monospace; font-size: .85rem; margin: 0 0 1.5rem; word-break: break-all; }
  ul { list-style: none; padding: 0; margin: 0 0 2rem; border-top: 1px solid #ddd; }
  li { border-bottom: 1px solid #ddd; }
  li a { display: flex; justify-content: space-between; gap: 1rem; padding: .6rem .25rem; color: #0b57d0; text-decoration: none; }
  li a:hover, li a:focus-visible { background: #eef3fd; }
  time { color: #555; font-size: .85rem; white-space: nowrap; }
  form { display: flex; gap: .5rem; flex-wrap: wrap; }
  input { flex: 1 1 16rem; padding: .5rem .6rem; font: inherit; border: 1px solid #888; border-radius: 4px; }
  button { padding: .5rem 1rem; font: inherit; border: 0; border-radius: 4px; background: #0b57d0; color: #fff; cursor: pointer; }
  :focus-visible { outline: 2px solid #0b57d0; outline-offset: 2px; }
  .empty { color: #555; }
`;

export function indexPage(dir, files) {
  const items = files.length
    ? `<ul>${files
        .map(
          (f) =>
            `<li><a href="/edit?file=${encodeURIComponent(f.file)}"><span>${escapeHtml(f.file)}</span>` +
            `<time data-ms="${f.mtime}"></time></a></li>`,
        )
        .join("")}</ul>`
    : `<p class="empty">No diagrams here yet.</p>`;
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Diagrams</title><style>${STYLE}</style></head>
<body><main>
<h1>Diagrams</h1>
<p class="dir">${escapeHtml(dir)}</p>
${items}
<form method="get" action="/edit">
  <label for="file" hidden>New diagram name</label>
  <input id="file" name="file" required placeholder="new diagram, e.g. diagrams/bot-flow">
  <button type="submit">New diagram</button>
</form>
</main>
<script>
for (const t of document.querySelectorAll("time[data-ms]")) {
  const d = new Date(Number(t.dataset.ms));
  t.textContent = d.toLocaleString();
  t.dateTime = d.toISOString();
}
</script>
</body></html>`;
}

const scriptJson = (v) => JSON.stringify(v).replace(/</g, "\\u003c");

export function editorPage(file, dir) {
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(file)}</title>
<style>
  html, body { height: 100%; margin: 0; font: 14px/1.4 system-ui, sans-serif; }
  body { display: flex; flex-direction: column; }
  header { display: flex; align-items: center; gap: 1rem; padding: .35rem .75rem; background: #1d1d1f; color: #fff; }
  header a { color: #a8c7fa; }
  header span { font-family: ui-monospace, monospace; }
  #state { margin-left: auto; color: #ccc; }
  .banner { display: none; gap: .75rem; align-items: center; flex-wrap: wrap; padding: .6rem .75rem; background: #fff4cc; color: #3d2e00; border-bottom: 1px solid #c9a400; }
  .banner.show { display: flex; }
  .banner button { padding: .35rem .8rem; font: inherit; border: 1px solid #3d2e00; border-radius: 4px; background: #fff; cursor: pointer; }
  iframe { flex: 1; border: 0; width: 100%; }
  :focus-visible { outline: 2px solid #0b57d0; outline-offset: 2px; }
</style></head>
<body>
<header><a href="/">All diagrams</a><span id="name"></span><span id="state" role="status"></span></header>
<div id="banner" class="banner" role="alert">
  <span>This diagram changed on disk since you opened it. Your edits are still here. Reload loses them; Save as copy keeps both.</span>
  <button id="reload" type="button">Reload</button>
  <button id="copy" type="button">Save as copy</button>
</div>
<div id="moved" class="banner" role="alert">
  <span>The server now serves a different folder, so saving here is switched off. Your edits are still in this tab: use File &gt; Export as &gt; XML to keep them, then open the diagram from the new server.</span>
</div>
<iframe id="editor" title="draw.io editor" referrerpolicy="no-referrer" src="${EMBED_URL}"></iframe>
<script>
const EDITOR_ORIGIN = "https://embed.diagrams.net";
const DIR = ${scriptJson(dir)};
let file = ${scriptJson(file)};
const frame = document.getElementById("editor");
const banner = document.getElementById("banner");
const moved = document.getElementById("moved");
const state = document.getElementById("state");
let mtime = null;
let modified = false;
let currentXml = "";
let conflictMtime = null;
let saving = false;
let locked = false;

const api = (f, q = "") => "/api/file?file=" + encodeURIComponent(f) + q;
const post = (msg) => frame.contentWindow.postMessage(JSON.stringify(msg), EDITOR_ORIGIN);
const setName = () => { document.getElementById("name").textContent = file; document.title = file; };
setName();

async function load() {
  if (locked) return;
  try {
    const res = await fetch(api(file));
    const body = await res.json();
    mtime = body.mtime;
    currentXml = body.xml || "";
    modified = false;
    conflictMtime = null;
    banner.classList.remove("show");
    post({ action: "load", xml: currentXml, autosave: 1, title: file });
    state.textContent = mtime === null ? "New diagram, not saved yet" : "";
  } catch {
    state.textContent = "Server unreachable";
  }
}

async function save(xml) {
  currentXml = xml;
  if (locked) return;
  if (saving) { state.textContent = "Still saving, press Save again in a moment"; return; }
  saving = true;
  try {
    const res = await fetch(api(file), {
      method: "PUT",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ xml, baseMtime: mtime }),
    });
    const body = await res.json();
    if (res.ok) {
      mtime = body.mtime;
      modified = false;
      banner.classList.remove("show");
      post({ action: "status", message: "Saved", modified: false });
      state.textContent = "Saved " + new Date().toLocaleTimeString();
    } else if (res.status === 409) {
      conflictMtime = body.mtime;
      banner.classList.add("show");
    } else {
      state.textContent = "Save failed: " + (body.error || res.status);
    }
  } catch {
    state.textContent = "Save failed: server unreachable. Your edits are still here.";
  } finally {
    saving = false;
  }
}

async function saveCopy() {
  if (locked) return;
  const stem = file.replace(/\\.drawio$/, "");
  for (const suffix of ["-mine", "-mine-" + Date.now()]) {
    const target = stem + suffix + ".drawio";
    try {
      const res = await fetch(api(target), {
        method: "PUT",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ xml: currentXml, baseMtime: null }),
      });
      if (res.ok) {
        file = target;
        mtime = (await res.json()).mtime;
        modified = false;
        conflictMtime = null;
        banner.classList.remove("show");
        history.replaceState(null, "", "/edit?file=" + encodeURIComponent(file));
        setName();
        post({ action: "status", message: "Saved as " + file, modified: false });
        state.textContent = "Saved as copy";
        return;
      }
    } catch {
      break;
    }
  }
  state.textContent = "Could not save a copy";
}

window.addEventListener("message", (e) => {
  if (e.origin !== EDITOR_ORIGIN || e.source !== frame.contentWindow || typeof e.data !== "string") return;
  let msg;
  try { msg = JSON.parse(e.data); } catch { return; }
  if (msg.event === "configure") post({ action: "configure", config: { compressXml: false } });
  else if (msg.event === "init") load();
  else if (msg.event === "autosave") { currentXml = msg.xml; modified = true; state.textContent = "Unsaved changes"; }
  else if (msg.event === "save") save(msg.xml);
});

document.getElementById("reload").addEventListener("click", load);
document.getElementById("copy").addEventListener("click", saveCopy);

setInterval(async () => {
  if (locked || saving) return;
  try {
    const { mtime: disk, dir } = await (await fetch(api(file, "&stat=1"))).json();
    if (dir !== DIR) {
      locked = true;
      banner.classList.remove("show");
      moved.classList.add("show");
      state.textContent = "Saving off";
      return;
    }
    if (disk === mtime || disk === conflictMtime) return;
    if (!modified) load();
    else { conflictMtime = disk; banner.classList.add("show"); }
  } catch {
    state.textContent = "Server unreachable";
  }
}, 2000);
</script>
</body></html>`;
}
