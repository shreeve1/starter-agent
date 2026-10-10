import contextlib
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "apply_release.py"
_spec = importlib.util.spec_from_file_location("apply_release", SCRIPT)
ar = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ar)

OPEN, MID, CLOSE = "<" * 7 + " ", "=" * 7, ">" * 7 + " "
GIT_ENV = {
    "GIT_AUTHOR_NAME": "Owner", "GIT_AUTHOR_EMAIL": "owner@example.com",
    "GIT_COMMITTER_NAME": "Owner", "GIT_COMMITTER_EMAIL": "owner@example.com",
    "GIT_CONFIG_NOSYSTEM": "1",
}

AGENTS = "# Agents\n\nline 1\nline 2\nline 3\nline 4\nline 5\nline 6\nline 7\nline 8\n"
SCHEMA = {"client_subjects": ["halo", "365"], "topics": ["halo", "skills"],
          "topic_dirs": ["workflows", "decisions"], "client_dirs": ["tickets", "projects"]}
PNG = b"\x89PNG\r\n\x1a\n\0\0\0binary-v1"


def schema_bytes(s):
    return (json.dumps(s, indent=2) + "\n").encode()


def edition_v1():
    return {
        "AGENTS.md": (AGENTS.encode(), "merge", "644"),
        "README.md": (b"# Readme\n\nintro\n", "merge", "644"),
        ".agents/skills/demo/SKILL.md": (b"---\nname: demo\n---\n\nbody\n", "merge", "644"),
        ".agents/skills/demo/run.py": (b"print('v1')\n", "merge", "644"),
        "memory/schema.json": (schema_bytes(SCHEMA), "merge", "644"),
        "memory/index.md": (b"# Index\n", "local", "644"),
        ".agents/operator-profile.json": (b"{}\n", "local", "644"),
        "memory/guides/welcome.md": (b"# Welcome\n", "seed", "644"),
        "memory/guides/tips.md": (b"# Tips\n", "seed", "644"),
        "assets/logo.png": (PNG, "merge", "644"),
        "docs/old.md": (b"# Old doc\n", "merge", "644"),
    }


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        cfg = self.tmp / "gitconfig"
        cfg.write_text("[init]\n\tdefaultBranch = main\n[commit]\n\tgpgsign = false\n", encoding="utf-8")
        patcher = mock.patch.dict(os.environ, {**GIT_ENV, "GIT_CONFIG_GLOBAL": str(cfg)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.root = self.tmp / "owner"
        self.root.mkdir()
        self.git("init", "-q")

    def git(self, *args, cwd=None):
        r = subprocess.run(["git", *args], cwd=cwd or self.root, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def release(self, n, files, edition="friends"):
        d = self.tmp / f"release-{n}"
        if d.exists():
            shutil.rmtree(d)
        man = {"edition": edition, "release": n, "files": {}}
        for rel, (data, cls, mode) in files.items():
            p = d / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
            man["files"][rel] = {"class": cls, "sha256": hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest(),
                                 "mode": mode}
        (d / "MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")
        (d / "CHANGELOG.md").write_text(f"# Release {n}\n", encoding="utf-8")
        return d

    def run_cli(self, *args):
        out = io.StringIO()
        err = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            rc = ar.main([*args, "--root", str(self.root)])
        text = out.getvalue()
        return rc, (json.loads(text) if text.strip() else None), err.getvalue()

    def ok(self, *args):
        rc, out, err = self.run_cli(*args)
        self.assertEqual(rc, 0, f"{args}: {out} {err}")
        return out

    def install(self, n, files):
        d = self.release(n, files)
        self.ok("apply", str(d))
        self.ok("finish")
        return d

    def read(self, rel):
        return (self.root / rel).read_bytes().decode()

    def write(self, rel, text):
        p = self.root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(text.encode() if isinstance(text, str) else text)

    def commit_all(self, msg="owner edit"):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def state(self):
        return json.loads(self.read(".agents/release-state.json"))

    def plan_entry(self, plan, path):
        return next(e for e in plan["files"] if e["path"] == path)


class UpdateFlow(Base):
    def test_customization_kept_v1_v2_v3(self):
        files = edition_v1()
        self.install(1, files)
        self.assertEqual(self.git("log", "-1", "--format=%s").strip(), "apply Release 1")
        self.write("AGENTS.md", AGENTS.replace("line 1", "line 1 OWNER"))
        self.commit_all()
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V2").encode(), "merge", "644")
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        self.assertEqual(self.plan_entry(plan, "AGENTS.md")["action"], "merge")
        self.ok("apply", str(d2))
        self.ok("finish")
        text = AGENTS.replace("line 8", "line 8 V2")
        files["AGENTS.md"] = (text.replace("line 4", "line 4 V3").encode(), "merge", "644")
        self.install(3, files)
        got = self.read("AGENTS.md")
        for s in ("line 1 OWNER", "line 4 V3", "line 8 V2"):
            self.assertIn(s, got)
        self.assertEqual(self.state()["release"], 3)
        self.assertEqual(self.git("log", "-1", "--format=%s").strip(), "apply Release 3")
        self.assertEqual(len(self.git("for-each-ref", "refs/releases/").splitlines()), 3)

    def test_skipped_release_v1_to_v3(self):
        files = edition_v1()
        self.install(1, files)
        self.write("AGENTS.md", AGENTS.replace("line 1", "line 1 OWNER"))
        self.commit_all()
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V3").encode(), "merge", "644")
        files["new/feature.md"] = (b"new\n", "merge", "644")
        d3 = self.release(3, files)
        plan = self.ok("plan", str(d3))
        self.assertEqual(plan["from_release"], 1)
        self.ok("apply", str(d3))
        self.ok("finish")
        self.assertIn("line 1 OWNER", self.read("AGENTS.md"))
        self.assertIn("line 8 V3", self.read("AGENTS.md"))
        self.assertEqual(self.read("new/feature.md"), "new\n")

    def test_overlap_conflict_blocks_finish_until_resolved(self):
        files = edition_v1()
        self.install(1, files)
        self.write("AGENTS.md", AGENTS.replace("line 4", "line 4 OWNER"))
        self.commit_all()
        files["AGENTS.md"] = (AGENTS.replace("line 4", "line 4 RELEASE").encode(), "merge", "644")
        d2 = self.release(2, files)
        rc, out, _ = self.run_cli("apply", str(d2))
        self.assertEqual(rc, 1)
        self.assertEqual([c["path"] for c in out["conflicts"]], ["AGENTS.md"])
        text = self.read("AGENTS.md")
        self.assertIn(OPEN, text)
        self.assertIn("\n" + MID + "\n", text)
        self.assertIn(CLOSE, text)
        rc, out, _ = self.run_cli("finish")
        self.assertEqual(rc, 1)
        self.assertFalse(out["finished"])
        self.assertEqual(self.ok("status")["in_progress"]["release"], 2)
        self.write("AGENTS.md", AGENTS.replace("line 4", "line 4 OWNER+RELEASE"))
        self.ok("finish")
        self.assertEqual(self.state()["release"], 2)
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_owner_deleted_merge_file(self):
        files = edition_v1()
        self.install(1, files)
        (self.root / "README.md").unlink()
        (self.root / "docs/old.md").unlink()
        self.commit_all()
        files["docs/old.md"] = (b"# Old doc\nchanged\n", "merge", "644")
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        self.assertEqual(self.plan_entry(plan, "README.md")["action"], "keep")
        self.assertEqual(self.plan_entry(plan, "docs/old.md")["action"], "conflict")
        rc, _, _ = self.run_cli("apply", str(d2))
        self.assertEqual(rc, 1)
        self.assertFalse((self.root / "README.md").exists())
        self.assertIn(OPEN + "owner (you deleted this file)", self.read("docs/old.md"))
        (self.root / "docs/old.md").unlink()
        self.ok("finish")
        self.assertFalse((self.root / "docs/old.md").exists())

    def test_owner_renamed_file(self):
        files = edition_v1()
        self.install(1, files)
        self.git("mv", "docs/old.md", "docs/mine.md")
        self.commit_all("rename")
        files["README.md"] = (b"# Readme\n\nintro v2\n", "merge", "644")
        d2 = self.release(2, files)
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertFalse((self.root / "docs/old.md").exists())
        self.assertEqual(self.read("docs/mine.md"), "# Old doc\n")

    def test_release_deletes_file(self):
        files = edition_v1()
        self.install(1, files)
        self.write("README.md", "# Readme\n\nmine\n")
        self.commit_all()
        del files["docs/old.md"]
        del files["README.md"]
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        self.assertEqual(self.plan_entry(plan, "docs/old.md")["action"], "delete")
        self.assertEqual(self.plan_entry(plan, "README.md")["reason"], "release-removed-owner-modified")
        self.assertIn("README.md", [r["path"] for r in plan["reports"]])
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertFalse((self.root / "docs/old.md").exists())
        self.assertEqual(self.read("README.md"), "# Readme\n\nmine\n")
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_release_renames_file(self):
        files = edition_v1()
        self.install(1, files)
        files["docs/renamed.md"] = files.pop("docs/old.md")
        self.install(2, files)
        self.assertFalse((self.root / "docs/old.md").exists())
        self.assertEqual(self.read("docs/renamed.md"), "# Old doc\n")

    def test_new_release_file_collides_with_owner_file(self):
        files = edition_v1()
        self.install(1, files)
        self.write("docs/guide.md", "owner guide\n")
        self.commit_all()
        files["docs/guide.md"] = (b"release guide\n", "merge", "644")
        d2 = self.release(2, files)
        rc, out, _ = self.run_cli("apply", str(d2))
        self.assertEqual(rc, 1)
        text = self.read("docs/guide.md")
        self.assertIn("owner guide", text)
        self.assertIn("release guide", text)
        self.assertIn(OPEN, text)

    def test_first_install_existing_merge_file_is_conflict(self):
        self.write("AGENTS.md", "my own agents file\n")
        self.commit_all()
        d1 = self.release(1, edition_v1())
        plan = self.ok("plan", str(d1))
        e = self.plan_entry(plan, "AGENTS.md")
        self.assertEqual((e["action"], e["reason"]), ("conflict", "collision"))
        rc, _, _ = self.run_cli("apply", str(d1))
        self.assertEqual(rc, 1)
        self.assertIn("my own agents file", self.read("AGENTS.md"))

    def test_interrupted_apply_is_idempotent(self):
        files = edition_v1()
        self.install(1, files)
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V2").encode(), "merge", "644")
        files["README.md"] = (b"# Readme\n\nintro v2\n", "merge", "644")
        files["docs/new.md"] = (b"new\n", "merge", "644")
        d2 = self.release(2, files)
        real = ar.save_state
        calls = []

        def crash(root, st):
            calls.append(1)
            real(root, st)
            if len(calls) == 2:
                raise KeyboardInterrupt

        with mock.patch.object(ar, "save_state", crash):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("apply", str(d2))
        st = self.ok("status")
        self.assertEqual(st["in_progress"]["release"], 2)
        self.assertEqual(st["in_progress"]["planned"], 3)
        self.assertTrue(st["in_progress"]["pending"])
        self.ok("apply", str(d2))
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertIn("line 8 V2", self.read("AGENTS.md"))
        self.assertEqual(self.read("README.md"), "# Readme\n\nintro v2\n")
        self.assertIsNone(self.state()["in_progress"])

    def test_dirty_tree(self):
        files = edition_v1()
        self.install(1, files)
        files["README.md"] = (b"# Readme\n\nintro\nv2 tail\n", "merge", "644")
        d2 = self.release(2, files)
        self.write("README.md", "# Readme OWNER\n\nintro\n")
        plan = self.ok("plan", str(d2))
        self.assertEqual(plan["dirty_blocking"], [])
        self.write("docs/old.md", "# Old doc\nuncommitted\n")
        self.write("scratch.txt", "x\n")
        rc, out, err = self.run_cli("apply", str(d2))
        self.assertEqual(rc, 2)
        self.assertIn("docs/old.md", err)
        self.assertIn("scratch.txt", err)
        self.assertIn("--allow-dirty", err)
        self.ok("apply", str(d2), "--allow-dirty")
        self.assertEqual(self.read("README.md"), "# Readme OWNER\n\nintro\nv2 tail\n")
        self.ok("finish")
        committed = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertNotIn("scratch.txt", committed)
        self.assertNotIn("docs/old.md", committed)
        self.assertIn("README.md", committed)

    def test_unrelated_staged_file_skips_commit(self):
        files = edition_v1()
        self.install(1, files)
        files["README.md"] = (b"# Readme\n\nv2\n", "merge", "644")
        d2 = self.release(2, files)
        self.ok("apply", str(d2))
        self.write("scratch.txt", "x\n")
        self.git("add", "scratch.txt")
        out = self.ok("finish")
        self.assertIn("scratch.txt", out["commit_skipped"])
        self.assertEqual(self.git("log", "-1", "--format=%s").strip(), "apply Release 1")

    def test_binary_files(self):
        files = edition_v1()
        self.install(1, files)
        files["assets/logo.png"] = (PNG + b"-v2", "merge", "644")
        self.install(2, files)
        self.assertEqual((self.root / "assets/logo.png").read_bytes(), PNG + b"-v2")
        self.write("assets/logo.png", PNG + b"-owner")
        self.commit_all()
        files["assets/logo.png"] = (PNG + b"-v3", "merge", "644")
        d3 = self.release(3, files)
        rc, out, _ = self.run_cli("apply", str(d3))
        self.assertEqual(rc, 1)
        self.assertEqual((self.root / "assets/logo.png").read_bytes(), PNG + b"-owner")
        self.assertEqual((self.root / "assets/logo.png.release").read_bytes(), PNG + b"-v3")
        self.assertEqual(self.run_cli("finish")[0], 1)
        (self.root / "assets/logo.png.release").unlink()
        self.ok("finish")

    @unittest.skipIf(os.name == "nt", "modes are ignored on Windows")
    def test_mode_change(self):
        files = edition_v1()
        self.install(1, files)
        script = ".agents/skills/demo/run.py"
        self.assertFalse(os.access(self.root / script, os.X_OK))
        self.assertEqual(self.git("ls-files", "-s", script).split()[0], "100644")
        files[script] = (b"print('v1')\n", "merge", "755")
        self.install(2, files)
        self.assertTrue(os.access(self.root / script, os.X_OK))
        self.assertEqual(self.git("ls-files", "-s", script).split()[0], "100755", "the commit must carry the mode")
        self.assertEqual(self.git("diff", "--name-only", "HEAD").strip(), "", "nothing left uncommitted")

    @unittest.skipIf(os.name == "nt", "modes are ignored on Windows")
    def test_mode_only_change_is_backed_up_and_rolled_back(self):
        files = edition_v1()
        self.install(1, files)
        script = ".agents/skills/demo/run.py"
        files[script] = (b"print('v1')\n", "merge", "755")
        d2 = self.release(2, files)
        self.assertEqual(self.plan_entry(self.ok("plan", str(d2)), script)["action"], "keep")
        self.ok("apply", str(d2))
        self.assertTrue(os.access(self.root / script, os.X_OK))
        self.ok("rollback")
        self.assertFalse(os.access(self.root / script, os.X_OK), "rollback must restore the old mode")
        self.assertEqual(self.git("ls-files", "-s", script).split()[0], "100644")

    def test_status_reports_snapshot_count(self):
        files = edition_v1()
        self.install(1, files)
        self.install(2, files)
        st = self.ok("status")
        self.assertEqual(st["snapshots"]["refs"], 2)
        self.assertEqual(st["release"], 2)
        self.assertIsNone(st["in_progress"])

    def test_crlf_owner_file_keeps_style(self):
        files = edition_v1()
        self.install(1, files)
        self.write("AGENTS.md", AGENTS.replace("line 1", "line 1 OWNER").replace("\n", "\r\n").encode())
        self.commit_all()
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V2").encode(), "merge", "644")
        d2 = self.release(2, files)
        self.assertEqual(self.plan_entry(self.ok("plan", str(d2)), "AGENTS.md")["action"], "merge")
        self.ok("apply", str(d2))
        raw = (self.root / "AGENTS.md").read_bytes()
        self.assertEqual(raw.count(b"\r\n"), raw.count(b"\n"))
        self.assertIn(b"line 1 OWNER\r\n", raw)
        self.assertIn(b"line 8 V2\r\n", raw)
        # CRLF-only difference counts as unchanged.
        self.write("README.md", b"# Readme\r\n\r\nintro\r\n")
        self.assertEqual(self.plan_entry(self.ok("plan", str(d2)), "README.md")["action"], "keep")


class NoGit(Base):
    def test_without_git_uses_folder_snapshot(self):
        shutil.rmtree(self.root / ".git")
        files = edition_v1()
        self.install(1, files)
        st = self.state()
        self.assertEqual(st["snapshots"]["1"], {"store": "folder", "location": ".agents/snapshots/1"})
        self.assertTrue((self.root / ".agents/snapshots/1/AGENTS.md").is_file())
        self.write("AGENTS.md", AGENTS.replace("line 1", "line 1 OWNER"))
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V2").encode(), "merge", "644")
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        self.assertFalse(plan["git_repo"])
        self.ok("apply", str(d2))
        out = self.ok("finish")
        self.assertFalse(out["committed"])
        self.assertIn("line 1 OWNER", self.read("AGENTS.md"))
        self.assertIn("line 8 V2", self.read("AGENTS.md"))
        self.assertEqual(self.ok("status")["snapshots"]["folders"], 2)


class Classes(Base):
    def test_owner_deleted_seed_and_local_never_return(self):
        files = edition_v1()
        self.install(1, files)
        for rel in ("memory/guides/welcome.md", "memory/index.md"):
            (self.root / rel).unlink()
        self.commit_all()
        files["memory/guides/welcome.md"] = (b"# Welcome v2\n", "seed", "644")
        self.install(2, files)
        self.install(3, files)
        self.assertFalse((self.root / "memory/guides/welcome.md").exists())
        self.assertFalse((self.root / "memory/index.md").exists())
        self.assertIn("memory/guides/welcome.md", self.state()["seeds_installed"])

    def test_seed_to_merge_after_owner_deleted(self):
        files = edition_v1()
        self.install(1, files)
        (self.root / "memory/guides/tips.md").unlink()
        self.commit_all()
        files["memory/guides/tips.md"] = (b"# Tips v2\n", "merge", "644")
        files["memory/guides/welcome.md"] = (b"# Welcome\nmore\n", "merge", "644")
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        tips = self.plan_entry(plan, "memory/guides/tips.md")
        self.assertEqual((tips["action"], tips["class_change"]), ("keep", "seed->merge"))
        reported = {r["path"]: r for r in plan["reports"]}
        self.assertEqual(reported["memory/guides/tips.md"]["reason"], "owner-deleted")
        self.assertEqual(self.plan_entry(plan, "memory/guides/welcome.md")["action"], "update")
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertFalse((self.root / "memory/guides/tips.md").exists())
        self.assertEqual(self.read("memory/guides/welcome.md"), "# Welcome\nmore\n")

    def test_seed_and_local_not_overwritten(self):
        files = edition_v1()
        self.install(1, files)
        self.write("memory/index.md", "# My index\n")
        self.commit_all()
        files["memory/index.md"] = (b"# Index v2\n", "local", "644")
        self.install(2, files)
        self.assertEqual(self.read("memory/index.md"), "# My index\n")


class Schema(Base):
    def test_held_removal_unused_removal_and_resolve_hold(self):
        files = edition_v1()
        self.install(1, files)
        self.write("memory/clients/halo/acme/note.md", "---\nsubject: halo\n---\nx\n")
        owner = dict(SCHEMA, topics=SCHEMA["topics"] + ["owner-topic"])
        self.write("memory/schema.json", schema_bytes(owner))
        self.commit_all()
        v2 = {"client_subjects": ["365", "network"], "topics": ["halo"],
              "topic_dirs": ["workflows", "decisions"], "client_dirs": ["tickets", "projects"]}
        files["memory/schema.json"] = (schema_bytes(v2), "merge", "644")
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        held = plan["schema"]["held"]
        self.assertEqual([(h["key"], h["entry"]) for h in held], [("client_subjects", "halo")])
        self.assertEqual(held[0]["notes"], ["memory/clients/halo/acme/note.md"])
        self.assertEqual(plan["schema"]["removed"], {"topics": ["skills"]})
        self.assertEqual(plan["schema"]["added"], {"client_subjects": ["network"]})
        rc, out, _ = self.run_cli("apply", str(d2))
        self.assertEqual(rc, 1)
        got = json.loads(self.read("memory/schema.json"))
        self.assertEqual(got["client_subjects"], ["halo", "365", "network"])
        self.assertEqual(got["topics"], ["halo", "owner-topic"])
        self.assertEqual(self.run_cli("finish")[0], 1)
        rc, out, _ = self.run_cli("resolve-hold", "halo")
        self.assertEqual(rc, 1)
        self.assertEqual(out["still_used_by"], ["memory/clients/halo/acme/note.md"])
        self.write("memory/clients/network/acme/note.md", "---\nsubject: network\n---\nx\n")
        shutil.rmtree(self.root / "memory/clients/halo")
        self.ok("resolve-hold", "client_subjects:halo")
        self.assertEqual(json.loads(self.read("memory/schema.json"))["client_subjects"], ["365", "network"])
        self.ok("finish")
        self.assertEqual(self.state()["holds"], [])
        self.assertIn("memory/schema.json", self.git("show", "--name-only", "--format=", "HEAD").split())

    def with_procedures(self):
        """Install Release 1 with `procedures` in client_dirs; return the files of a Release 2 that drops it."""
        v1 = dict(SCHEMA, client_dirs=["tickets", "projects", "procedures"])
        files = edition_v1()
        files["memory/schema.json"] = (schema_bytes(v1), "merge", "644")
        self.install(1, files)
        v2 = dict(SCHEMA, client_dirs=["tickets", "projects"])
        files["memory/schema.json"] = (schema_bytes(v2), "merge", "644")
        return files

    def test_removed_client_dir_with_files_is_held_until_migrated(self):
        files = self.with_procedures()
        self.write("clients/exampleco/procedures/mail-backup.md", "# how we back up mail\n")
        self.commit_all()
        d2 = self.release(2, files)
        plan = self.ok("plan", str(d2))
        self.assertEqual([(h["key"], h["entry"]) for h in plan["schema"]["held"]], [("client_dirs", "procedures")])
        self.assertEqual(plan["schema"]["held"][0]["notes"], ["clients/exampleco/procedures/mail-backup.md"])
        self.assertEqual(self.run_cli("apply", str(d2))[0], 1)
        self.assertIn("procedures", json.loads(self.read("memory/schema.json"))["client_dirs"])
        self.assertEqual(self.run_cli("finish")[0], 1)
        (self.root / "clients/exampleco/procedures/mail-backup.md").unlink()
        self.ok("resolve-hold", "client_dirs:procedures")
        self.assertNotIn("procedures", json.loads(self.read("memory/schema.json"))["client_dirs"])
        self.ok("finish")

    def test_removed_client_dir_that_is_empty_applies(self):
        files = self.with_procedures()
        plan = self.ok("plan", str(self.release(2, files)))
        self.assertEqual(plan["schema"]["held"], [])
        self.assertEqual(plan["schema"]["removed"], {"client_dirs": ["procedures"]})


class SnapshotAndReadOnly(Base):
    def test_snapshot_survives_gc(self):
        self.install(1, edition_v1())
        commit = self.git("rev-parse", "refs/releases/1").strip()
        self.git("reflog", "expire", "--expire=now", "--all")
        self.git("gc", "-q", "--prune=now", "--aggressive")
        self.git("fsck", "--no-dangling")
        self.assertEqual(self.git("rev-parse", "refs/releases/1").strip(), commit)
        self.assertEqual(self.git("show", "refs/releases/1:AGENTS.md"), AGENTS)
        self.assertIn("MANIFEST.json", self.git("ls-tree", "--name-only", "refs/releases/1").split())

    def snapshot_bytes(self):
        out = {}
        for dirpath, _, names in os.walk(self.root):
            for n in names:
                p = Path(dirpath, n)
                out[p.relative_to(self.root).as_posix()] = p.read_bytes()
        return out

    def test_plan_is_read_only(self):
        files = edition_v1()
        self.install(1, files)
        self.write("AGENTS.md", AGENTS.replace("line 4", "line 4 OWNER"))
        self.write("scratch.txt", "dirty\n")
        files["AGENTS.md"] = (AGENTS.replace("line 4", "line 4 R").encode(), "merge", "644")
        files["docs/x.md"] = (b"x\n", "merge", "644")
        d2 = self.release(2, files)
        before = self.snapshot_bytes()
        refs = self.git("for-each-ref")
        plan = self.ok("plan", str(d2))
        self.assertEqual(plan["conflicts"][0]["path"], "AGENTS.md")
        self.assertEqual(self.snapshot_bytes(), before)
        self.assertEqual(self.git("for-each-ref"), refs)


class UnsafePaths(Base):
    """A Release is untrusted input: no manifest path may reach outside the owner's workspace."""

    def hostile_release(self, bad_path, payload_in_release=False):
        d = self.release(2, edition_v1())
        man = json.loads((d / "MANIFEST.json").read_text(encoding="utf-8"))
        data = b"payload\n"
        man["files"][bad_path] = {"class": "merge", "sha256": hashlib.sha256(data).hexdigest(), "mode": "644"}
        (d / "MANIFEST.json").write_text(json.dumps(man), encoding="utf-8")
        if payload_in_release and not ("\\" in bad_path and os.name == "nt"):
            p = d / bad_path
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        return d

    def assert_refused(self, d, outside, reason):
        """The refusal must come from the path rule, not from an unrelated problem such as a missing file."""
        for cmd in ("plan", "apply"):
            rc, out, err = self.run_cli(cmd, str(d))
            self.assertEqual(rc, 2, f"{cmd}: {out} {err}")
            self.assertIn(reason, err, f"{cmd} refused for the wrong reason: {err}")
        self.assertFalse(outside.exists(), "a file was written outside the workspace")

    def test_backslash_traversal_is_refused(self):
        d = self.hostile_release("..\\outside.txt", payload_in_release=True)
        self.assert_refused(d, self.tmp / "outside.txt", "unsafe path")
        self.assertFalse((self.root / "..\\outside.txt").exists(), "backslash name must not become a file")

    def test_posix_traversal_is_refused(self):
        d = self.hostile_release("../outside.txt")
        self.assert_refused(d, self.tmp / "outside.txt", "unsafe path")

    def test_drive_letter_stream_and_trailing_names_are_refused(self):
        for bad in ("C:/Windows/x.txt", "C:evil.txt", "docs/a.txt:stream", "/etc/x", "docs/trailing.", "docs/sp "):
            d = self.hostile_release(bad)
            self.assert_refused(d, self.tmp / "outside.txt", "unsafe path")

    def test_symlinked_parent_cannot_redirect_a_write(self):
        outside_dir = self.tmp / "elsewhere"
        outside_dir.mkdir()
        try:
            os.symlink(outside_dir, self.root / "link", target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable on this system")
        d = self.hostile_release("link/escaped.txt", payload_in_release=True)
        self.assert_refused(d, outside_dir / "escaped.txt", "escapes the workspace")

    def test_install_state_files_cannot_be_shipped(self):
        d = self.hostile_release(".agents/release-state.json", payload_in_release=True)
        rc, out, err = self.run_cli("plan", str(d))
        self.assertEqual(rc, 2)
        self.assertIn("may not ship apply-release state", err)

    def test_backup_dir_cannot_be_shipped(self):
        d = self.hostile_release(".agents/release-backup/x", payload_in_release=True)
        rc, out, err = self.run_cli("plan", str(d))
        self.assertEqual(rc, 2)
        self.assertIn("may not ship apply-release state", err)

    def test_git_internals_and_windows_device_names_are_refused(self):
        for bad in (".git/hooks/pre-commit", ".GIT/config", "docs/NUL", "docs/con.txt", "aux.md", "docs/LPT1.log"):
            d = self.hostile_release(bad)
            self.assert_refused(d, self.tmp / "outside.txt", "unsafe path")
        self.assertFalse((self.root / ".git/hooks/pre-commit").exists())


def tree_bytes(root):
    """Every file under root except git internals and the backup folder."""
    out = {}
    for dirpath, dirnames, names in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != ".git"]
        for n in names:
            rel = Path(dirpath, n).relative_to(root).as_posix()
            if not rel.startswith(".agents/release-backup/"):
                out[rel] = Path(dirpath, n).read_bytes()
    return out


class Rollback(Base):
    """Rollback returns the exact pre-apply working tree, including edits the owner never committed."""

    DIRTY = AGENTS.replace("line 1", "line 1 UNCOMMITTED")

    def release2(self):
        files = edition_v1()
        self.install(1, files)
        files["AGENTS.md"] = (AGENTS.replace("line 8", "line 8 V2").encode(), "merge", "644")
        files["docs/new.md"] = (b"new in 2\n", "merge", "644")
        files["README.md"] = (b"# Readme\n\nintro v2\n", "merge", "644")
        return self.release(2, files)

    def test_rollback_before_finish_restores_uncommitted_edit(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        before = tree_bytes(self.root)
        self.ok("apply", str(d2))
        self.assertIn("line 8 V2", self.read("AGENTS.md"))
        self.assertIn("line 1 UNCOMMITTED", self.read("AGENTS.md"))
        out = self.ok("rollback")
        self.assertIn("AGENTS.md", out["restored"])
        self.assertIn("docs/new.md", out["deleted"])
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY)
        self.assertEqual(tree_bytes(self.root), before)
        self.assertEqual(self.git("status", "--porcelain").splitlines(), [" M AGENTS.md"])
        self.assertIsNone(self.state()["in_progress"])
        self.assertEqual(self.state()["release"], 1)
        meta = json.loads(self.read(".agents/release-backup/2/backup.json"))
        self.assertTrue(meta["rolled_back"])
        self.assertEqual(self.ok("status")["release"], 1)

    def test_rollback_after_finish_restores_pre_apply_tree(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        before = tree_bytes(self.root)
        self.ok("apply", str(d2))
        self.ok("finish")
        head = self.git("rev-parse", "HEAD").strip()
        log = self.git("log", "--format=%H")
        self.assertEqual(self.git("log", "-1", "--format=%s").strip(), "apply Release 2")
        out = self.ok("rollback")
        self.assertEqual(out["release"], 2)
        self.assertEqual(tree_bytes(self.root), before)
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY)
        self.assertFalse((self.root / "docs/new.md").exists())
        self.assertEqual(self.state()["release"], 1)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), head)
        self.assertEqual(self.git("log", "--format=%H"), log)
        self.git("rev-parse", "--verify", "refs/releases/2")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), "")
        # Applying again works: the backup folder never blocks or gets committed.
        self.ok("apply", str(d2))
        self.ok("finish")
        committed = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertFalse([p for p in committed if p.startswith(".agents/release-backup")])

    def test_interrupted_apply_backup_keeps_true_pre_apply_bytes(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        before = tree_bytes(self.root)
        real = Path.write_bytes
        writes = []

        def crash(path, data):
            n = real(path, data)
            if path.name == "AGENTS.md" and ".agents" not in path.parts:
                writes.append(path)
                raise KeyboardInterrupt
            return n

        with mock.patch.object(Path, "write_bytes", crash):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("apply", str(d2))
        self.assertTrue(writes)
        self.assertIn("line 8 V2", self.read("AGENTS.md"))
        self.ok("apply", str(d2))
        self.assertEqual((self.root / ".agents/release-backup/2/files/AGENTS.md").read_bytes(), self.DIRTY.encode())
        self.ok("rollback")
        self.assertEqual(tree_bytes(self.root), before)

    def test_rollback_refuses_changed_file_unless_forced(self):
        d2 = self.release2()
        self.ok("apply", str(d2))
        self.ok("finish")
        later = self.read("README.md") + "owner wrote this after the apply\n"
        self.write("README.md", later)
        rc, out, err = self.run_cli("rollback")
        self.assertEqual(rc, 2)
        self.assertIn("README.md", err)
        self.assertIn("--force", err)
        self.assertEqual(self.read("README.md"), later)
        out = self.ok("rollback", "--force")
        self.assertIn("README.md", out["restored"])
        self.assertEqual(self.read("README.md"), "# Readme\n\nintro\n")
        self.assertEqual((self.root / ".agents/release-backup/2/rolled-back/README.md").read_text(encoding="utf-8"),
                         later)

    def interrupt_apply(self, d2):
        real = Path.write_bytes

        def crash(path, data):
            n = real(path, data)
            if path.name == "AGENTS.md" and ".agents" not in path.parts:
                raise KeyboardInterrupt
            return n

        with mock.patch.object(Path, "write_bytes", crash):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("apply", str(d2))

    def test_rollback_after_interrupted_apply_does_not_delete_owner_work(self):
        d2 = self.release2()
        self.interrupt_apply(d2)
        self.write("docs/new.md", "OWNER WORK\n")
        rc, out, err = self.run_cli("rollback")
        self.assertEqual(rc, 2, f"{out} {err}")
        self.assertIn("docs/new.md", err)
        self.assertEqual(self.read("docs/new.md"), "OWNER WORK\n")
        self.ok("rollback", "--force")
        self.assertFalse((self.root / "docs/new.md").exists())
        self.assertEqual((self.root / ".agents/release-backup/2/rolled-back/docs/new.md").read_text(encoding="utf-8"),
                         "OWNER WORK\n")

    def test_rerun_after_interrupted_rollback_finishes_it_and_not_the_previous_release(self):
        d2 = self.release2()
        self.ok("apply", str(d2))
        self.ok("finish")
        real = ar.Backup.save

        def interrupted_at_the_end(backup):
            if backup.meta.get("rolled_back"):
                raise KeyboardInterrupt
            return real(backup)

        with mock.patch.object(ar.Backup, "save", interrupted_at_the_end):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("rollback")
        self.assertEqual(self.state()["release"], 1, "the state file was already restored")
        out = self.ok("rollback")
        self.assertEqual(out["release"], 2, "the rerun must finish Release 2's rollback, not undo Release 1")
        self.assertEqual(self.state()["release"], 1)
        self.assertTrue((self.root / "AGENTS.md").is_file(), "Release 1's files are still installed")
        rc, out, err = self.run_cli("rollback")
        self.assertEqual(rc, 0, f"Release 1 may still be rolled back deliberately: {err}")
        self.assertEqual(out["release"], 1)

    def interrupt_rollback_after(self, restored_name):
        """Crash a rollback right after `restored_name` has been put back (shutil.copy2 is the restore step)."""
        real = shutil.copy2

        def crash(src, dst, *a, **k):
            out = real(src, dst, *a, **k)
            if Path(dst).name == restored_name:
                raise KeyboardInterrupt
            return out

        with mock.patch.object(shutil, "copy2", crash):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("rollback")

    def test_owner_edit_after_an_interrupted_rollback_is_not_overwritten_on_resume(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        self.ok("apply", str(d2))
        self.interrupt_rollback_after("AGENTS.md")
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY, "the first file was already restored")
        mine = self.DIRTY + "my work after the interruption\n"
        self.write("AGENTS.md", mine)
        rc, out, err = self.run_cli("rollback")
        self.assertEqual(rc, 2, f"{out} {err}")
        self.assertIn("AGENTS.md", err)
        self.assertEqual(self.read("AGENTS.md"), mine, "refused, so nothing was overwritten")
        self.ok("rollback", "--force")
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY)
        saved = self.root / ".agents/release-backup/2/rolled-back/AGENTS.md"
        self.assertEqual(saved.read_text(encoding="utf-8"), mine, "--force keeps the newer bytes")

    def test_resume_without_owner_edits_still_finishes(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        before = tree_bytes(self.root)
        self.ok("apply", str(d2))
        self.interrupt_rollback_after("AGENTS.md")
        self.ok("rollback")
        self.assertEqual(tree_bytes(self.root), before)

    def rescued(self, rel="AGENTS.md"):
        base = self.root / ".agents/release-backup/2/rolled-back" / rel
        found = sorted(base.parent.glob(base.name + "*"))
        return [p.read_text(encoding="utf-8") for p in found]

    def test_a_second_forced_pass_never_overwrites_the_first_rescue_copy(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        self.ok("apply", str(d2))
        version_a = self.DIRTY + "owner edit A, made after the apply\n"
        self.write("AGENTS.md", version_a)
        self.interrupt_rollback_after_force("AGENTS.md")
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY, "A was overwritten by the restore; only the rescue holds it")
        self.assertEqual(self.rescued(), [version_a])
        version_b = self.DIRTY + "owner edit B, made after the interruption\n"
        self.write("AGENTS.md", version_b)
        self.ok("rollback", "--force")
        self.assertEqual(self.read("AGENTS.md"), self.DIRTY)
        self.assertCountEqual(self.rescued(), [version_a, version_b], "both owner versions must survive")

    def test_a_repeated_forced_pass_with_the_same_bytes_saves_one_copy(self):
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        self.ok("apply", str(d2))
        mine = self.DIRTY + "same bytes both times\n"
        self.write("AGENTS.md", mine)
        self.interrupt_rollback_after_force("AGENTS.md")
        self.write("AGENTS.md", mine)
        self.ok("rollback", "--force")
        self.assertEqual(self.rescued(), [mine])

    def interrupt_rollback_after_force(self, restored_name):
        real = shutil.copy2

        def crash(src, dst, *a, **k):
            out = real(src, dst, *a, **k)
            if Path(dst).name == restored_name:
                raise KeyboardInterrupt
            return out

        with mock.patch.object(shutil, "copy2", crash):
            with self.assertRaises(KeyboardInterrupt):
                self.run_cli("rollback", "--force")

    def test_missing_backup_is_refused(self):
        self.install(1, edition_v1())
        shutil.rmtree(self.root / ".agents/release-backup/1")
        rc, out, err = self.run_cli("rollback")
        self.assertEqual(rc, 2)
        self.assertIn("no backup for Release 1", err)

    def test_first_install_rollback_removes_everything_it_added(self):
        self.write("notes.md", "mine\n")
        self.commit_all()
        before = tree_bytes(self.root)
        self.install(1, edition_v1())
        out = self.ok("rollback")
        self.assertIn(".agents/release-state.json", out["deleted"])
        self.assertEqual(tree_bytes(self.root), before)

    def test_later_release_ignores_backup_folder(self):
        d2 = self.release2()
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertTrue((self.root / ".agents/release-backup/2/backup.json").is_file())
        files = edition_v1()
        files["README.md"] = (b"# Readme\n\nintro v3\n", "merge", "644")
        d3 = self.release(3, files)
        self.assertEqual(self.ok("plan", str(d3))["dirty_blocking"], [])
        self.ok("apply", str(d3))
        self.ok("finish")
        committed = self.git("show", "--name-only", "--format=", "HEAD").split()
        self.assertIn("README.md", committed)
        self.assertFalse([p for p in committed if p.startswith(".agents/release-backup")])
        self.assertEqual(self.git("ls-files", ".agents/release-backup"), "")

    def test_without_git(self):
        shutil.rmtree(self.root / ".git")
        d2 = self.release2()
        self.write("AGENTS.md", self.DIRTY)
        before = tree_bytes(self.root)
        self.ok("apply", str(d2))
        self.ok("finish")
        self.assertTrue((self.root / ".agents/snapshots/2/AGENTS.md").is_file())
        self.ok("rollback")
        after = tree_bytes(self.root)
        self.assertEqual({k: v for k, v in after.items() if not k.startswith(".agents/snapshots/2/")}, before)

    def test_crlf_bytes_restored_exactly(self):
        d2 = self.release2()
        crlf = self.DIRTY.replace("\n", "\r\n").encode()
        self.write("AGENTS.md", crlf)
        self.ok("apply", str(d2))
        self.assertIn(b"line 8 V2\r\n", (self.root / "AGENTS.md").read_bytes())
        self.ok("rollback")
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), crlf)


if __name__ == "__main__":
    unittest.main()
