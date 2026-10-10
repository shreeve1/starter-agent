#!/usr/bin/env python3
"""Apply an edition Release to the owner's workspace.

Commands: plan, apply, finish, status, resolve-hold, rollback. Run from the workspace root
(or pass --root). See ../SKILL.md for the rules.
"""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

STATE_REL = ".agents/release-state.json"
SNAP_DIR_REL = ".agents/snapshots"
BACKUP_DIR_REL = ".agents/release-backup"
SCHEMA_PATH = "memory/schema.json"
RELEASE_META = {"MANIFEST.json", "CHANGELOG.md"}
SCHEMA_KEYS = ("client_subjects", "topics", "topic_dirs", "client_dirs")
DEFAULT_TOPIC_DIRS = ["workflows", "decisions"]
CLASSES = {"merge", "seed", "local"}
WINDOWS_DEVICES = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}
WRITING_ACTIONS = {"add", "update", "merge", "conflict", "delete", "schema"}
CLEAN_ACTIONS = {"add", "update", "merge", "delete", "schema"}
# Built, not literal, so this file never looks like a conflicted file to the scan.
OPEN, MID, CLOSE = "<" * 7 + " ", "=" * 7, ">" * 7 + " "
SNAPSHOT_IDENT = {
    "GIT_AUTHOR_NAME": "apply-release",
    "GIT_AUTHOR_EMAIL": "apply-release@localhost",
    "GIT_COMMITTER_NAME": "apply-release",
    "GIT_COMMITTER_EMAIL": "apply-release@localhost",
}


class Refusal(Exception):
    """A rule stops the command; exit 2 with the message."""


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(data):
    return data.replace(b"\r\n", b"\n")


def sha(data):
    return hashlib.sha256(norm(data)).hexdigest()


def is_binary(*blobs):
    return any(b is not None and b"\0" in b[:8192] for b in blobs)


def styled(lf_data, owner):
    """Write LF content using the owner file's existing line-ending style."""
    lf_data = norm(lf_data)
    if owner is not None and b"\r\n" in owner:
        return lf_data.replace(b"\n", b"\r\n")
    return lf_data


def fs_path(root, rel):
    """Map a Release-relative POSIX path to a file under `root`, or refuse.

    Layer one rejects anything that is not a plain POSIX relative path, so a Windows-only spelling
    (backslash, drive letter, alternate data stream, trailing dot or space) never reaches the OS.
    Layer two resolves the real target, following symlinks and junctions in every parent, and requires
    it to stay inside `root`.
    """
    if not isinstance(rel, str) or not rel:
        raise Refusal(f"unsafe path in Release: {rel!r}")
    parts = rel.split("/")
    bad = (rel.startswith("/") or "\\" in rel or ":" in rel or any(ord(c) < 32 for c in rel)
           or any(p in ("", ".", "..") or p != p.rstrip(" .") for p in parts)
           or parts[0].lower() == ".git" or any(p.split(".")[0].upper() in WINDOWS_DEVICES for p in parts))
    if bad:
        raise Refusal(f"unsafe path in Release: {rel!r}")
    base = Path(root).resolve()
    target = Path(root).joinpath(*parts)
    try:
        target.resolve().relative_to(base)
    except ValueError:
        raise Refusal(f"path escapes the workspace: {rel!r}") from None
    return target


def read_opt(path):
    return path.read_bytes() if path.is_file() else None


def git(args, cwd, data=None, env=None, check=True):
    full_env = None
    if env:
        full_env = dict(os.environ)
        full_env.update(env)
    try:
        r = subprocess.run(["git", *args], cwd=cwd, input=data, capture_output=True, env=full_env)
    except FileNotFoundError:
        raise Refusal("git is not installed; install Git for Windows/macOS/Linux and retry")
    if check and r.returncode != 0:
        msg = r.stderr.decode("utf-8", errors="replace").strip()
        raise Refusal(f"git {' '.join(args)} failed: {msg}")
    return r


def is_repo(root):
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True)
    except FileNotFoundError:
        return False
    if r.returncode != 0:
        return False
    return Path(r.stdout.decode("utf-8").strip()).resolve() == Path(root).resolve()


def merge3(base, ours, theirs, release):
    with tempfile.TemporaryDirectory() as d:
        names = []
        for name, data in (("ours", ours), ("base", base), ("theirs", theirs)):
            p = Path(d, name)
            p.write_bytes(norm(data))
            names.append(str(p))
        try:
            r = subprocess.run(
                ["git", "merge-file", "-p", "-L", "owner", "-L", "snapshot", "-L", f"release {release}", *names],
                capture_output=True,
            )
        except FileNotFoundError:
            raise Refusal("git is not installed; it is needed for git merge-file")
    if r.returncode >= 128:
        raise Refusal("git merge-file failed: " + r.stderr.decode("utf-8", errors="replace").strip())
    return r.stdout, r.returncode != 0


