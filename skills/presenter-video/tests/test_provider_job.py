"""Mock-only regressions for the optional provider ledger; no paid calls occur."""

import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('provider_job', Path(__file__).resolve().parents[1] / 'scripts/provider_job.py')
job = importlib.util.module_from_spec(spec)
spec.loader.exec_module(job)


class Provider:
    def __init__(self):
        self.calls = 0
        self.ids = {}
        self.status = 'pending'
        self.credentials = True
        self.timeout = False

    def ensure_ready(self):
        if not self.credentials:
            raise RuntimeError('missing credentials')

    def submit(self, request, key):
        self.calls += 1
        self.ids[key] = 'task-' + str(self.calls)
        if self.timeout:
            raise TimeoutError('response lost after remote acceptance')
        return self.ids[key]

    def lookup(self, key):
        return self.ids.get(key)

    def poll(self, task_id):
        assert task_id in self.ids.values()
        return self.status


class Jobs(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'job.json'
        self.provider = Provider()
        self.limits = dict(max_attempts=2, budget=200, cost_per_attempt=100)

    def step(self, request=None):
        return job.advance(self.path, request or {'model': 'mock', 'seconds': 3}, self.provider, **self.limits)

    def test_resume_polls_without_duplicate(self):
        """Resuming a pending or successful request cannot submit another paid task."""
        self.step()
        self.step()
        self.provider.status = 'succeeded'
        self.assertEqual(self.step()['attempts'][-1]['status'], 'succeeded')
        self.step()
        self.assertEqual(self.provider.calls, 1)

    def test_lost_submission_response_is_recovered(self):
        """A saved idempotency key recovers acceptance after a lost response."""
        self.provider.timeout = True
        with self.assertRaises(TimeoutError):
            self.step()
        self.provider.status = 'succeeded'
        self.assertEqual(self.step()['attempts'][-1]['status'], 'succeeded')
        self.assertEqual(self.provider.calls, 1)

    def test_unknown_submission_never_resubmits(self):
        """Unreconciled submissions preserve the attempt instead of risking another charge."""
        self.provider.timeout = True
        with self.assertRaises(TimeoutError):
            self.step()
        self.provider.ids.clear()
        for _ in range(3):
            with self.assertRaisesRegex(RuntimeError, 'outcome unknown'):
                self.step()
        self.assertEqual(self.provider.calls, 1)

    def test_missing_credentials_reserves_nothing(self):
        """Unavailable credentials cannot consume a budget reservation."""
        self.provider.credentials = False
        with self.assertRaisesRegex(RuntimeError, 'credentials'):
            self.step()
        self.assertFalse(self.path.exists())
        self.assertEqual(self.provider.calls, 0)

    def test_attempt_ceiling(self):
        """Confirmed failures cannot exceed the authorized attempt count."""
        self.provider.status = 'failed'
        for _ in range(2):
            self.step()
            self.step()
        with self.assertRaisesRegex(RuntimeError, 'ceiling'):
            self.step()
        self.assertEqual(self.provider.calls, 2)

    def test_budget_ceiling(self):
        """Conservative reservations cannot exceed the authorized budget."""
        self.limits['budget'] = 150
        self.provider.status = 'failed'
        self.step()
        self.step()
        with self.assertRaisesRegex(RuntimeError, 'ceiling'):
            self.step()
        self.assertEqual(self.provider.calls, 1)

    def test_changed_request_is_not_new_charge(self):
        """A changed request cannot reuse a ledger to silently start another task."""
        self.step()
        with self.assertRaises(ValueError):
            self.step({'model': 'different'})
        self.assertEqual(self.provider.calls, 1)

    def test_poll_failure_keeps_existing_id(self):
        """Failed polling retains the accepted task rather than resubmitting."""
        self.step()
        original = self.provider.poll
        self.provider.poll = lambda _: (_ for _ in ()).throw(TimeoutError())
        with self.assertRaises(TimeoutError):
            self.step()
        self.provider.poll = original
        self.step()
        self.assertEqual(self.provider.calls, 1)


if __name__ == '__main__':
    unittest.main()
