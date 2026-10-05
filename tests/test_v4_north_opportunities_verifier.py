import json
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import verify_v4_north_opportunities as v


def fixture():
    return json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())


class NorthVerifierTests(unittest.TestCase):
    def test_actual_replay_actor_identity_and_tamper(self):
        case = fixture()
        record = v.recount(case, 'homogeneous')
        self.assertEqual(len(record['steps']), 32)
        self.assertEqual([a['identity'] for a in record['steps'][0]], [0, 1, 2])
        self.assertEqual([a['root'] for a in record['steps'][0]], [0, 1, 2])
        for mutate in (
            lambda c: c['rows'][0]['physical']['driven']['inputs'][85].update(accepted=1),
            lambda c: c['rows'][0]['physical']['interaction_units'][85].update(energy=1),
            lambda c: c['rows'][0]['site_ids'].__setitem__(85, 999),
            lambda c: c['final']['parents'].__setitem__(3, 2),
        ):
            bad = deepcopy(case); mutate(bad)
            with self.assertRaises(ValueError): v.recount(bad, 'homogeneous')

    def test_aggregate_order_schema_and_joint_masks(self):
        rows = []
        for genotype, mode, exchange, seed in v.GRID:
            actor = dict(tick=1, site=85, identity=0, root=0, direction=3,
                proposed=8, accepted=0, energy_before=64, energy_interaction=15,
                target=69, target_occupied=True, raw_available=0, reason='energy',
                encoded_material=0, formed_material=None)
            rows.append(dict(genotype=genotype, mode=mode, exchange=exchange, seed=seed,
                             steps=[[actor]] + [[] for _ in range(31)]))
        cells = v.aggregate(rows)
        self.assertEqual(len(cells), 12)
        self.assertEqual(cells[0]['all']['north_predicates']['7'], 20)
        self.assertEqual(list(cells[0]['all']['reasons']), list(v.REASONS))
        for change in ('order', 'extra', 'bool'):
            bad = deepcopy(rows)
            if change == 'order': bad[:2] = reversed(bad[:2])
            elif change == 'extra': bad[0]['steps'][0][0]['extra'] = 0
            else: bad[0]['steps'][0][0]['proposed'] = True
            with self.assertRaises(ValueError): v.aggregate(bad)


class NorthMainTests(unittest.TestCase):
    def test_proof_hashes_and_failure_evidence(self):
        import hashlib
        import sys
        import types
        from tempfile import TemporaryDirectory
        from unittest.mock import patch
        digest = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
        for corrupt in (None, 'record', 'summary', 'binding', 'early'):
            with self.subTest(corrupt=corrupt), TemporaryDirectory() as directory:
                root = Path(directory)
                sources = []
                records = []
                for i, (genotype, mode, exchange, seed) in enumerate(v.GRID):
                    path = root/f'input-{i}.json'
                    path.write_text(json.dumps(dict(mode=mode, exchange=exchange, seed=seed)))
                    sources.append((genotype, path))
                    records.append(dict(genotype=genotype, mode=mode, exchange=exchange, seed=seed, steps=[[] for _ in range(32)]))
                output = root/'output'; output.mkdir()
                bound = {str(path): digest(path) for _, path in sources}
                for i in range(148):
                    path = root/f'other-{i}'; path.write_text(str(i)); bound[str(path)] = digest(path)
                bound['scripts/verify_v4_north_opportunities.py'] = digest(v.__file__)
                if corrupt == 'binding': bound['scripts/verify_v4_north_opportunities.py'] = '0'*64
                saved = deepcopy(records)
                if corrupt == 'record': saved[0]['steps'][0] = [{'extra': 1}]
                (output/'records.json').write_text(json.dumps(saved))
                summary = v.aggregate(records)
                if corrupt == 'summary': summary[0]['all']['north_predicates']['7'] = 1
                (output/'summary.json').write_text(json.dumps(summary))
                meta = dict(status='complete', planned_cases=240, completed_cases=240, saved_steps=7680,
                    new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
                    new_independent_initial_worlds=0, time_limit_seconds=300, storage_limit_bytes=67108864,
                    git_commit='a'*40, elapsed_seconds=1, input_sha256=bound, input_sha256_after=bound,
                    output_sha256={n: digest(output/n) for n in ('records.json', 'summary.json')})
                (output/'metadata.json').write_text(json.dumps(meta))
                def bindings():
                    if corrupt == 'early': raise ValueError('initial provenance failure')
                    return bound
                helper = types.SimpleNamespace(bindings=bindings, digest=digest,
                    read=lambda p: json.loads(Path(p).read_text()), input_paths=lambda errors: sorted(bound),
                    source_cases=lambda: iter(sources))
                index = {(r['genotype'], r['mode'], r['exchange'], r['seed']): r for r in records}
                with patch.dict(sys.modules, {'scripts.north_opportunity_inputs': helper}), patch.object(v, 'OUTPUT', output), patch.object(v, 'recount', side_effect=lambda c,g: index[g,c['mode'],c['exchange'],c['seed']]) as replay:
                    if corrupt:
                        with self.assertRaises(ValueError): v.main()
                        evidence = json.loads((output/'verification-failure.json').read_text())
                        self.assertEqual(len(evidence['input_sha256']), 389)
                        self.assertEqual(len(evidence['files_sha256_before']), 3)
                        self.assertEqual(len(evidence['files_sha256_after']), 3)
                        self.assertFalse((output/'independent-verification.json').exists())
                        if corrupt in ('early', 'binding'): replay.assert_not_called()
                    else:
                        v.main(); self.assertEqual(replay.call_count, 240)
                        proof_path = output/'independent-verification.json'
                        original = proof_path.read_bytes(); proof = json.loads(original)
                        self.assertEqual(proof['input_files'], 389)
                        self.assertEqual(proof['saved_steps'], 7680)
                        self.assertEqual(proof['files_sha256'], {n: digest(output/n) for n in ('metadata.json', 'records.json', 'summary.json')})
                        with self.assertRaises(ValueError): v.main()
                        self.assertEqual(proof_path.read_bytes(), original)
                        self.assertFalse((output/'verification-failure.json').exists())


class NorthActualCoverageTests(unittest.TestCase):
    def test_both_genotypes_modes_exchange_and_corruption(self):
        for genotype in v.GENOTYPES:
            for mode in v.MODES:
                for exchange in (False, True):
                    study = '019' if genotype == 'homogeneous' else ('023' if mode == 'random-direction' else '025')
                    path = Path(f'data/v4-study-{study}/cases/seed-120000-{mode}-exchange-{str(exchange).lower()}.json')
                    with self.subTest(genotype=genotype, mode=mode, exchange=exchange):
                        case = json.loads(path.read_text())
                        result = v.recount(case, genotype)
                        self.assertEqual(len(result['steps']), 32)
                        self.assertTrue(all(a['identity'] in case['initial']['site_ids'] for a in result['steps'][0]))
                        wrong = 'heterogeneous' if genotype == 'homogeneous' else 'homogeneous'
                        with self.assertRaises(ValueError): v.recount(case, wrong)
