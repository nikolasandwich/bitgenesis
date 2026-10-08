"""Zero-science control diagnostic; preserve each parent commit time share."""
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))
sys.path.insert(0, str(Path.cwd() / 'tests'))
import test_v4_middle_withdrawal_verifier as tests

events = []
original = tests.verifier.Guard.commit
def measured(self, action):
    start = time.monotonic()
    event = dict(remaining_seconds=self.end-start, first_writer_share_seconds=(self.end-start)*.6)
    events.append(event)
    try:
        return original(self, action)
    except BaseException as error:
        event['exception'] = repr(error)
        raise
    finally:
        event['wall_seconds'] = time.monotonic()-start
        event['remaining_after_seconds'] = self.end-time.monotonic()

tests.verifier.Guard.commit = measured
suite = unittest.TestSuite(tests.PreflightBoundaryTests('test_run_interrupts_preflight_gate_and_process_with_failed_epoch') for _ in range(6))
result = unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps(dict(diagnostic='original 0.2s preflight test, six repetitions, no science', commit_events=events), sort_keys=True))
sys.exit(not result.wasSuccessful())
