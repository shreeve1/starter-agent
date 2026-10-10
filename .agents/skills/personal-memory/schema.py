#!/usr/bin/env python3
"""Load memory/schema.json: the single Schema for subjects, topics and client dirs.

`load(memory_dir)` returns the schema dict. The file and its four keys are
required; a missing file or key exits with a clear one-line message naming the
path (and the key) instead of a traceback wall.
"""
import json
import sys
from pathlib import Path

REQUIRED_KEYS = ("client_subjects", "topics", "topic_dirs", "client_dirs")


def load(memory_dir):
    path = Path(memory_dir) / "schema.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        sys.exit(f"Alert: memory schema file not found: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"Alert: memory schema file {path} is not valid JSON: {exc.msg}")
    if not isinstance(data, dict):
        sys.exit(f"Alert: memory schema file {path} must contain a JSON object")
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        sys.exit(f"Alert: memory schema file {path} is missing key(s): {', '.join(missing)}")
    return data