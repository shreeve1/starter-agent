#!/usr/bin/env python3
"""Deterministic audit for personal memory.

Checks that memory/index.md is in sync with the promoted topic files, that the
topic-ized folders (workflows, decisions) hold only topic subfolders plus a
generated index, that the two sub-indexes are current (`indexes.py` drift), and
that Client Memory under memory/clients/ is well formed and listed on its hub.
memory/candidates/ is not audited.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hubs  # noqa: E402
import indexes  # noqa: E402
import schema  # noqa: E402

PROMOTED_DIRS = ["preferences", "docs", "voice", "email", "guides"]
CROWDED_LIMIT = 15
CLIENT_KEYS = ["type", "client", "subject", "title", "verified", "source"]


def indexed_paths(memory_dir):
    """Paths linked from memory/index.md plus the two sub-indexes."""
    content = (memory_dir / "index.md").read_text(encoding="utf-8")
    backticks = re.findall(r"`(memory/[^`]+)`", content)
    links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", content)
    paths = {path for _, path in links} | set(backticks)
    topic_dirs = schema.load(memory_dir)["topic_dirs"]
    for d in topic_dirs:
        idx = memory_dir / d / "index.md"
        if idx.exists():
            text = idx.read_text(encoding="utf-8")
            paths |= {p for _, p in re.findall(r"\[([^\]]+)\]\(([^)]+)\)", text)}
    return paths


def audit_index(memory_dir, indexed):
    actual_files = []
    for d in PROMOTED_DIRS:
        p_dir = memory_dir / d
        if p_dir.exists():
            actual_files.extend(f"memory/{d}/{f.name}" for f in sorted(p_dir.glob("*.md")))
    missing = [f for f in actual_files if f not in indexed]
    stale = sorted(
        p for p in indexed
        if p.startswith("memory/") and not (memory_dir / p[len("memory/"):]).exists()
    )
    return missing, stale


def audit_topic_dirs(memory_dir, indexed):
    """Problems in workflows/decisions: flat promoted files, unknown topics, drift."""
    data = schema.load(memory_dir)
    topic_dirs = data["topic_dirs"]
    topics = data["topics"]
    problems = []
    for d in topic_dirs:
        base = memory_dir / d
        if not base.is_dir():
            continue
        for child in sorted(base.iterdir()):
            if child.is_file():
                if child.name not in ("index.md", ".gitkeep"):
                    problems.append(
                        f"memory/{d}/{child.name}: promoted file directly in {d}/ (move it into a topic folder)")
            elif child.is_dir() and child.name not in topics:
                problems.append(f"memory/{d}/{child.name}: topic folder not in {topics}")
        for topic in topics:
            tdir = base / topic
            if tdir.is_dir():
                for p in sorted(tdir.glob("*.md")):
                    rel = "memory/" + p.relative_to(memory_dir).as_posix()
                    if rel not in indexed:
                        problems.append(f"{rel}: missing from memory/{d}/index.md")
    changed, _ = indexes.drift(memory_dir)
    problems.extend(f"index drift: {p} (run indexes.py)" for p in changed)
    return problems


def audit_index_links(memory_dir):
    """memory/index.md must link each sub-index."""
    content = (memory_dir / "index.md").read_text(encoding="utf-8")
    topic_dirs = schema.load(memory_dir)["topic_dirs"]
    return [f"memory/index.md: missing link to memory/{d}/index.md"
            for d in topic_dirs if f"memory/{d}/index.md" not in content]


def crowded(memory_dir):
    """'crowded: memory/<dir> <n> files' lines for any non-topic memory folder
    holding more than CROWDED_LIMIT .md files directly (excluding index.md)."""
    topic_dirs = schema.load(memory_dir)["topic_dirs"]
    out = []
    for d in sorted(p for p in memory_dir.iterdir() if p.is_dir()):
        if d.name in topic_dirs:
            continue
        n = len([f for f in d.glob("*.md") if f.name != "index.md"])
        if n > CROWDED_LIMIT:
            out.append(f"crowded: memory/{d.name} {n} files")
    return out


def audit_clients(memory_dir, indexed):
    root = memory_dir / "clients"
    subjects = schema.load(memory_dir)["client_subjects"]
    problems = []
    for p in hubs.note_paths(memory_dir):
        rel = "memory/" + p.relative_to(memory_dir).as_posix()
        parts = p.relative_to(root).parts
        if len(parts) != 3:
            problems.append(f"{rel}: not at clients/<subject>/<short>/<slug>.md")
            continue
        subject, short, _ = parts
        fm = hubs.parse_frontmatter(p)
        missing = [k for k in CLIENT_KEYS if not fm.get(k)]
        if missing:
            problems.append(f"{rel}: missing frontmatter {missing}")
        if subject not in subjects:
            problems.append(f"{rel}: folder subject '{subject}' not in {subjects}")
        if fm.get("subject") and fm["subject"] not in subjects:
            problems.append(f"{rel}: subject '{fm['subject']}' not in {subjects}")
        if fm.get("subject") and fm["subject"] != subject:
            problems.append(f"{rel}: frontmatter subject '{fm['subject']}' != folder '{subject}'")
        if fm.get("client") and fm["client"] != short:
            problems.append(f"{rel}: frontmatter client '{fm['client']}' != folder '{short}'")
        if fm.get("type") and fm["type"] != "client-memory":
            problems.append(f"{rel}: type '{fm['type']}' != 'client-memory'")
        hub = root / hubs.HUB_DIR / f"{short}.md"
        if not hub.exists() or f"]({rel})" not in hub.read_text(encoding="utf-8"):
            problems.append(f"{rel}: not listed on hub memory/clients/{hubs.HUB_DIR}/{short}.md")
    changed, stale = hubs.drift(memory_dir)
    problems.extend(f"hub out of date: {p} (run hubs.py)" for p in changed)
    problems.extend(f"hub stale: {p} (run hubs.py)" for p in stale)
    hub_dir = root / hubs.HUB_DIR
    if hub_dir.is_dir():
        for h in sorted(hub_dir.glob("*.md")):
            rel = "memory/" + h.relative_to(memory_dir).as_posix()
            if rel not in indexed:
                problems.append(f"{rel}: hub has no memory/index.md row")
    return problems


def main():
    ap = argparse.ArgumentParser(description="Audit personal memory index and Client Memory.")
    ap.add_argument("--memory", default="memory", help="Memory directory root (default: memory)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("audit", help="Audit index alignment and Client Memory")
    sub.add_parser("crowded", help="Report memory folders holding more than 15 direct .md files")

    args = ap.parse_args()
    mem_path = Path(args.memory)

    if args.cmd == "crowded":
        for line in crowded(mem_path):
            print(line)
        sys.exit(0)

    if args.cmd != "audit":
        ap.error(f"unknown command: {args.cmd}")

    if not (mem_path / "index.md").exists():
        print("Alert: The memory index file (memory/index.md) was not found.")
        sys.exit(1)
    indexed = indexed_paths(mem_path)
    missing, stale = audit_index(mem_path, indexed)
    topic_problems = audit_topic_dirs(mem_path, indexed)
    index_link_problems = audit_index_links(mem_path)
    client_problems = audit_clients(mem_path, indexed)
    failed = False
    if missing or stale:
        print("Memory index out of sync: missing_from_index=%s stale_in_index=%s" % (missing, stale))
        failed = True
    if topic_problems:
        print("Topic folder problems:")
        for line in topic_problems:
            print(f"- {line}")
        failed = True
    if index_link_problems:
        print("Memory index structure problems:")
        for line in index_link_problems:
            print(f"- {line}")
        failed = True
    if client_problems:
        print("Client Memory problems:")
        for line in client_problems:
            print(f"- {line}")
        failed = True
    for line in crowded(mem_path):
        print(f"Warning: {line}")
    if failed:
        sys.exit(1)
    print("Success: Memory index and Client Memory are in sync.")
    sys.exit(0)


if __name__ == "__main__":
    main()