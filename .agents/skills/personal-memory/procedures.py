#!/usr/bin/env python3
"""Read-only structural checks for shared procedures; approval remains an owner decision."""
import re
from datetime import date
from pathlib import Path

import hubs
import schema


def unsafe_path(path: Path) -> bool:
    return any(part.is_symlink() for part in (path, *path.parents))


def validate(path: Path, today: date | None = None) -> list[str]:
    today = today or date.today()
    if unsafe_path(path) or not path.is_file():
        return [f"{path}: expected a regular file without symlink components"]
    fields = hubs.parse_frontmatter(path)
    problems = []
    if fields.get('type') != 'procedure':
        problems.append(f"{path}: requires type: procedure")
    risk = fields.get('risk')
    if risk not in ('read-only', 'changes-state'):
        problems.append(f"{path}: risk must be read-only or changes-state")
    for key in ('approved', 'verified'):
        value = fields.get(key, '')
        try:
            if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value) or date.fromisoformat(value) > today:
                raise ValueError
        except ValueError:
            problems.append(f"{path}: {key} requires a real YYYY-MM-DD date, not in the future")
    sections = {}
    current = None
    fence = None
    text = hubs.read_note(path)
    if text.startswith('---\n'):
        end = text.find('\n---', 4)
        text = text[end + 4:] if end != -1 else ''
    for line in text.splitlines():
        marker = re.match(r'^ {0,3}(`{3,}|~{3,})', line)
        if marker:
            delimiter = marker[1]
            if fence is None:
                fence = delimiter
            elif delimiter[0] == fence[0] and len(delimiter) >= len(fence) and not line.strip().strip(delimiter[0]):
                fence = None
            continue
        if fence:
            continue
        heading = re.match(r'^(#{1,6})\s+(.+?)\s*#*\s*$', line)
        if heading:
            current = (len(heading[1]), heading[2])
            sections.setdefault(current, [])
        elif current:
            sections[current].append(line)
    required = [(2, 'Active memory'), (3, 'Prerequisites'), (3, 'Steps'),
                (3, 'Verify'), (2, 'Related'), (2, 'Notes')]
    if risk == 'changes-state':
        required += [(3, 'Approval'), (3, 'Recovery')]
    for key in required:
        if not '\n'.join(sections.get(key, [])).strip():
            problems.append(f"{path}: requires nonempty {'#' * key[0]} {key[1]}")
    if not re.search(r'^Trigger:\s*\S.*$', '\n'.join(sections.get((2, 'Active memory'), [])), re.M):
        problems.append(f"{path}: Active memory requires Trigger: text")
    if not re.search(r'^\s*\d+[.)]\s+\S', '\n'.join(sections.get((3, 'Steps'), [])), re.M):
        problems.append(f"{path}: Steps requires a numbered action")
    return problems


def audit(memory_dir: Path, today: date | None = None) -> list[str]:
    problems = []
    base = memory_dir / 'workflows'
    if unsafe_path(base):
        return [f"{base}: symlink components are not allowed"]
    for topic in schema.load(memory_dir)['topics']:
        folder = base / topic
        if unsafe_path(folder):
            problems.append(f"{folder}: symlink components are not allowed")
            continue
        for path in sorted(folder.glob('*.md')):
            if unsafe_path(path):
                problems.append(f"{path}: symlink components are not allowed")
            elif hubs.parse_frontmatter(path).get('type') == 'procedure':
                problems.extend(validate(path, today))
    return problems
