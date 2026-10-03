import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts import verify_v4_copy_control as verify


class CopyControlVerifier(unittest.TestCase):
    def test_reject_unknown_case(self):
        with self.assertRaises(ValueError):verify.verify_case(dict(name='unknown'))

    def cases(self):
        from scripts.run_v4_copy_control import run_case
        return [run_case(name) for name in ('constructed-off','constructed-on','no-raw-off')]

    def test_three_physical_cases_and_positive_negative_expectations(self):
        cases=self.cases()
        for case in cases:
            self.assertEqual(verify.verify_case(case),case['summary'])
        self.assertTrue(cases[0]['summary']['persistent10'])
        self.assertEqual(cases[2]['summary']['births'],0)

    def test_tampered_tape_identity_copy_and_initial_rejected(self):
        case=self.cases()[0]
        bad=copy.deepcopy(case);bad['rows'][0]['physical']['driven']['inputs'][0]['proposed']=1
        with self.assertRaises(ValueError):verify.verify_case(bad)
        bad=copy.deepcopy(case);bad['rows'][0]['site_ids'][85]=99
        with self.assertRaises(ValueError):verify.verify_case(bad)
        bad=copy.deepcopy(case);bad['copy_parents'][0]['series']['descendant_genetic'][0]+=1
        with self.assertRaises(ValueError):verify.verify_case(bad)
        bad=copy.deepcopy(case);bad['initial']['raw'][0]=1
        with self.assertRaises(ValueError):verify.verify_case(bad)
        bad=copy.deepcopy(case);bad['rows'][2]['physical']['mutation_tickets'][0]=[998,0,1]
        with self.assertRaises(ValueError):verify.verify_case(bad)

    def output(self,root,cases):
        for name,value in (('cases',cases),('summary',[c['summary'] for c in cases])):
            (root/f'{name}.json').write_text(json.dumps(value))
        bound=verify.bindings()
        meta=dict(status='complete',planned_cases=3,completed_cases=3,new_simulation_steps=96,new_independent_sources=0,
                  artificial_control=True,git_commit='a'*40,input_sha256=bound,input_sha256_after=bound,
                  output_sha256={n:verify.digest(root/n) for n in ('cases.json','summary.json')},elapsed_seconds=1,
                  time_limit_seconds=60,storage_limit_bytes=33554432,expectations_met=True)
        (root/'metadata.json').write_text(json.dumps(meta))
        return meta

    def test_main_proof_exclusive_and_expectations_metadata_binding(self):
        cases=self.cases()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);self.output(root,cases)
            with patch.object(verify,'OUTPUT',root):
                verify.main()
                self.assertEqual(json.loads((root/'independent-verification.json').read_text())['saved_steps'],96)
                with self.assertRaises(FileExistsError):verify.main()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);meta=self.output(root,cases);meta['expectations_met']=False
            (root/'metadata.json').write_text(json.dumps(meta))
            with patch.object(verify,'OUTPUT',root):
                with self.assertRaises(ValueError):verify.main()
            self.assertTrue((root/'verification-failure.json').exists())
            self.assertFalse((root/'independent-verification.json').exists())

    def test_metadata_inventory_and_output_tampering_rejected(self):
        cases=self.cases()
        for corruption in ('inventory','steps','cases_hash','order','missing_case'):
            with self.subTest(corruption=corruption), tempfile.TemporaryDirectory() as directory:
                root=Path(directory);meta=self.output(root,cases)
                if corruption=='inventory':meta['input_sha256'].pop(next(iter(meta['input_sha256'])))
                elif corruption=='steps':meta['new_simulation_steps']=95
                elif corruption=='cases_hash':meta['output_sha256']['cases.json']='0'*64
                else:
                    bad=cases[::-1] if corruption=='order' else cases[:-1]
                    (root/'cases.json').write_text(json.dumps(bad));meta['output_sha256']['cases.json']=verify.digest(root/'cases.json')
                (root/'metadata.json').write_text(json.dumps(meta))
                with patch.object(verify,'OUTPUT',root):
                    with self.assertRaises(ValueError):verify.main()
                self.assertTrue((root/'verification-failure.json').exists())

    def test_unmet_expectations_can_be_verified_after_all_cases(self):
        cases=self.cases()
        summaries=[copy.deepcopy(c['summary']) for c in cases]
        summaries[0]['persistent10']=False
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);meta=self.output(root,cases)
            (root/'summary.json').write_text(json.dumps(summaries))
            meta['output_sha256']['summary.json']=verify.digest(root/'summary.json');meta['expectations_met']=False
            (root/'metadata.json').write_text(json.dumps(meta))
            # Isolate orchestration: physical correctness is covered by verify_case tests.
            with patch.object(verify,'OUTPUT',root), patch.object(verify,'verify_case',side_effect=summaries) as checked:
                verify.main();self.assertEqual(checked.call_count,3)
            proof=json.loads((root/'independent-verification.json').read_text())
            self.assertFalse(proof['expectations_met'])
