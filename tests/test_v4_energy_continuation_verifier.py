import json
import tarfile
import unittest
from copy import deepcopy
from pathlib import Path
from scripts import verify_v4_energy_continuation as audit


def fixture():
    probe = json.loads(Path('docs/research/results/v4-study-027-records.json').read_text())[0]
    name = f"cases/seed-{probe['seed']}-random-both-exchange-false.json"
    with tarfile.open('docs/research/results/v4-study-019-cases.tar.gz') as archive:
        source = json.load(archive.extractfile(name))
    return source, probe


class ContinuationVerifierTest(unittest.TestCase):
    def test_fixture_identity_energy_observation_and_no_mutation(self):
        source, probe = fixture(); original = deepcopy((source, probe))
        branch = audit.verify_branch(source, probe)
        self.assertEqual((source, probe), original)
        self.assertEqual(branch['initial']['tick'], 15)
        self.assertEqual(len(branch['rows']), 17)
        self.assertEqual(branch['final']['tick'], 32)
        self.assertEqual(branch['initial']['units'], probe['treated']['units'])
        self.assertEqual(branch['final']['parents'][:len(branch['initial']['parents'])], branch['initial']['parents'])
        self.assertEqual(branch['metrics']['final_energy'], sum(u['energy'] for u in branch['initial']['units'] if u) + branch['metrics']['imported'] - branch['metrics']['spent'])
        self.assertEqual(set(branch['metrics']), set(audit.METRICS))
        self.assertTrue(all(len(values)==32 for p in branch['copy_parents'] for values in p['series'].values()))
        self.assertEqual(branch['delta'], {k:branch['metrics'][k]-branch['control_metrics'][k] for k in audit.METRICS})

    def test_full_probe_and_prefix_identity_tamper_rejected(self):
        for field in ('treated', 'initial', 'control', 'added_energy', 'prefix'):
            source, probe = fixture()
            if field == 'prefix': source['rows'][0]['site_ids'][85] = 900
            elif field == 'added_energy': probe[field] = True
            elif field == 'initial': probe[field]['raw'][0] += 1
            else: probe[field]['raw'][0] += 1
            with self.subTest(field=field), self.assertRaises(ValueError): audit.verify_branch(source, probe)

    def test_future_accepted_ignored_and_proposed_replayed(self):
        source, probe = fixture()
        baseline = audit.verify_branch(source, probe)
        for row in source['rows'][probe['tick']:]:
            for item in row['physical']['driven']['inputs']: item['accepted'] = 999
        self.assertEqual(audit.verify_branch(source, probe), baseline)
        source['rows'][probe['tick']]['physical']['driven']['inputs'][117]['proposed'] += 8
        self.assertNotEqual(audit.verify_branch(source, probe)['rows'][0]['physical'], baseline['rows'][0]['physical'])

    def test_summary_strict_types_order_and_delta(self):
        source, probe = fixture(); base = audit.record(audit.verify_branch(source, probe))
        probes = json.loads(Path('docs/research/results/v4-study-027-records.json').read_text())
        records=[]
        for p in probes:
            r=deepcopy(base); r['selection']={k:p[k] for k in audit.prior.KEYS}; r['added_energy']=p['added_energy']
            f=r['child_fate']; f['birth_tick']=p['tick']; f['death_tick']=None; f['alive_final']=True; f['observed_alive_finals']=33-p['tick']; f['lineage_living_final']=max(1,f['lineage_living_final'])
            r['metrics']['living']=max(f['lineage_living_final'],r['metrics']['living'])
            r['delta']={k:r['metrics'][k]-r['control_metrics'][k] for k in audit.METRICS}
            records.append(r)
        self.assertEqual([c['n'] for c in audit.aggregate(records)], [21,5,21,5])
        with self.assertRaises(ValueError): audit.aggregate(records[::-1])
        for label,key,value in [('metrics','births',True),('delta','final_energy',base['delta']['final_energy']+1),('child_fate','identity',True),('child_fate','lineage_living_final',0),('child_fate','lineage_living_final',8),('metrics','living',8),('metrics','final_energy',449)]:
            bad=deepcopy(records); bad[0][label][key]=value
            with self.subTest(label=label), self.assertRaises(ValueError): audit.aggregate(bad)

    def test_main_failure_preserves_inventory_and_existing_proof(self):
        import tempfile, types, sys, hashlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); present=root/'present'; missing=root/'missing'; present.write_text('original')
            def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
            helper=types.SimpleNamespace(input_paths=lambda errors:[str(present),str(missing)],
                bindings=lambda:(_ for _ in ()).throw(ValueError('bad binding')),digest=digest,
                read=lambda p:json.loads(p.read_text()),source_cases=lambda:iter([]))
            with patch.object(audit,'OUTPUT',root), patch.dict(sys.modules,{'scripts.energy_continuation_inputs':helper}):
                with self.assertRaisesRegex(ValueError,'bad binding'): audit.main()
                failure=json.loads((root/'verification-failure.json').read_text())
                self.assertEqual(failure['input_sha256'],{str(present):digest(present)})
                self.assertEqual(failure['input_sha256_after'],failure['input_sha256'])
                self.assertIn(str(missing),failure['read_errors_before'])
                self.assertEqual(len([n for n in failure['read_errors_before'] if n.startswith('cases/')]),52)
                proof=root/'independent-verification.json'; proof.write_text('keep')
                with self.assertRaisesRegex(ValueError,'proof already exists'): audit.main()
                self.assertEqual(proof.read_text(),'keep')
