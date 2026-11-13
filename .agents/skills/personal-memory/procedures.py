#!/usr/bin/env python3
"""Read-only structural checks for shared procedures; approval remains an owner decision."""

import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import NamedTuple

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


RESULTS = ("pass", "fail", "partial", "skipped")
MARKER = re.compile(r"^\d{4}-\d{2}-\d{2} after \S+$")


class RunRow(NamedTuple):
    ref: str
    date: str
    step: str
    result: str


def runs_path(path: Path) -> Path:
    return path.with_name(path.stem + ".runs.md")


def read_runs(path: Path) -> tuple[dict, list[RunRow], list[str]]:
    text = hubs.read_note(path)
    fields = {}
    body = text
    end = text.find("\n---", 4)
    if text.startswith("---\n") and end != -1:
        fields = hubs.parse_frontmatter(path)
        body = text[end + 4 :]
    problems = []
    if not fields:
        problems.append(f"{path}: runs file has no frontmatter")
    rows = []
    in_section = False
    seen = False
    for line in body.splitlines():
        heading = re.match(r"^##\s+(.+?)\s*$", line)
        if heading:
            in_section = heading[1] == "Worked runs"
            seen = seen or in_section
            continue
        if not in_section or not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells[0] == "Ref" or all(re.fullmatch(r":?-+:?", c) for c in cells):
            continue
        if len(cells) != 6:
            problems.append(f"{path}: row is not 6 cells: {line.strip()}")
            continue
        rows.append(RunRow(cells[0], cells[1], cells[2], cells[5]))
    if not seen:
        problems.append(f"{path}: runs file needs a ## Worked runs table")
    return fields, rows, problems


def _marker_ref(value: str, refs: set[str]) -> str | None:
    if not MARKER.fullmatch(value):
        return None
    ref = value.split(" after ", 1)[1]
    return ref if ref in refs else None


def counted(fields: dict, rows: list[RunRow]) -> list[RunRow]:
    if "renumbered" not in fields:
        return rows
    ref = _marker_ref(fields["renumbered"], {r.ref for r in rows})
    if ref is None:
        return []
    last = max(i for i, r in enumerate(rows) if r.ref == ref)
    return rows[last + 1 :]


def runs_problems(runs_file: Path, memory_dir: Path) -> list[str]:
    name = runs_file.name
    try:
        rel = runs_file.absolute().relative_to(memory_dir.absolute()).as_posix()
    except ValueError:
        return [f"{runs_file}: runs file must sit inside the memory folder"]
    if unsafe_path(runs_file, memory_dir) or not runs_file.is_file():
        return [f"{runs_file}: expected a regular file without symlink components"]
    fields, rows, problems = read_runs(runs_file)
    if not fields:
        return problems
    if fields.get("type") != "worked-runs":
        problems.append(f"{runs_file}: type must be worked-runs")
    expected = "memory/" + rel[: -len(".runs.md")] + ".md"
    if fields.get("procedure") != expected:
        return problems + [f"{runs_file}: procedure must be {expected}"]
    sibling = runs_file.with_name(name[: -len(".runs.md")] + ".md")
    if unsafe_path(sibling, memory_dir) or not sibling.is_file():
        return problems + [f"{runs_file}: no procedure beside it at {expected}"]
    _, sections = parse_sections(sibling)
    numbered = step_ids(sections)
    if "renumbered" in fields and _marker_ref(fields["renumbered"], {r.ref for r in rows}) is None:
        marker = fields["renumbered"]
        problems.append(f"{runs_file}: bad renumbered marker: {marker}")
    for row in counted(fields, rows):
        if row.result not in RESULTS:
            problems.append(
                f"{runs_file}: {row.ref} result {row.result!r} must be one of {', '.join(RESULTS)}"
            )
        if row.step not in numbered:
            problems.append(
                f"{runs_file}: {row.ref} step {row.step} is not a step in the procedure; "
                "if a Correction renumbered the steps, add renumbered: <date> after <last old Ref> to the runs file"
            )
    return problems


def target(memory_dir: Path, relative_path: str) -> Path | None:
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
        return None
    return memory_dir.joinpath(*parts[1:])


def selected(memory_dir: Path, relative_path: str, today: date | None = None) -> list[str]:
    path = target(memory_dir, relative_path)
    if path is None:
        return [f"{relative_path}: invalid procedure target"]
    problems = validate(path, today)
    runs = runs_path(path)
    if runs.exists():
        problems += runs_problems(runs, memory_dir)
    return problems


@dataclass
class StepStatus:
    step: str
    state: str
    reason: str
    passes: list[str]


@dataclass
class Ladder:
    path: str
    rung: int
    rung_name: str
    runs: list[tuple[str, bool]]
    steps: list[StepStatus]
    skipped_rows: list[str]
    next_move: str


