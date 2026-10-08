"""Synthetic I/O-only checks for method evidence finalization; no scientific work."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('withdrawal_method_audit', 'scripts/audit_v4_middle_withdrawal_design.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class EvidenceFailures(unittest.TestCase):
    def test_capture_preserves_keyboardinterrupt_and_systemexit(self):
        for kind in (KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind.__name__), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                sources, census = root/'sources.json', root/'census.json'
                sentinel = kind('synthetic capture interruption')
                original = m.hashes
                def injected(paths, *, phase=''):
                    values, errors, first = original(paths, phase=phase)
                    if phase == 'entry_inventory':
                        path = sorted(values)[0]
                        values.pop(path)
                        errors[path] = repr(sentinel)
                        return values, errors, sentinel
                    return values, errors, first
                with patch.object(m, 'hashes', side_effect=injected):
                    try:
                        m.run(sources, census)
                    except BaseException as caught:
                        self.assertIs(caught, sentinel)
                    else:
                        self.fail('interruption not propagated')
                result = m.read(sources)
                self.assertEqual(result['status'], 'failed')
                self.assertTrue(result['files_sha256'])
                self.assertTrue(result['input_read_errors_before'])
                self.assertEqual(result['capture_stages'][0]['phase'], 'entry_inventory')
                self.assertTrue(result['capture_stages'][0]['files_sha256'])
                self.assertEqual(m.read(census)['status'], 'failed')

    def test_bad_historical_hash_has_captured_source_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, census = Path(tmp)/'sources.json', Path(tmp)/'census.json'
            original = m.hashes
            def injected(paths, *, phase=''):
                values, errors, first = original(paths, phase=phase)
                if phase == 'first_method_epoch_archive':
                    path = sorted(values)[0]
                    values[path] = '0'*64
                return values, errors, first
            with patch.object(m, 'hashes', side_effect=injected):
                with self.assertRaises(ValueError):
                    m.run(sources, census)
            result = m.read(sources)
            self.assertEqual(result['status'], 'failed')
            self.assertEqual(result['capture_stages'][-1]['phase'], 'first_method_epoch_archive')
            self.assertIn('0'*64, result['capture_stages'][-1]['files_sha256'].values())
            self.assertTrue(result['files_sha256_after'])
            self.assertEqual(m.read(census)['status'], 'failed')

    def test_second_creation_race_does_not_overwrite_foreign_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, census = Path(tmp)/'sources.json', Path(tmp)/'census.json'
            original = m.reserve
            foreign = b'{"foreign":true}\n'
            def racing(path, value, owned):
                if path == census:
                    path.write_bytes(foreign)
                return original(path, value, owned)
            with patch.object(m, 'reserve', side_effect=racing):
                with self.assertRaises(FileExistsError):
                    m.run(sources, census)
            self.assertEqual(census.read_bytes(), foreign)
            self.assertEqual(m.read(sources)['status'], 'failed')
            self.assertNotIn('census_sha256', m.read(sources))

    def test_closing_interrupt_attempts_other_actions_and_propagates_original(self):
        for kind in (KeyboardInterrupt, SystemExit):
            with self.subTest(kind=kind.__name__), tempfile.TemporaryDirectory() as tmp:
                sources, census_path = Path(tmp)/'sources.json', Path(tmp)/'census.json'
                source = dict(status='running', files_sha256={'synthetic-input':'old'}, files_sha256_after={})
                census = dict(status='running', cases=[], environments=[])
                m.save(sources, source);m.save(census_path, census)
                sentinel = kind('synthetic closing interruption')
                with patch.object(m, 'hashes', return_value=({}, {'synthetic-input':repr(sentinel)}, sentinel)):
                    try:
                        m.finish_method(source, census, ['synthetic-input'], {sources,census_path},
                                        sources, census_path, time.monotonic(), True, None, lambda: None)
                    except BaseException as caught:
                        self.assertIs(caught, sentinel)
                    else:
                        self.fail('closing interruption not propagated')
                result = m.read(sources)
                self.assertEqual(result['status'], 'failed')
                self.assertEqual(m.read(census_path)['status'], 'failed')
                self.assertTrue(result['input_read_errors_after'])
                self.assertIn('bindings_and_budget', result['finalization_errors'])
                self.assertEqual(result['census_sha256'], m.digest(census_path))

    def test_prior_failure_wins_over_closing_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            sources, census_path = Path(tmp)/'sources.json', Path(tmp)/'census.json'
            source=dict(status='running', files_sha256={})
            census=dict(cases=[], environments=[])
            m.save(sources, source);m.save(census_path, census)
            first=KeyboardInterrupt('first');second=SystemExit('second')
            with patch.object(m, 'hashes', return_value=({}, {'later':repr(second)}, second)):
                try:
                    m.finish_method(source,census,[],{sources,census_path},sources,census_path,time.monotonic(),False,first,lambda:None)
                except BaseException as caught:
                    self.assertIs(caught,first)
                else:self.fail('first exception lost')
            self.assertEqual(m.read(sources)['error'],repr(first))


if __name__ == '__main__':
    unittest.main(verbosity=2)
