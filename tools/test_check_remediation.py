"""Synthetic coverage of the scoped similarity gate and reviewed exceptions."""
import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import check_remediation as gate


class RemediationGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.local = self.root / 'skills'
        self.corpus = self.root / 'corpus'
        self.local.mkdir()
        self.corpus.mkdir()
        self.original = ' '.join(f'observation_{n} describes a distinct measured event' for n in range(40))
        (self.corpus / 'old.md').write_text(self.original)
        (self.local / 'new.md').write_text(self.original)
        (self.local / 'outside.md').write_text(self.original)
        self.manifest = {'files': ['new.md'], 'thresholds': {'difflib': .35, 'shingle': .30}, 'reviewed_matches': {}}

    def run_audit(self):
        return gate.audit(self.local, [self.corpus], self.manifest)

    def test_identical_renamed_copy_is_a_failure_inside_scope(self):
        """A renamed legacy copy remains detectable without scanning unrelated files."""
        result = self.run_audit()
        self.assertEqual(result['files_checked'], 1)
        self.assertEqual(result['unreviewed_matches'], 1)
        self.assertTrue(result['matches'][0]['identical'])

    def test_clean_replacement_does_not_fail_for_outside_copy(self):
        """The gate applies to the reviewed remediation scope, not licensed bundles."""
        (self.local / 'new.md').write_text('A garden requires drainage and measured watering.')
        self.assertEqual(self.run_audit()['unreviewed_matches'], 0)

    def test_reviewed_match_is_reported_and_change_requires_review(self):
        """A compatibility exception is visible and cannot exempt later edits silently."""
        self.manifest['reviewed_matches']['new.md'] = {
            'sha256': hashlib.sha256((self.local / 'new.md').read_bytes()).hexdigest(),
            'reason': 'Synthetic approved interface fixture.',
        }
        result = self.run_audit()
        self.assertEqual(result['unreviewed_matches'], 0)
        self.assertTrue(result['matches'][0]['reviewed'])
        (self.local / 'new.md').write_text(self.original + '\nChanged material')
        with self.assertRaisesRegex(ValueError, 're-review'):
            self.run_audit()

    def test_missing_escape_duplicate_and_empty_scope_are_rejected(self):
        """A broken path list must not produce a misleading successful empty audit."""
        (self.root / 'escape.md').write_text('outside')
        for files in ([], ['missing.md'], ['../escape.md'], ['new.md', 'new.md']):
            with self.subTest(files=files), self.assertRaises(ValueError):
                self.manifest['files'] = files
                self.run_audit()

    def test_empty_corpus_is_rejected(self):
        """A missing baseline cannot certify that replacement text is distinct."""
        (self.corpus / 'old.md').unlink()
        with self.assertRaisesRegex(ValueError, 'empty corpus'):
            self.run_audit()

    def test_review_requires_scope_and_explanation(self):
        """Exceptions are file-specific review decisions, not blanket exclusions."""
        for name, reason in [('elsewhere.md', 'review'), ('new.md', '')]:
            self.manifest['reviewed_matches'] = {name: {'reason': reason, 'sha256': '0' * 64}}
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.run_audit()

    def test_absent_or_self_only_corpus_cannot_pass(self):
        """Comparing a file only with itself supplies no independent baseline."""
        with self.assertRaisesRegex(ValueError, 'at least one corpus'):
            gate.audit(self.local, [], self.manifest)
        (self.local / 'outside.md').unlink()
        with self.assertRaisesRegex(ValueError, 'empty effective corpus'):
            gate.audit(self.local, [self.local], self.manifest)

    def test_invalid_thresholds_cannot_disable_the_gate(self):
        """Nonfinite, out-of-range, boolean, or textual thresholds cannot hide copying."""
        for value in (2, -1, float('nan'), float('inf'), True, '0.35'):
            for metric in ('difflib', 'shingle'):
                self.manifest['thresholds'] = {'difflib': .35, 'shingle': .30}
                self.manifest['thresholds'][metric] = value
                with self.subTest(value=value, metric=metric), self.assertRaises(ValueError):
                    self.run_audit()

    def test_cli_requires_explicit_corpus(self):
        """Reject an omitted reference corpus instead of assuming a repository archive."""
        with contextlib.redirect_stderr(io.StringIO()) as errors, self.assertRaises(SystemExit) as caught:
            gate.main(['--local', str(self.local)])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn('--corpus', errors.getvalue())

    def test_cli_reports_failure_and_usage_errors(self):
        """CI receives nonzero status for copied text and malformed scope files."""
        path = self.root / 'manifest.json'
        path.write_text(json.dumps(self.manifest))
        args = ['--local', str(self.local), '--corpus', str(self.corpus), '--manifest', str(path)]
        with contextlib.redirect_stdout(io.StringIO()) as output:
            self.assertEqual(gate.main(args), 1)
        self.assertEqual(json.loads(output.getvalue())['unreviewed_matches'], 1)
        path.write_text('{}')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
            gate.main(args)
        self.assertEqual(caught.exception.code, 2)


if __name__ == '__main__':
    unittest.main()