def _and_list(items: list[str]) -> str:
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + " and " + items[-1]


def ladder(memory_dir: Path, relative_path: str, today: date | None = None) -> Ladder:
    path = target(memory_dir, relative_path)
    if path is None:
        raise ValueError(f"{relative_path}: invalid procedure target")
    problems = validate(path, today)
    if problems:
        raise ValueError("\n".join(problems))
    fields, sections = parse_sections(path)
    draft = fields.get("status") == "draft"
    notes = "\n".join(sections.get((2, "Notes"), []))
    numbered = step_ids(sections)
    undo = undo_steps(sections)
    change = sorted(recovery_steps(sections) & numbered, key=int)

    run_fields, rows, skipped = {}, [], []
    runs_file = runs_path(path)
    if runs_file.exists():
        run_fields, rows, skipped = read_runs(runs_file)
        if not run_fields:
            rows = []
    if (
        "renumbered" in run_fields
        and _marker_ref(run_fields["renumbered"], {r.ref for r in rows}) is None
    ):
        skipped.append(f"bad renumbered marker: {run_fields['renumbered']}")

    trust_date = fields.get("trusted", "")
    revoked = re.findall(r"^- (\d{4}-\d{2}-\d{2}): trust revoked", notes, re.M)
    last_change = max(revoked + ([trust_date] if trust_date else []), default="")
    trusted_ids = (
        set(trusted_step_ids(fields.get("trusted_steps", "")) or []) if trust_date else set()
    )

    grouped: dict[str, dict[str, RunRow]] = {}
    for row in counted(run_fields, rows):
        if last_change and not (row.date and row.date >= last_change):
            continue
        if row.result not in RESULTS or row.step not in numbered:
            skipped.append(f"{row.ref} step {row.step}: {row.result}")
            continue
        grouped.setdefault(row.ref, {})[row.step] = row

    runs = []
    for ref, by_step in grouped.items():
        clean = all(row.result != "fail" for row in by_step.values()) and all(
            by_step[s].result in ("pass", "skipped") for s in change if s in by_step
        )
        runs.append((ref, clean))

    steps = []
    qualifying = []
    for s in change:
        if s in trusted_ids:
            steps.append(StepStatus(s, "trusted", "", []))
            continue
        vals = [
            by_step[s]
            for by_step in grouped.values()
            if s in by_step and by_step[s].result != "skipped"
        ]
        passes = [row.ref for row in vals if row.result == "pass"]
        if s not in undo:
            state, reason = "blocked", "no known undo"
        elif vals and vals[-1].result != "pass":
            state, reason = "blocked", f"last result {vals[-1].result} on {vals[-1].ref}"
        else:
            trailing = 0
            for row in reversed(vals):
                if row.result != "pass":
                    break
                trailing += 1
            if trailing < 3:
                state, reason = "blocked", f"{trailing} clean pass(es) of 3"
            elif draft:
                state, reason = "blocked", "procedure is draft"
            else:
                state, reason = "qualifies", ""
        if state == "qualifies":
            qualifying.append(s)
        steps.append(StepStatus(s, state, reason, passes))

    if trust_date:
        rung = 3
    elif draft:
        rung = 0
    elif re.search(r"^- \d{4}-\d{2}-\d{2}: trust suggested", notes, re.M):
        rung = 2
    else:
        rung = 1
    rung_name = ("proposed", "reviewed", "trust offered", "trusted")[rung]

    if draft and not runs:
        next_move = "next: a clean run under the current numbering"
    elif draft and runs[-1][1]:
        next_move = "next: mark it reviewed (the owner's yes in a run review)"
    elif draft:
        next_move = "next: fix what differed, then a clean run"
    elif qualifying:
        next_move = f"next: trust steps {_and_list(qualifying)} (the owner's yes)"
    else:
        next_move = "next: nothing to offer yet"
    return Ladder(relative_path, rung, rung_name, runs, steps, skipped, next_move)


def render(report: Ladder) -> str:
    lines = [
        f"{report.path}: rung {report.rung} {report.rung_name}",
        f"Counted runs: {len(report.runs)}",
    ]
    for ref, clean in report.runs:
        lines.append(f"  {ref}: {'clean' if clean else 'not clean'}")
    for step in report.steps:
        extra = f": {step.reason}" if step.reason else ""
        lines.append(f"  step {step.step}: {step.state}{extra}")
        if step.passes and step.state != "trusted":
            lines.append(f"    passes: {', '.join(step.passes)}")
    for row in report.skipped_rows:
        lines.append(f"  skipped row: {row}")
    lines.append(report.next_move)
    return "\n".join(lines)


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
            elif path.name.endswith(".runs.md"):
                problems.extend(runs_problems(path, memory_dir))
            elif hubs.parse_frontmatter(path).get("type") == "procedure":
                problems.extend(validate(path, today))
    return problems
