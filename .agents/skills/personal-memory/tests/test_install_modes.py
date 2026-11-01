"""A shared skill install does not own its host's workspace configuration."""

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PM = Path(__file__).resolve().parents[1]


class InstallModeTests(unittest.TestCase):
    def test_plain_description_is_valid_yaml_scalar(self):
        text = (PM / "SKILL.md").read_text(encoding="utf-8")
        description = next(line for line in text.splitlines() if line.startswith("description: "))
        value = description.removeprefix("description: ")
        self.assertNotIn(": ", value, "Plain YAML descriptions cannot contain mapping separators")
        self.assertIn("saved workspace tasks", value)

    def test_global_copy_does_not_require_host_workspace_upgrade(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            copied = root / ".agents/skills/personal-memory"
            shutil.copytree(PM, copied, ignore=shutil.ignore_patterns("__pycache__"))
            (root / "AGENTS.md").write_text("# Existing project\n", encoding="utf-8")
            (root / "memory").mkdir()
            for name in ("README.md", "TEMPLATES.md"):
                (root / "memory" / name).write_text("# Existing project format\n", encoding="utf-8")
            (root / ".gitignore").write_text("existing-output/\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "unittest",
                    "test_policy",
                    "test_tasks_policy",
                    "test_recovery",
                    "-q",
                ],
                cwd=copied / "tests",
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr[-5000:])
            self.assertEqual((root / "AGENTS.md").read_text(), "# Existing project\n")
            self.assertFalse((root / "tasks").exists())


if __name__ == "__main__":
    unittest.main()
