"""Small-world tests; never use the formal study cohort."""
import json
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bitgenesis.v4.hereditary_runner import run as source_run
from bitgenesis.v4 import exchange_branch as legacy
from scripts import history_exchange_branch as branch
from scripts import history_exchange_audit as auditor
from scripts.history_exchange_audit import audit


def read(path):
    return json.loads(path.read_text())


def write(path, value):
    path.write_text(json.dumps(value))


class HistoryExchangeTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def source(self, exchange=True):
        path = self.root / ('source-on' if exchange else 'source-off')
        source_run(path, 105000, steps=10, width=4, height=4,
                   mutation_per_thousand=100, leak=4, exchange=exchange)
        return path

    def rebind(self, output, name):
        meta = read(output/'metadata.json')
        meta['output_sha256'][name] = sha256((output/name).read_bytes()).hexdigest()
        write(output/'metadata.json', meta)

    def test_both_histories_and_switches_replay_isolation_and_legacy_bytes(self):
        for history in (False, True):
            source = self.source(history)
            before = {p.name:p.read_bytes() for p in source.iterdir()}
            tapes = [json.loads(s) for s in (source/'steps.jsonl').read_text().splitlines()][2:8]
            for exchange in (False, True):
                output = self.root/f'{history}-{exchange}'
                branch.run(output, source, 2, 6, exchange)
                meta = read(output/'metadata.json')
                self.assertEqual(meta['schema'], 'v4-history-exchange-branch-1')
                self.assertIs(meta['source_exchange'], history)
                expected_paths = list(Path(legacy.__file__).parent.glob('*.py')) + [Path(branch.__file__), Path(auditor.__file__)]
                repo = Path(branch.__file__).resolve().parents[1]
                self.assertEqual(meta['code_sha256'], {str(p.resolve().relative_to(repo)):sha256(p.read_bytes()).hexdigest() for p in expected_paths})
                rows = [json.loads(s) for s in (output/'steps.jsonl').read_text().splitlines()]
                if history == exchange:
                    self.assertEqual([r['physical'] for r in rows], tapes)
                for row, tape in zip(rows, tapes):
                    for key in ('directions', 'mutation_tickets'):
                        self.assertEqual(row['physical'][key], tape[key])
                    self.assertEqual([i['proposed'] for i in row['physical']['driven']['inputs']], [i['proposed'] for i in tape['driven']['inputs']])
                with patch.object(branch, 'step', side_effect=AssertionError('production physics')), patch.object(branch, 'follow', side_effect=AssertionError('production continuity')):
                    audit(output, source)
                if history:
                    old = self.root/f'legacy-{exchange}'
                    legacy.run(old, source, 2, 6, exchange)
                    for name in legacy.FILES:
                        self.assertEqual((old/name).read_bytes(), (output/name).read_bytes())
            self.assertEqual(before, {p.name:p.read_bytes() for p in source.iterdir()})
        with self.assertRaisesRegex(ValueError, 'retain exchange'):
            legacy.run(self.root/'legacy-off-source', self.root/'source-off', 0, 2)

    def test_independent_tampering_with_rebound_payload_hashes(self):
        source = self.source(False)
        for name in ('steps.jsonl', 'final.json', 'continuity.json', 'metadata.json'):
            output = self.root/name.replace('.', '-')
            branch.run(output, source, 0, 10, False)
            if name == 'steps.jsonl':
                rows = [json.loads(s) for s in (output/name).read_text().splitlines()]
                rows[0]['physical']['energy'] += 1
                (output/name).write_text(''.join(json.dumps(r)+'\n' for r in rows))
            else:
                value = read(output/name)
                if name == 'final.json':
                    value['parents'][0] = 0
                elif name == 'continuity.json':
                    value[0]['endpoint']['descendants'] += 1
                else:
                    value['source_exchange'] = True
                write(output/name, value)
            if name != 'metadata.json':
                self.rebind(output, name)
            with self.assertRaises(ValueError):
                audit(output, source)

    def test_strict_source_boolean_and_schema(self):
        source = self.source(False)
        for flag in (0, 1, None, 'false'):
            meta = read(source/'metadata.json')
            meta['exchange'] = flag
            write(source/'metadata.json', meta)
            output = self.root/str(flag)
            with self.assertRaisesRegex(ValueError, 'source exchange'):
                branch.run(output, source, 0, 2)
            self.assertEqual(read(output/'metadata.json')['status'], 'failed')
        meta['exchange'] = False
        write(source/'metadata.json', meta)
        output = self.root/'good'
        branch.run(output, source, 0, 2, False)
        for key, bad in (('source_exchange', 0), ('schema', 'v4-exchange-branch-1')):
            saved = (output/'metadata.json').read_bytes()
            meta = read(output/'metadata.json')
            meta[key] = bad
            write(output/'metadata.json', meta)
            with self.assertRaises(ValueError):
                audit(output, source)
            (output/'metadata.json').write_bytes(saved)

    def test_source_history_tampering_and_exclusive_failures(self):
        source = self.source(False)
        output = self.root/'good'
        branch.run(output, source, 0, 2, False)
        before = {p.name:p.read_bytes() for p in output.iterdir()}
        with self.assertRaises(FileExistsError):
            branch.run(output, source, 0, 2, True)
        self.assertEqual(before, {p.name:p.read_bytes() for p in output.iterdir()})
        with patch.object(branch, 'step', side_effect=RuntimeError('injected')):
            with self.assertRaisesRegex(RuntimeError, 'injected'):
                branch.run(self.root/'failed', source, 0, 2, False)
        self.assertEqual(read(self.root/'failed/metadata.json')['status'], 'failed')
        for target, src, anchor in [('short', source, 10), ('missing', self.root/'absent', 0)]:
            with self.assertRaises((ValueError, FileNotFoundError)):
                branch.run(self.root/target, src, anchor, 2)
            self.assertEqual(read(self.root/target/'metadata.json')['status'], 'failed')
        meta = read(source/'metadata.json')
        meta['exchange'] = True
        write(source/'metadata.json', meta)
        with self.assertRaises(ValueError):
            audit(output, source)
        with self.assertRaises(ValueError):
            branch.run(self.root/'tampered-source', source, 0, 2)

    def test_source_records_cannot_be_forged_by_rehashing(self):
        source = self.source(False)
        output = self.root/'branch'
        branch.run(output, source, 0, 2, False)
        rows = [json.loads(s) for s in (source/'steps.jsonl').read_text().splitlines()]
        rows[0]['energy'] += 1
        (source/'steps.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
        self.rebind(source, 'steps.jsonl')
        meta = read(output/'metadata.json')
        meta['source_sha256'] = meta['source_sha256_after'] = branch.hashes(source)
        write(output/'metadata.json', meta)
        with self.assertRaises(ValueError):
            audit(output, source)
        with self.assertRaises(ValueError):
            branch.run(self.root/'forged', source, 0, 2, False)
        self.assertEqual(read(self.root/'forged/metadata.json')['status'], 'failed')

    def test_empty_world_both_histories_and_invalid_arguments(self):
        for history in (False, True):
            source = self.root/f'empty-{history}'
            source_run(source, 105001, steps=2, width=4, height=4,
                       occupancy=0, exchange=history)
            for current in (False, True):
                result = branch.run(self.root/f'empty-{history}-{current}', source, 0, 2, current)
                self.assertEqual(result['records'], [])
                self.assertIsNone(result['summary']['continuous_fraction'])
        for anchor, horizon, exchange in ((True, 1, True), (0, False, True), (0, 1, 1), (-1, 1, True)):
            with self.assertRaises(ValueError):
                branch.run(self.root/'invalid', source, anchor, horizon, exchange)
        self.assertFalse((self.root/'invalid').exists())
