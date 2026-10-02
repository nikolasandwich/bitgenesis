import json
from hashlib import sha256

import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest.mock import patch
from bitgenesis.v4.hereditary_runner import run as source_run
from bitgenesis.v4 import exchange_branch as branch
from bitgenesis.v4.exchange_branch_audit import audit, continuity


def read(path):
    return json.loads(path.read_text())


class ExchangeBranchTests(unittest.TestCase):
    def test_historical_replay_and_isolation(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        tmp_path = Path(temporary.name)
        source = tmp_path/'source'
        source_run(source, 105000, steps=10, width=4, height=4, mutation_per_thousand=100, leak=4)
        before = {p.name: p.read_bytes() for p in source.iterdir()}
        result = branch.run(tmp_path/'on', source, 0, 10)
        branch.run(tmp_path/'off', source, 0, 10, False)
        historical = [json.loads(s) for s in (source/'steps.jsonl').read_text().splitlines()]
        on = [json.loads(s) for s in (tmp_path/'on/steps.jsonl').read_text().splitlines()]
        off = [json.loads(s) for s in (tmp_path/'off/steps.jsonl').read_text().splitlines()]
        assert [r['physical'] for r in on] == historical
        assert any(r['physical']['driven']['interaction']['transfers'] for r in on)
        for a,b in zip(on,off):
            assert a['physical']['directions'] == b['physical']['directions']
            assert a['physical']['mutation_tickets'] == b['physical']['mutation_tickets']
            assert [i['proposed'] for i in a['physical']['driven']['inputs']] == [i['proposed'] for i in b['physical']['driven']['inputs']]
            assert b['physical']['driven']['interaction']['transfers'] == []
        for key in ('bonds','spent'):
            assert on[0]['physical']['driven']['interaction'][key] == off[0]['physical']['driven']['interaction'][key]
        assert on[0]['physical']['driven']['energy_after'] == off[0]['physical']['driven']['energy_after']
        final = read(tmp_path/'on/final.json')
        old_ids = read(tmp_path/'on/initial.json')['site_ids']
        refills = 0
        for row in on:
            for site in row['physical']['material']['dissolved']:
                assert final['death_ticks'][old_ids[site]] == row['tick']
                if row['site_ids'][site] is not None:
                    refills += 1
                    assert row['site_ids'][site] != old_ids[site]
            old_ids = row['site_ids']
        assert refills > 0
        assert before == {p.name:p.read_bytes() for p in source.iterdir()}
        assert audit(tmp_path/'on', source)['summary'] == result['summary']
        audit(tmp_path/'off',source)
        with self.assertRaises(FileExistsError):
            branch.run(tmp_path/'on',source,0,10)
    
    
    def test_independent_audit_and_tampering(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        tmp_path = Path(temporary.name)
        source=tmp_path/'source'
        source_run(source,105000,steps=6,width=4,height=4)
        output=tmp_path/'out'
        branch.run(output,source,2,4)
        with patch.object(branch,'step',side_effect=AssertionError('production called')), patch.object(branch,'follow',side_effect=AssertionError('production called')):
            audit(output,source)
        rows=read(output/'continuity.json')
        rows[0]['endpoint']['descendants']+=1
        (output/'continuity.json').write_text(json.dumps(rows))
        meta=read(output/'metadata.json')
        meta['output_sha256']['continuity.json']=sha256((output/'continuity.json').read_bytes()).hexdigest()
        (output/'metadata.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'continuity'):
            audit(output,source)
    
    
    def test_empty_denominator(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        tmp_path = Path(temporary.name)
        source=tmp_path/'source'
        source_run(source,105000,steps=2,width=4,height=4,occupancy=0)
        result=branch.run(tmp_path/'out',source,0,2)
        assert result['records'] == []
        assert result['summary']['continuous_fraction'] is None
        audit(tmp_path/'out',source)

    def test_ancestral_edge_cases(self):
        fixtures = [
            ({0:[[0,1],[2]],1:[[0,3],[2]]}, [None,None,None,0]),
            ({0:[[0,1],[2]],1:[[0,1,2]]}, [None,None,None]),
            ({0:[[0,1],[2]],1:[[0],[1],[2]],2:[[0,1],[2]]}, [None,None,None]),
            ({0:[[0,1],[2]],1:[[0,1]]}, [None,None,None]),
            ({0:[[0]],1:[[0]]}, [None]),
            ({0:[[0,1]],1:[[0,1]]}, [None,None]),
            ({0:[[0,1],[2]],1:[[3,4],[2]]}, [None,None,None,0,1]),
        ]
        for series, parents in fixtures:
            expected = branch.follow(series,parents,0,[len(series)-1])[len(series)-1]
            self.assertEqual(continuity(series,parents),expected)
        lost = continuity(*fixtures[0])[0]
        self.assertTrue(lost['continuous_closed_multi'])
        self.assertEqual(lost['endpoint']['represented_anchor_members'],1)
        self.assertEqual(lost['endpoint']['original_survivors'],1)
        self.assertEqual(continuity(*fixtures[1])[0]['endpoint']['state'],'mixed')
        self.assertTrue(continuity(*fixtures[2])[0]['endpoint_closed_after_break'])
        self.assertFalse(continuity(*fixtures[2])[0]['continuous_closed_multi'])
        self.assertEqual(branch.summarize(continuity(*fixtures[3]))['eligible_components'],1)
        for fixture in fixtures[4:6]:
            self.assertIsNone(branch.summarize(continuity(*fixture))['continuous_fraction'])
        self.assertTrue(continuity(*fixtures[6])[0]['primary'])

    def test_physical_tamper_and_failure_metadata(self):
        with TemporaryDirectory() as temporary:
            root=Path(temporary)
            source=root/'source'
            source_run(source,105000,steps=3,width=4,height=4)
            output=root/'branch'
            branch.run(output,source,0,3,False)
            rows=[json.loads(line) for line in (output/'steps.jsonl').read_text().splitlines()]
            rows[0]['physical']['driven']['interaction']['spent']+=1
            (output/'steps.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in rows))
            meta=read(output/'metadata.json')
            meta['output_sha256']['steps.jsonl']=sha256((output/'steps.jsonl').read_bytes()).hexdigest()
            (output/'metadata.json').write_text(json.dumps(meta))
            with self.assertRaisesRegex(ValueError,'physical'):
                audit(output,source)
            with patch.object(branch,'step',side_effect=RuntimeError('injected failure')):
                with self.assertRaisesRegex(RuntimeError,'injected failure'):
                    branch.run(root/'failed',source,0,3)
            self.assertEqual(read(root/'failed/metadata.json')['status'],'failed')
            with self.assertRaisesRegex(ValueError,'horizon'):
                branch.run(root/'short',source,2,3)
            self.assertEqual(read(root/'short/metadata.json')['status'],'failed')

    def test_missing_source_leaves_failure_metadata(self):
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root/'branch'
            with self.assertRaises(FileNotFoundError):
                branch.run(output, root/'missing', 0, 2)
            self.assertTrue((output/'metadata.json').is_file())
            self.assertEqual(read(output/'metadata.json')['status'], 'failed')
            self.assertFalse((output/'steps.jsonl').exists())
