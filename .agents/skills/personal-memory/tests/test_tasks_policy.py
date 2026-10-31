"""Template and install contracts; agent behavior is verified with disposable probes."""
import re
import unittest
from pathlib import Path

PM = Path(__file__).resolve().parents[1]
ROOT = PM.parents[2]


def markdown_blocks(path):
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^```markdown\n(.*?)^```", text, re.M | re.S)


class TaskTemplateTests(unittest.TestCase):
    def test_task_record_can_be_filled_without_design_documents(self):
        path = PM / "task-templates.md"
        self.assertTrue(path.is_file(), "Installed task template missing")
        blocks = markdown_blocks(path)
        record = blocks[0]
        for key in ("id", "title", "status", "created", "updated"):
            self.assertRegex(record, rf"(?m)^{key}: .+")
        for heading in ("Purpose", "Current position", "Next action", "References", "Progress", "Outcome", "Durable outputs"):
            self.assertIn("## " + heading, record)
        self.assertEqual(record.count("\n---"), 1)

    def test_empty_index_has_no_fictional_tasks(self):
        path = PM / "task-templates.md"
        self.assertTrue(path.is_file(), "Installed index template missing")
        index = markdown_blocks(path)[1]
        rows = [line for line in index.splitlines() if line.startswith("|")]
        self.assertEqual(len(rows), 2)
        self.assertEqual(len(rows[0].split("|")), 8)

    def test_supporting_formats_are_installed_and_fences_parse(self):
        path = PM / "supporting-templates.md"
        self.assertTrue(path.is_file(), "Installed supporting templates missing")
        blocks = markdown_blocks(path)
        self.assertEqual(len(blocks), 2)
        self.assertIn("## Still needed", blocks[0])
        self.assertIn("## Findings:", blocks[1])
        self.assertIn("## Questions", blocks[1])

    def test_operations_are_packaged_with_copied_skill(self):
        # A self-contained copy must contain the targets reached by its reader.
        for name in ("tasks.md", "task-templates.md", "supporting-templates.md"):
            self.assertTrue((PM / name).is_file(), name)
        for path in (PM / "tasks.md", PM / "task-templates.md", PM / "supporting-templates.md"):
            text = path.read_text(encoding="utf-8")
            self.assertEqual(sum(line.startswith("```") for line in text.splitlines()) % 2, 0)
            instructions = re.sub(r"^```.*?^```", "", text, flags=re.M | re.S)
            for target in re.findall(r"\]\(([^)]+\.md)\)", instructions):
                self.assertTrue((path.parent / target).is_file(), target)


if __name__ == "__main__":
    unittest.main()
