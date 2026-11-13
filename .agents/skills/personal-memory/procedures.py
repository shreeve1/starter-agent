#!/usr/bin/env python3
"""Read-only structural checks for shared procedures; approval remains an owner decision."""

import re
from datetime import date
from pathlib import Path

import hubs
import schema

NOT_UNDO = ("<", "not known", "none", "n/a", "...", "not possible", "cannot", "irreversible")
UNDO_LINE = re.compile(r"^\s*-\s+Steps?\s+(\d+(?:\s*(?:,|and)\s*\d+)*)\s*:\s*(.*)$", re.I)


def unsafe_path(path: Path, boundary: Path | None = None) -> bool:
    path = path.absolute()
    boundary = boundary.absolute() if boundary is not None else path.parents[2]
    current = path
    while True:
        if current.is_symlink():
            return True
        if current == boundary:
            return False
        current = current.parent


def real_date(value: str, today: date) -> bool:
    try:
        return (
            bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)) and date.fromisoformat(value) <= today
        )
    except ValueError:
        return False


def parse_sections(path: Path) -> tuple[dict, dict]:
    fields = hubs.parse_frontmatter(path)
    sections = {}
    current = None
    parent = None
    fence = None
    text = hubs.read_note(path)
    if text.startswith("---\n"):
        end = text.find("\n---", 4)
        text = text[end + 4 :] if end != -1 else ""
    for line in text.splitlines():
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            delimiter = marker[1]
            if fence is None:
                fence = delimiter
            elif (
                delimiter[0] == fence[0]
                and len(delimiter) >= len(fence)
                and not line.strip().strip(delimiter[0])
            ):
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        if heading:
            level = len(heading[1])
            if level <= 2:
                parent = heading[2] if level == 2 else None
            current = (level, heading[2])
            if level != 2 and not (level == 3 and parent == "Active memory"):
                current = None
            if current:
                sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    return fields, sections


def step_ids(sections: dict) -> set[str]:
    found = set()
    for line in sections.get((3, "Steps"), []):
        m = re.match(r"^\s*(\d+)[.)]\s+\S", line)
        if m:
            found.add(m[1])
    return found


def _recovery_lines(sections: dict):
    for line in sections.get((3, "Recovery"), []):
        m = UNDO_LINE.match(line)
        if m:
            yield re.findall(r"\d+", m[1]), m[2].strip()


def undo_steps(sections: dict) -> set[str]:
    return {
        step
        for nums, undo in _recovery_lines(sections)
        if not undo.lower().startswith(NOT_UNDO)
        for step in nums
    }


def recovery_steps(sections: dict) -> set[str]:
    return {step for nums, _ in _recovery_lines(sections) for step in nums}


def trusted_step_ids(value: str) -> list[str] | None:
    if not re.fullmatch(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]", value):
        return None
    return re.findall(r"\d+", value)


def trust_problems(path: Path, fields: dict, sections: dict, today: date) -> list[str]:
    problems = []
    raw = fields.get("trusted_steps", "")
    ids = trusted_step_ids(raw)
    if raw and ids is None:
        problems.append(f"{path}: trusted_steps requires [<n>, ...] with whole step numbers")
    if not fields.get("trusted", ""):
        return problems
    if fields.get("status") != "promoted":
        problems.append(f"{path}: trusted requires status: promoted")
    if fields.get("risk") != "changes-state":
        problems.append(f"{path}: trusted requires risk: changes-state")
    if not real_date(fields["trusted"], today):
        problems.append(f"{path}: trusted requires a real YYYY-MM-DD date, not in the future")
    if not ids:
        problems.append(f"{path}: trusted requires trusted_steps: [<n>, ...]")
        return problems
    numbered = step_ids(sections)
    undo = undo_steps(sections)
    for step in ids:
        if step not in numbered:
            problems.append(f"{path}: trusted step {step} is not a numbered step")
        elif step not in undo:
            problems.append(f"{path}: trusted step {step} has no real undo under ### Recovery")
    return problems


def validate(path: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    if unsafe_path(path) or not path.is_file():
        return [f"{path}: expected a regular file without symlink components"]
    fields, sections = parse_sections(path)
    problems = []
    if fields.get("type") != "procedure":
        problems.append(f"{path}: requires type: procedure")
    risk = fields.get("risk")
    if risk not in ("read-only", "changes-state"):
        problems.append(f"{path}: risk must be read-only or changes-state")
    draft = fields.get("status") == "draft"
    for key in ("approved", "verified"):
        value = fields.get(key, "")
        if draft and not value:
            continue
        if not real_date(value, today):
            problems.append(f"{path}: {key} requires a real YYYY-MM-DD date, not in the future")
    required = [
        (2, "Active memory"),
        (3, "Prerequisites"),
        (3, "Steps"),
        (3, "Verify"),
        (2, "Related"),
        (2, "Notes"),
    ]
    if risk == "changes-state":
        required += [(3, "Approval"), (3, "Recovery")]
    if draft:
        required.append((3, "Gaps"))
    for key in required:
        if not "\n".join(sections.get(key, [])).strip():
            problems.append(f"{path}: requires nonempty {'#' * key[0]} {key[1]}")
    if not re.search(
        r"^Trigger:[ \t]*[^\s].*$", "\n".join(sections.get((2, "Active memory"), [])), re.M
    ):
        problems.append(f"{path}: Active memory requires Trigger: text")
    if not re.search(r"^\s*\d+[.)]\s+\S", "\n".join(sections.get((3, "Steps"), [])), re.M):
        problems.append(f"{path}: Steps requires a numbered action")
    problems.extend(trust_problems(path, fields, sections, today))
    return problems


def selected(memory_dir: Path, relative_path: str, today: date | None = None) -> list[str]:
    parts = relative_path.split("/")
    topics = schema.load(memory_dir)["topics"]
    if (
        len(parts) != 4
        or parts[:2] != ["memory", "workflows"]
        or not isinstance(topics, list)
        or parts[2] not in topics
        or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", parts[2])
        or not parts[3].endswith(".md")
        or parts[3] in (".", "..")
        or "\\" in relative_path
        or ":" in relative_path
    ):
        return [f"{relative_path}: invalid procedure target"]
    path = memory_dir.joinpath(*parts[1:])
    return validate(path, today)


def audit(memory_dir: Path, today: date | None = None) -> list[str]:
    problems = []
    base = memory_dir / "workflows"
    if unsafe_path(base, memory_dir):
        return [f"{base}: symlink components are not allowed"]
    topics = schema.load(memory_dir)["topics"]
    if not isinstance(topics, list):
        return [f"{base}: invalid workflow topic list"]
    for topic in topics:
        if not isinstance(topic, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", topic):
            problems.append(f"{base}: invalid workflow topic {topic!r}")
            continue
        folder = base / topic
        if unsafe_path(folder, memory_dir):
            problems.append(f"{folder}: symlink components are not allowed")
            continue
        for path in sorted(folder.glob("*.md")):
            if unsafe_path(path, memory_dir):
                problems.append(f"{path}: symlink components are not allowed")
            elif hubs.parse_frontmatter(path).get("type") == "procedure":
                problems.extend(validate(path, today))
    return problems