# ---- state ---------------------------------------------------------------

def empty_state():
    return {
        "version": 1,
        "edition": None,
        "release": None,
        "snapshots": {},
        "seeds_installed": [],
        "locals_installed": [],
        "holds": [],
        "in_progress": None,
        "history": [],
    }


def load_state(root):
    p = fs_path(root, STATE_REL)
    if not p.is_file():
        return empty_state()
    st = json.loads(p.read_text(encoding="utf-8"))
    base = empty_state()
    base.update(st)
    return base


def save_state(root, st):
    p = fs_path(root, STATE_REL)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + ".tmp")
    tmp.write_bytes((json.dumps(st, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    os.replace(tmp, p)


# ---- pre-apply backup ----------------------------------------------------

def raw_sha(data):
    return None if data is None else hashlib.sha256(data).hexdigest()


def is_tool_path(rel):
    """Paths apply-release owns: never dirty, never committed, never part of a Release."""
    low = rel.lower()
    return (low == STATE_REL or low.startswith(SNAP_DIR_REL + "/") or low.startswith(BACKUP_DIR_REL + "/"))


class Backup:
    """The owner's exact pre-apply bytes of every path an apply changes, in .agents/release-backup/<N>/.

    backup.json: {"release", "from_release", "files": {path: {"existed", "after_sha256"}},
    "state_file_existed", "rolled_back"}. The first copy of a path is never overwritten, so a rerun after an
    interruption keeps the true pre-apply state.
    """

    def __init__(self, root, n):
        self.root = root
        self.n = n
        self.dir = fs_path(root, f"{BACKUP_DIR_REL}/{n}")
        self.meta_path = self.dir / "backup.json"
        self.meta = json.loads(self.meta_path.read_text(encoding="utf-8")) if self.meta_path.is_file() else None

    def copy_path(self, area, rel):
        return fs_path(self.dir / area, rel)

    def start(self, st, fresh):
        """Called before the apply changes anything. `fresh`: no apply of this Release is in progress."""
        if self.meta is not None and fresh and self.meta.get("rolled_back"):
            k = 1
            while (aside := self.dir.with_name(f"{self.n}-rolled-back-{k}")).exists():
                k += 1
            os.replace(self.dir, aside)
            self.meta = None
        if self.meta is None:
            self.meta = {"release": self.n, "from_release": st["release"], "files": {},
                         "state_file_existed": fs_path(self.root, STATE_REL).is_file(), "rolled_back": False}
            self.save()
        self.protect(STATE_REL)

    def save(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        ignore = self.dir.parent / ".gitignore"
        if not ignore.exists():
            ignore.write_bytes(b"# apply-release backups: the owner's safety net, never committed\n*\n")
        tmp = self.meta_path.with_name("backup.json.tmp")
        tmp.write_bytes((json.dumps(self.meta, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        os.replace(tmp, self.meta_path)

    def protect(self, rel):
        """Copy the current bytes of `rel` before its first change; record whether it existed."""
        if self.meta is None or rel in self.meta["files"]:
            return
        src = fs_path(self.root, rel)
        existed = src.is_file()
        if existed:
            dst = self.copy_path("files", rel)
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        self.meta["files"][rel] = {"existed": existed}
        self.save()

    def wrote(self, rel):
        """Record the sha256 of what the apply left at `rel` (null when it deleted the path)."""
        if self.meta is None or rel not in self.meta["files"]:
            return
        self.meta["files"][rel]["after_sha256"] = raw_sha(read_opt(fs_path(self.root, rel)))
        self.save()

    def rescue(self, rel, data):
        """Keep the owner's newer bytes of `rel` before a forced rollback overwrites them.

        Append-only: the first copy keeps the plain name, different bytes get `.1`, `.2`, ... and bytes that are
        already saved are not saved again. A copy is never overwritten, so an earlier rescue (the owner's only
        copy of an earlier edit) survives any number of forced passes."""
        base = self.copy_path("rolled-back", rel)
        base.parent.mkdir(parents=True, exist_ok=True)
        k = 0
        while True:
            dst = base if k == 0 else base.with_name(f"{base.name}.{k}")
            if not dst.exists():
                dst.write_bytes(data)
                return dst
            if dst.read_bytes() == data:
                return dst
            k += 1


# ---- snapshots -----------------------------------------------------------

class GitSnapshot:
    def __init__(self, root, ref):
        self.root = root
        out = git(["ls-tree", "-r", "-z", "--full-tree", ref], root).stdout
        self.blobs = {}
        for item in out.split(b"\0"):
            if item:
                meta, path = item.split(b"\t", 1)
                self.blobs[path.decode("utf-8")] = meta.split()[2].decode()

    def read(self, rel):
        blob = self.blobs.get(rel)
        if blob is None:
            return None
        return git(["cat-file", "blob", blob], self.root).stdout


class FolderSnapshot:
    def __init__(self, path):
        self.path = path

    def read(self, rel):
        return read_opt(fs_path(self.path, rel))


def open_snapshot(root, st):
    if st["release"] is None:
        return None
    snap = st["snapshots"].get(str(st["release"]))
    if snap is None:
        raise Refusal(f"state says Release {st['release']} is applied but has no snapshot entry")
    if snap["store"] == "git":
        if not is_repo(root):
            raise Refusal(f"snapshot {snap['location']} is a git ref but {root} is not a git repo")
        return GitSnapshot(root, snap["location"])
    folder = fs_path(root, snap["location"])
    if not folder.is_dir():
        raise Refusal(f"snapshot folder {snap['location']} is missing")
    return FolderSnapshot(folder)


def snapshot_manifest(snap):
    data = snap.read("MANIFEST.json")
    if data is None:
        raise Refusal("previous snapshot has no MANIFEST.json")
    return json.loads(data.decode("utf-8"))


def store_git_snapshot(root, rdir, manifest, ref):
    paths = sorted(rel_files(rdir))
    shas = git(["hash-object", "-w", "--no-filters", "--stdin-paths"], root,
               data="\n".join(str(fs_path(rdir, p)) for p in paths).encode("utf-8")).stdout.decode().split()
    lines = []
    for p, blob in zip(paths, shas):
        mode = "100755" if manifest["files"].get(p, {}).get("mode") == "755" else "100644"
        lines.append(f"{mode} {blob}\t{p}")
    with tempfile.TemporaryDirectory() as d:
        env = {"GIT_INDEX_FILE": str(Path(d, "index"))}
        git(["update-index", "--add", "--index-info"], root, data=("\n".join(lines) + "\n").encode("utf-8"), env=env)
        tree = git(["write-tree"], root, env=env).stdout.decode().strip()
    commit = git(["commit-tree", tree, "-m", f"Pristine Snapshot of Release {manifest['release']}"],
                 root, env=SNAPSHOT_IDENT).stdout.decode().strip()
    git(["update-ref", ref, commit], root)


def rel_files(top):
    top = Path(top)
    out = []
    for dirpath, dirnames, filenames in os.walk(top):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for f in filenames:
            out.append(Path(dirpath, f).relative_to(top).as_posix())
    return out


# ---- release -------------------------------------------------------------

def load_release(release_dir):
    rdir = Path(release_dir).resolve()
    mpath = rdir / "MANIFEST.json"
    if not mpath.is_file():
        raise Refusal(f"{rdir} has no MANIFEST.json; is this a Release folder?")
    man = json.loads(mpath.read_text(encoding="utf-8"))
    if man.get("edition") not in ("friends", "team") or not isinstance(man.get("release"), int):
        raise Refusal("MANIFEST.json needs edition friends|team and an integer release")
    for rel, meta in man.get("files", {}).items():
        if meta.get("class") not in CLASSES:
            raise Refusal(f"{rel}: unknown class {meta.get('class')!r}")
        if isinstance(rel, str) and is_tool_path(rel):
            raise Refusal(f"{rel}: a Release may not ship apply-release state")
        data = read_opt(fs_path(rdir, rel))
        if data is None:
            raise Refusal(f"{rel} is listed in MANIFEST.json but missing from the Release folder")
        if sha(data) != meta.get("sha256"):
            raise Refusal(f"{rel} does not match its MANIFEST.json sha256; the Release folder is damaged")
    return rdir, man


# ---- schema --------------------------------------------------------------

def dump_schema(schema):
    items = list(schema.items())
    lines = ["{"]
    for i, (k, v) in enumerate(items):
        comma = "," if i < len(items) - 1 else ""
        lines.append(f"  {json.dumps(k)}: {json.dumps(v, ensure_ascii=False)}{comma}")
    lines.append("}")
    return ("\n".join(lines) + "\n").encode("utf-8")


def frontmatter_subject(path):
    try:
        text = norm(path.read_bytes()).decode("utf-8", errors="replace")
    except OSError:
        return None
    if not text.startswith("---\n"):
        return None
    for line in text.split("\n")[1:]:
        if line.strip() == "---":
            break
        if line.startswith("subject:"):
            return line.split(":", 1)[1].strip().strip("'\"")
    return None


def md_under(root, d):
    return [p.relative_to(root).as_posix() for p in d.rglob("*.md")] if d.is_dir() else []


def schema_usage(root, key, entry, schema):
    mem = Path(root) / "memory"
    hits = []
    if key == "client_subjects":
        hits += md_under(root, mem / "clients" / entry)
        if mem.is_dir():
            hits += [p.relative_to(root).as_posix() for p in mem.rglob("*.md") if frontmatter_subject(p) == entry]
    elif key == "topics":
        for td in schema.get("topic_dirs") or DEFAULT_TOPIC_DIRS:
            hits += md_under(root, mem / td / entry)
    elif key == "topic_dirs":
        hits += md_under(root, mem / entry)
    elif key == "client_dirs":
        clients = Path(root) / "clients"
        if clients.is_dir():
            for d in clients.glob(f"*/{entry}"):
                if d.is_dir():
                    hits += [p.relative_to(root).as_posix() for p in d.rglob("*") if p.is_file()]
    return sorted(set(hits))


def plan_schema(root, rdir, snap, st, n):
    """Data merge of memory/schema.json: owner kept, Release additions added, removals held if used."""
    theirs_b = fs_path(rdir, SCHEMA_PATH).read_bytes()
    theirs = json.loads(theirs_b.decode("utf-8"))
    base_b = snap.read(SCHEMA_PATH) if snap else None
    base = json.loads(base_b.decode("utf-8")) if base_b else {}
    owner_b = read_opt(fs_path(root, SCHEMA_PATH))
    report = {"added": {}, "removed": {}, "held": [], "holds_cleared": []}
    if owner_b is None:
        entry = {"path": SCHEMA_PATH, "class": "merge", "action": "add",
                 "reason": "schema-restored" if snap else "new"}
        return entry, theirs_b, report
    owner = json.loads(owner_b.decode("utf-8"))
    result = dict(owner)
    for k in SCHEMA_KEYS:
        ol = list(owner.get(k, []))
        tl = theirs.get(k, [])
        bl = base.get(k, [])
        add = [x for x in tl if x not in ol and x not in bl]
        for x in [x for x in bl if x not in tl and x in ol]:
            notes = schema_usage(root, k, x, owner)
            if notes:
                report["held"].append({"key": k, "entry": x, "change": "remove", "release": n, "notes": notes})
            else:
                ol.remove(x)
                report["removed"].setdefault(k, []).append(x)
        ol += add
        if add:
            report["added"][k] = add
        if k in owner or ol:
            result[k] = ol
    for h in st["holds"]:
        if h["entry"] in theirs.get(h["key"], []):
            report["holds_cleared"].append(h)
    write = styled(dump_schema(result), owner_b) if result != owner else None
    entry = {"path": SCHEMA_PATH, "class": "merge", "action": "schema" if write else "keep",
             "reason": "schema-data-merge" if write else "schema-unchanged"}
    return entry, write, report


# ---- plan ----------------------------------------------------------------

def deleted_conflict_text(theirs, n):
    body = norm(theirs)
    if body and not body.endswith(b"\n"):
        body += b"\n"
    return (OPEN + "owner (you deleted this file)\n" + MID + "\n").encode() + body + (CLOSE + f"release {n}\n").encode()


def decide(root, rdir, p, new, old, owner, base, first, seeds, locals_, n):
    """Return (entry, write_bytes, sidecar_bytes) for one path."""
    e = {"path": p, "class": new["class"] if new else None}
    if old and new and old["class"] != new["class"]:
        e["class_change"] = f"{old['class']}->{new['class']}"

    def done(action, reason, write=None, sidecar=None, kind=None):
        e["action"], e["reason"] = action, reason
        if kind:
            e["conflict"] = kind
        if new and action != "delete" and (write is not None or (owner is not None and old and old.get("mode") != new.get("mode"))):
            e["mode"] = new.get("mode", "644")
        return e, write, sidecar

    if new is None:
        if old["class"] != "merge":
            return done("keep", "owner-file")
        if owner is None:
            return done("keep", "already-absent")
        if base is not None and sha(owner) == sha(base):
            return done("delete", "release-removed")
        return done("keep", "release-removed-owner-modified")

    theirs = fs_path(rdir, p).read_bytes()
    if new["class"] in ("seed", "local"):
        if owner is not None:
            return done("keep", "owner-file")
        if first or (old is None and p not in seeds and p not in locals_):
            return done("add", "install-once", theirs)
        return done("keep", "owner-deleted")

    previously_owned = bool(old and old["class"] != "merge") or p in seeds or p in locals_
    if owner is None:
        if previously_owned:
            return done("keep", "owner-deleted")
        if old is None:
            return done("add", "new", theirs)
        if old["sha256"] == new["sha256"]:
            return done("keep", "owner-deleted")
        if is_binary(theirs):
            return done("conflict", "owner-deleted-release-changed", sidecar=theirs, kind="owner-deleted-release-changed")
        return done("conflict", "owner-deleted-release-changed", deleted_conflict_text(theirs, n),
                    kind="owner-deleted-release-changed")
    if sha(owner) == new["sha256"]:
        return done("keep", "same")
    if base is None:
        if is_binary(owner, theirs):
            return done("conflict", "collision", sidecar=theirs, kind="collision")
        out, _ = merge3(b"", owner, theirs, n)
        return done("conflict", "collision", styled(out, owner), kind="collision")
    if sha(base) == new["sha256"]:
        return done("keep", "unchanged-in-release")
    if sha(owner) == sha(base):
        return done("update", "owner-unchanged", theirs if is_binary(theirs) else styled(theirs, owner))
    if is_binary(owner, base, theirs):
        return done("conflict", "binary", sidecar=theirs, kind="binary")
    out, conflicted = merge3(base, owner, theirs, n)
    if conflicted:
        return done("conflict", "overlap", styled(out, owner), kind="overlap")
    return done("merge", "clean-3-way", styled(out, owner))


def build_plan(root, release_dir):
    st = load_state(root)
    rdir, man = load_release(release_dir)
    n = man["release"]
    inprog = st["in_progress"]
    if st["edition"] and st["edition"] != man["edition"]:
        raise Refusal(f"this workspace runs the {st['edition']} edition; the Release is {man['edition']}")
    if inprog and inprog["release"] != n:
        raise Refusal(f"Release {inprog['release']} is half applied; finish it (or roll back) first")
    if st["release"] is not None and n <= st["release"]:
        raise Refusal(f"Release {n} is not newer than the applied Release {st['release']}")
    snap = open_snapshot(root, st)
    old_files = snapshot_manifest(snap)["files"] if snap else {}
    new_files = man["files"]
    seeds, locals_ = set(st["seeds_installed"]), set(st["locals_installed"])
    first = snap is None
    entries, writes, schema_report = [], {}, None
    for p in sorted(set(new_files) | set(old_files)):
        if p in RELEASE_META:
            continue
        new, old = new_files.get(p), old_files.get(p)
        if p == SCHEMA_PATH and new:
            e, w, schema_report = plan_schema(root, rdir, snap, st, n)
            sidecar = None
        else:
            owner = read_opt(fs_path(root, p))
            base = snap.read(p) if (snap and old) else None
            e, w, sidecar = decide(root, rdir, p, new, old, owner, base, first, seeds, locals_, n)
        entries.append(e)
        writes[p] = (w, sidecar)
    conflicts = [{"path": e["path"], "kind": e["conflict"],
                  **({"sidecar": e["path"] + ".release"} if writes[e["path"]][1] is not None else {})}
                 for e in entries if e["action"] == "conflict"]
    notable = {"release-removed-owner-modified", "owner-deleted", "collision", "owner-deleted-release-changed",
               "schema-restored"}
    reports = [{"path": e["path"], "reason": e["reason"], **({"class_change": e["class_change"]} if "class_change" in e else {})}
               for e in entries if e["reason"] in notable or "class_change" in e]
    plan = {
        "edition": man["edition"],
        "release": n,
        "from_release": st["release"],
        "first_install": first,
        "git_repo": is_repo(root),
        "files": entries,
        "conflicts": conflicts,
        "reports": reports,
        "schema": schema_report or {"added": {}, "removed": {}, "held": [], "holds_cleared": []},
        "holds_pending": st["holds"],
        "dirty_blocking": [],
    }
    if plan["git_repo"]:
        plan["dirty_blocking"] = blocking_dirty(root, entries, inprog)
    return plan, writes, st, rdir, man


# ---- working tree checks -------------------------------------------------

def dirty_paths(root):
    out = git(["--no-optional-locks", "status", "--porcelain=v1", "-z", "--untracked-files=all"], root).stdout
    toks = out.decode("utf-8").split("\0")
    paths, i = [], 0
    while i < len(toks):
        t = toks[i]
        i += 1
        if not t:
            continue
        paths.append(t[3:])
        if "R" in t[:2] or "C" in t[:2]:
            paths.append(toks[i])
            i += 1
    return [p for p in paths if not is_tool_path(p)]


def blocking_dirty(root, entries, inprog):
    ok = {e["path"] for e in entries if e["action"] in CLEAN_ACTIONS}
    if inprog:
        ok |= {f["path"] for f in inprog["files"]}
        ok |= {c["sidecar"] for c in inprog["conflicts"] if c.get("sidecar")}
    return sorted(p for p in dirty_paths(root) if p not in ok)


def marker_flags(data):
    lines = norm(data).decode("utf-8", errors="replace").split("\n")
    return (any(l.startswith(OPEN) for l in lines), any(l == MID for l in lines),
            any(l.startswith(CLOSE) for l in lines))


def workspace_files(root):
    if is_repo(root):
        out = git(["ls-files", "-z", "--cached", "--others", "--exclude-standard"], root).stdout
        files = [p for p in out.decode("utf-8").split("\0") if p]
    else:
        files = rel_files(root)
    return [p for p in files if not is_tool_path(p)]


def remaining_conflicts(root, st):
    found = {}
    inprog = st["in_progress"] or {"conflicts": []}
    for c in inprog["conflicts"]:
        if c.get("sidecar") and fs_path(root, c["sidecar"]).exists():
            found[c["path"]] = f"decide between your file and {c['sidecar']}, then delete {c['sidecar']}"
            continue
        data = read_opt(fs_path(root, c["path"]))
        if data is not None and not is_binary(data):
            o, m, cl = marker_flags(data)
            if o or cl or (o and m):
                found[c["path"]] = "conflict markers remain"
    for p in workspace_files(root):
        if p in found:
            continue
        data = read_opt(fs_path(root, p))
        if data is not None and not is_binary(data) and all(marker_flags(data)):
            found[p] = "conflict markers remain"
    return [{"path": p, "problem": v} for p, v in sorted(found.items())]


# ---- commands ------------------------------------------------------------

def emit(obj):
    sys.stdout.write(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def cmd_plan(root, args):
    plan, *_ = build_plan(root, args.release_dir)
    emit(plan)
    return 0


def chmod(path, mode):
    if os.name != "nt" and path.is_file():
        os.chmod(path, int(mode, 8))


def entries_mode_only(plan, rel):
    """A file kept as is whose only change in this Release is its mode: it is still modified by the apply."""
    return any(e["path"] == rel and "mode" in e for e in plan["files"])


def cmd_apply(root, args):
    plan, writes, st, rdir, man = build_plan(root, args.release_dir)
    if plan["dirty_blocking"] and not args.allow_dirty:
        raise Refusal("uncommitted changes in files this Release does not cleanly touch: "
                      + ", ".join(plan["dirty_blocking"])
                      + ". Commit or set them aside first, or rerun with --allow-dirty.")
    n = man["release"]
    inprog = st["in_progress"]
    backup = Backup(root, n)
    backup.start(st, fresh=inprog is None)
    if inprog is None:
        inprog = {
            "release": n,
            "edition": man["edition"],
            "release_dir": str(rdir),
            "started": now(),
            "files": [{"path": e["path"], "action": e["action"],
                       "target": sha(writes[e["path"]][0]) if writes[e["path"]][0] is not None else None}
                      for e in plan["files"] if e["action"] in WRITING_ACTIONS or "mode" in e],
            "done": [],
            "conflicts": plan["conflicts"],
        }
        held = {(h["key"], h["entry"]) for h in plan["schema"]["held"]}
        cleared = {(h["key"], h["entry"]) for h in plan["schema"]["holds_cleared"]}
        st["holds"] = [h for h in st["holds"] if (h["key"], h["entry"]) not in held | cleared] + plan["schema"]["held"]
    # Every path this apply may change is copied before the first change, so an interruption stays recoverable.
    for f in inprog["files"]:
        if f["action"] in WRITING_ACTIONS or entries_mode_only(plan, f["path"]):
            backup.protect(f["path"])
    for c in inprog["conflicts"]:
        if c.get("sidecar"):
            backup.protect(c["sidecar"])
    if st["in_progress"] is None:
        st["in_progress"] = inprog
        save_state(root, st)
    entries = {e["path"]: e for e in plan["files"]}
    for f in inprog["files"]:
        p = f["path"]
        if p in inprog["done"]:
            continue
        target = fs_path(root, p)
        current = read_opt(target)
        # Rerun after an interruption: the file already holds what we planned to write.
        already = (f["action"] == "delete" and current is None) or (
            f["target"] is not None and current is not None and sha(current) == f["target"])
        e = entries.get(p)
        if not already and e is not None:
            write, sidecar = writes[p]
            if e["action"] == "delete":
                target.unlink(missing_ok=True)
            elif write is not None:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(write)
            if sidecar is not None:
                fs_path(root, p + ".release").write_bytes(sidecar)
        if e is not None and "mode" in e:
            chmod(target, e["mode"])
        backup.wrote(p)
        if e is not None and writes[p][1] is not None:
            backup.wrote(p + ".release")
        inprog["done"].append(p)
        save_state(root, st)
    left = remaining_conflicts(root, st)
    emit({"release": n, "applied": len(inprog["done"]), "conflicts": left, "holds": st["holds"],
          "next": "resolve conflicts and holds with the owner, then run finish" if left or st["holds"] else "run finish"})
    return 1 if left or st["holds"] else 0


def cmd_finish(root, args):
    st = load_state(root)
    inprog = st["in_progress"]
    if inprog is None:
        raise Refusal("nothing to finish: run apply first")
    left = remaining_conflicts(root, st)
    if left or st["holds"]:
        emit({"finished": False, "conflicts": left, "holds": st["holds"]})
        return 1
    rdir, man = load_release(inprog["release_dir"])
    n = man["release"]
    repo = is_repo(root)
    if repo:
        ref = f"refs/releases/{n}"
        store_git_snapshot(root, rdir, man, ref)
        st["snapshots"][str(n)] = {"store": "git", "location": ref}
    else:
        loc = f"{SNAP_DIR_REL}/{n}"
        dest = fs_path(root, loc)
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(rdir, dest)
        st["snapshots"][str(n)] = {"store": "folder", "location": loc}
    files = man["files"]
    st["seeds_installed"] = sorted(set(st["seeds_installed"]) | {p for p, m in files.items() if m["class"] == "seed"})
    st["locals_installed"] = sorted(set(st["locals_installed"]) | {p for p, m in files.items() if m["class"] == "local"})
    st["edition"], st["release"], st["in_progress"] = man["edition"], n, None
    st["history"].append({"release": n, "started": inprog["started"], "finished": now()})
    save_state(root, st)
    result = {"finished": True, "release": n, "snapshot": st["snapshots"][str(n)], "committed": False}
    if repo:
        result.update(commit(root, inprog, n))
    emit(result)
    return 0 if result.get("commit_error") is None else 1


def commit(root, inprog, n):
    touched = {f["path"] for f in inprog["files"]} | {STATE_REL}
    staged = [p for p in git(["diff", "--cached", "--name-only", "-z"], root).stdout.decode("utf-8").split("\0") if p]
    unrelated = sorted(set(staged) - touched)
    if unrelated:
        return {"commit_skipped": "other files are staged: " + ", ".join(unrelated) + "; commit the Release yourself"}
    env = {"GIT_LITERAL_PATHSPECS": "1"}
    for p in sorted(touched):
        if fs_path(root, p).exists():
            git(["add", "--", p], root, env=env)
        else:
            git(["rm", "--cached", "--quiet", "--ignore-unmatch", "--", p], root, env=env)
    if git(["diff", "--cached", "--quiet"], root, check=False).returncode == 0:
        return {"commit_skipped": "nothing changed"}
    r = git(["commit", "-q", "-m", f"apply Release {n}"], root, env=env, check=False)
    if r.returncode != 0:
        return {"commit_error": (r.stdout + r.stderr).decode("utf-8", errors="replace").strip()
                + f"\nFix what the hook reports, then commit with message 'apply Release {n}'."}
    return {"committed": True}


def cmd_status(root, args):
    st = load_state(root)
    repo = is_repo(root)
    refs = 0
    if repo:
        out = git(["for-each-ref", "--format=%(refname)", "refs/releases/"], root).stdout.decode()
        refs = len([l for l in out.splitlines() if l])
    snap_dir = fs_path(root, SNAP_DIR_REL)
    folders = len([d for d in snap_dir.iterdir() if d.is_dir()]) if snap_dir.is_dir() else 0
    inprog = st["in_progress"]
    emit({
        "edition": st["edition"],
        "release": st["release"],
        "git_repo": repo,
        "in_progress": None if inprog is None else {
            "release": inprog["release"], "release_dir": inprog["release_dir"],
            "planned": len(inprog["files"]), "done": len(inprog["done"]),
            "pending": [f["path"] for f in inprog["files"] if f["path"] not in inprog["done"]],
        },
        "conflicts": remaining_conflicts(root, st) if inprog else [],
        "holds": st["holds"],
        "snapshots": {"refs": refs, "folders": folders, "count": refs + folders},
    })
    return 0


def cmd_resolve_hold(root, args):
    st = load_state(root)
    key, _, entry = args.entry.rpartition(":")
    matches = [h for h in st["holds"] if h["entry"] == entry and (not key or h["key"] == key)]
    if not matches:
        raise Refusal(f"no hold for {args.entry!r}")
    if len(matches) > 1:
        raise Refusal(f"{entry!r} is held under several keys; use <key>:<entry>")
    hold = matches[0]
    spath = fs_path(root, SCHEMA_PATH)
    owner_b = spath.read_bytes()
    schema = json.loads(owner_b.decode("utf-8"))
    notes = schema_usage(root, hold["key"], hold["entry"], schema)
    if notes:
        emit({"resolved": False, "hold": hold, "still_used_by": notes})
        return 1
    if hold["entry"] in schema.get(hold["key"], []):
        schema[hold["key"]] = [x for x in schema[hold["key"]] if x != hold["entry"]]
        backup = Backup(root, st["in_progress"]["release"]) if st["in_progress"] is not None else None
        if backup is not None:
            backup.protect(SCHEMA_PATH)
        spath.write_bytes(styled(dump_schema(schema), owner_b))
        if backup is not None:
            backup.wrote(SCHEMA_PATH)
    st["holds"] = [h for h in st["holds"] if h is not hold]
    if st["in_progress"] is not None:
        files = st["in_progress"]["files"]
        if not any(f["path"] == SCHEMA_PATH for f in files):
            files.append({"path": SCHEMA_PATH, "action": "schema", "target": None})
            st["in_progress"]["done"].append(SCHEMA_PATH)
    save_state(root, st)
    emit({"resolved": True, "hold": hold})
    return 0


def interrupted_rollback(root):
    """The Release whose rollback started but did not finish, if any (its state file may already be restored)."""
    base = fs_path(root, BACKUP_DIR_REL)
    if not base.is_dir():
        return None
    for d in sorted(base.iterdir()):
        meta_path = d / "backup.json"
        if d.is_dir() and d.name.isdigit() and meta_path.is_file():
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            if meta.get("rolling_back") and not meta.get("rolled_back"):
                return int(d.name)
    return None


def cmd_rollback(root, args):
    st = load_state(root)
    inprog = st["in_progress"]
    current = inprog["release"] if inprog else st["release"]
    resuming = interrupted_rollback(root) if args.release is None else None
    n = args.release if args.release is not None else (resuming if resuming is not None else current)
    if n is None:
        raise Refusal("nothing to roll back: no Release is applied or in progress")
    backup = Backup(root, n)
    meta = backup.meta
    if meta is None:
        raise Refusal(f"no backup for Release {n} in {BACKUP_DIR_REL}/{n}/; it cannot be rolled back automatically")
    if meta.get("rolled_back"):
        raise Refusal(f"Release {n} was already rolled back")
    resuming = bool(meta.get("rolling_back"))
    if n != current and not resuming:
        raise Refusal(f"Release {current} is the latest applied or in-progress Release; roll it back before Release {n}")
    # Checked on every pass, a resumed one included: a path counts as changed unless it still holds what rolling
    # back would put there anyway (the pre-apply bytes, or for a path the apply reached the bytes the apply left).
    # A path the apply never reached has no recorded result, so anything but its pre-apply state is the owner's
    # work. A path an interrupted rollback already restored equals its pre-apply bytes, so it is not flagged,
    # while an owner edit made after that restore is.
    changed = []
    for rel, info in meta["files"].items():
        if rel == STATE_REL:
            continue
        now_sha = raw_sha(read_opt(fs_path(root, rel)))
        before_sha = raw_sha(read_opt(backup.copy_path("files", rel))) if info["existed"] else None
        left_sha = info.get("after_sha256", before_sha)
        if now_sha not in (left_sha, before_sha):
            changed.append(rel)
    if changed and not args.force:
        raise Refusal("changed since the apply wrote them: " + ", ".join(sorted(changed))
                      + ". Rolling back would lose those changes; rerun with --force to save them under "
                      + f"{BACKUP_DIR_REL}/{n}/rolled-back/ first.")
    for rel in changed:
        data = read_opt(fs_path(root, rel))
        if data is not None:
            backup.rescue(rel, data)
    if not resuming:
        # Recorded before anything is restored. Restoring is idempotent, so a rerun resumes it, and the state
        # file may by then point at the previous Release.
        meta["rolling_back"] = True
        backup.save()
    restored, deleted = [], []
    # The state file goes last: if this is interrupted, a rerun resumes and finishes.
    for rel in sorted(meta["files"], key=lambda r: r == STATE_REL):
        target = fs_path(root, rel)
        if meta["files"][rel]["existed"]:
            src = backup.copy_path("files", rel)
            if not src.is_file():
                raise Refusal(f"backup copy of {rel} is missing from {BACKUP_DIR_REL}/{n}/files/")
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
            restored.append(rel)
        elif target.is_file():
            target.unlink()
            deleted.append(rel)
    meta["rolled_back"] = True
    meta.pop("rolling_back", None)
    backup.save()
    nxt = ("The working tree is back to how it was before Release {n} was applied, including uncommitted edits. "
           "Show the owner `git status`; the owner decides what to commit (hooks run, never --no-verify). "
           "Git history, the index and the snapshot ref refs/releases/{n} were not touched; the ref is harmless. "
           "The backup stays in {d}/{n}/.").format(n=n, d=BACKUP_DIR_REL)
    emit({"release": n, "restored": restored, "deleted": deleted, "next": nxt})
    return 0


def main(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=".", help="owner workspace root (default: current directory)")
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("plan", parents=[common], help="read-only JSON plan")
    p.add_argument("release_dir")
    p.set_defaults(fn=cmd_plan)
    p = sub.add_parser("apply", parents=[common], help="apply the plan to the working tree")
    p.add_argument("release_dir")
    p.add_argument("--allow-dirty", action="store_true")
    p.set_defaults(fn=cmd_apply)
    sub.add_parser("finish", parents=[common], help="snapshot and commit").set_defaults(fn=cmd_finish)
    sub.add_parser("status", parents=[common], help="show state").set_defaults(fn=cmd_status)
    p = sub.add_parser("rollback", parents=[common], help="restore the working tree to before an apply")
    p.add_argument("--release", type=int, help="Release to roll back (default: the latest applied or in progress)")
    p.add_argument("--force", action="store_true", help="overwrite files changed since the apply, saving them first")
    p.set_defaults(fn=cmd_rollback)
    p = sub.add_parser("resolve-hold", parents=[common], help="clear a schema hold after migrating notes")
    p.add_argument("entry", help="<entry> or <key>:<entry>")
    p.set_defaults(fn=cmd_resolve_hold)
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    try:
        return args.fn(root, args)
    except Refusal as exc:
        sys.stderr.write(f"apply-release: {exc}\n")
        return 2


if __name__ == "__main__":
    sys.exit(main())
