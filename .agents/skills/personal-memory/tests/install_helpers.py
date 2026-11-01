from pathlib import Path


def is_starter_workspace(root: Path) -> bool:
    """Release markers distinguish a starter workspace from a shared skill host."""
    return (root / "MANIFEST.json").is_file() and (root / "START-HERE.md").is_file()
