"""Shared procedures are structurally ready, not authorized by lint."""
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_rules import workspace, audit as full_audit
from test_indexes import run_script, INDEXES, GATE
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import procedures

TODAY = date(2026, 10, 30)
BODY = """## Active memory
Trigger: review a change

### Prerequisites
A proposed change is available.

### Steps
1. Read the proposed change.

### Verify
Summarize findings before editing.

## Related
None.

## Notes
Owner tested the read-only steps.
"""


def write_procedure(mem, risk='read-only', approved='2026-10-01', verified='2026-10-01', body=BODY):
    path = mem / 'workflows/projects/review.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f'---\ntype: procedure\ntitle: Review\nrisk: {risk}\napproved: {approved}\nverified: {verified}\n---\n{body}', encoding='utf-8')
    return path


class ProcedureTests(unittest.TestCase):
    def test_read_only_and_extra_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_procedure(Path(td))
            path.write_text(path.read_text().replace('type: procedure', 'extra: yes\ntype: procedure'))
            self.assertEqual(procedures.validate(path, TODAY), [])

    def test_missing_empty_sections_and_numbered_action(self):
        variants = [BODY.replace(section, '### Other') for section in
                    ('## Active memory', '### Prerequisites', '### Steps', '### Verify', '## Related', '## Notes')]
        variants += [BODY.replace('Trigger: review a change', 'Trigger:'), BODY.replace('1. Read the proposed change.', 'Read it.'),
                     BODY.replace('Summarize findings before editing.', ''), BODY.replace('None.', '')]
        for body in variants:
            with self.subTest(body=body), tempfile.TemporaryDirectory() as td:
                path = write_procedure(Path(td), body=body)
                before = path.read_bytes()
                self.assertTrue(procedures.validate(path, TODAY))
                self.assertEqual(path.read_bytes(), before)

    def test_changes_state_requires_approval_recovery(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_procedure(Path(td), risk='changes-state')
            self.assertTrue(procedures.validate(path, TODAY))
            path = write_procedure(Path(td), risk='changes-state', body=BODY.replace('## Related', '### Approval\nAsk now before publishing.\n\n### Recovery\nIrreversible; stop and escalate.\n\n## Related'))
            self.assertEqual(procedures.validate(path, TODAY), [])

    def test_dates_and_risk(self):
        for kwargs in ({'risk': 'maybe'}, {'approved': ''}, {'verified': ''}, {'approved': '2026-10-31'},
                       {'verified': '2026-02-30'}, {'approved': '20261001'}):
            with self.subTest(kwargs=kwargs), tempfile.TemporaryDirectory() as td:
                path = write_procedure(Path(td), **kwargs)
                self.assertTrue(procedures.validate(path, TODAY))

    def test_fenced_examples_do_not_count(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_procedure(Path(td), body='```markdown\n' + BODY + '\n```')
            self.assertTrue(procedures.validate(path, TODAY))

    def test_bom_crlf(self):
        with tempfile.TemporaryDirectory() as td:
            path = write_procedure(Path(td))
            path.write_bytes(b'\xef\xbb\xbf' + path.read_bytes().replace(b'\n', b'\r\n'))
            self.assertEqual(procedures.validate(path, TODAY), [])

    def test_cli_and_full_audit_reject_legacy_without_writes(self):
        with tempfile.TemporaryDirectory() as td:
            mem = workspace(td, [])
            path = write_procedure(mem, approved='', verified='', body='## Active memory\nTrigger: test\n### Steps\n1. Do it.\n')
            run_script(INDEXES, mem)
            before = {p: p.read_bytes() for p in mem.rglob('*') if p.is_file()}
            for command in ('procedures', 'audit'):
                proc = run_script(GATE, mem, command)
                self.assertEqual(proc.returncode, 1, proc.stdout)
                self.assertIn('Procedure problems:', proc.stdout)
                self.assertIn('review.md', proc.stdout)
            self.assertEqual(before, {p: p.read_bytes() for p in mem.rglob('*') if p.is_file()})

    def test_full_audit_keeps_unrelated_findings(self):
        with tempfile.TemporaryDirectory() as td:
            mem = workspace(td, [])
            write_procedure(mem, body='Incomplete.')
            run_script(INDEXES, mem)
            note = mem / 'docs/unindexed.md'
            note.parent.mkdir()
            note.write_text('Unindexed ordinary note.')
            result = run_script(GATE, mem, 'audit')
            self.assertIn('Procedure problems:', result.stdout)
            self.assertIn('missing_from_index', result.stdout)

    def test_empty_and_ordinary_notes(self):
        with tempfile.TemporaryDirectory() as td:
            mem = workspace(td, [])
            path = write_procedure(mem)
            path.write_text('---\ntype: workflow\n---\nordinary note')
            self.assertEqual(procedures.audit(mem, TODAY), [])
            path.unlink()
            self.assertEqual(procedures.audit(mem, TODAY), [])
            self.assertEqual(run_script(GATE, mem, 'procedures').returncode, 0)

    def test_symlink_not_read(self):
        with tempfile.TemporaryDirectory() as td:
            mem = workspace(td, [])
            path = write_procedure(mem)
            outside = mem.parent / 'outside.md'
            outside.write_bytes(path.read_bytes())
            path.unlink()
            try:
                path.symlink_to(outside)
            except OSError as exc:
                self.skipTest(str(exc))
            self.assertTrue(procedures.audit(mem, TODAY))
            self.assertTrue(procedures.validate(path, TODAY))


if __name__ == '__main__':
    unittest.main()
