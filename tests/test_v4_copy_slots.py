import json
import unittest
import tempfile
from unittest.mock import patch
from copy import deepcopy
from pathlib import Path
from scripts import analyze_v4_copy_slots as a


def fixture():
    units = [None]*256
    ids = [None]*256
    for site, identity in ((85, 0), (86, 1), (204, 2)):
        units[site] = dict(material=0 if identity < 2 else 3, program=[0]*4 if identity < 2 else [3]*4, energy=64)
        ids[site] = identity
    initial = dict(units=units, site_ids=ids, raw=[int(s in (101,102,117,118)) for s in range(256)])
    rows = [dict(tick=t, site_ids=deepcopy(ids), physical=dict(units=deepcopy(units)), observation=dict(components=dict(material=[[0,1],[2]]))) for t in range(1,33)]
    return dict(mode='random-direction', exchange=False, seed=120000, initial=initial, rows=rows, final=dict(parents=[None]*3))


class CopySlotsTest(unittest.TestCase):
    def test_all_translations_and_wrapping(self):
        self.assertEqual(a.placements({85,86,101,102,117,118,204}), [[85,86],[101,102],[117,118]])
        self.assertEqual(a.placements({15,0,16}), [[15,0]])
        self.assertEqual(len(a.placements(set(range(256)))),256)

    def test_positions_missing_and_whole_component(self):
        case=fixture(); r=a.analyze_case(case,'homogeneous')
        self.assertEqual(r['rows'][0]['copy_count'],1)
        self.assertEqual(r['rows'][0]['slots'][0]['roots'],[0,1])
        self.assertFalse(any(r['rows'][0]['slots'][1][k] for k in a.FLAGS))
        case['rows'][0]['observation']['components']['material']=[[0,1,2]]
        r=a.analyze_case(case,'homogeneous')
        self.assertTrue(r['rows'][0]['slots'][0]['genetic_match'])
        self.assertFalse(r['rows'][0]['slots'][0]['copy'])

    def test_ancestry_new_and_episodes(self):
        case=fixture(); case['final']['parents'] += [0,1,3,4]
        for row in case['rows'][:10]:
            for site,identity in ((101,5),(102,6)):
                row['site_ids'][site]=identity
                row['physical']['units'][site]=deepcopy(case['initial']['units'][85])
            row['observation']['components']['material'].append([5,6])
        r=a.analyze_case(case,'homogeneous')
        self.assertEqual((r['episodes'],r['longest']),([[1,10]],10))
        self.assertEqual(r['rows'][0]['slots'][1]['roots'],[0,1])
        self.assertEqual(r['rows'][0]['new_copy_count'],1)
        case['final']['parents'][3]=2
        r=a.analyze_case(case,'homogeneous')
        self.assertFalse(r['rows'][0]['slots'][1]['descendant'])

    def test_program_difference_and_partial_slot(self):
        case=fixture()
        case['rows'][0]['physical']['units'][86]['program'][3]=1
        r=a.analyze_case(case,'homogeneous')
        self.assertTrue(r['rows'][0]['slots'][0]['material_match'])
        self.assertFalse(r['rows'][0]['slots'][0]['genetic_match'])
        case['rows'][0]['site_ids'][86]=None
        case['rows'][0]['physical']['units'][86]=None
        case['rows'][0]['observation']['components']['material']=[[0],[2]]
        r=a.analyze_case(case,'homogeneous')
        slot=r['rows'][0]['slots'][0]
        self.assertEqual(slot['identities'],[0,None])
        self.assertEqual(slot['roots'],[0,None])
        self.assertFalse(any(slot[k] for k in a.FLAGS))

    def test_failure_preserves_incremental_records_and_readable_hashes(self):
        from scripts import copy_slots_inputs as inputs
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); output=root/'out'; known=root/'known.json'; missing=root/'missing.json'
            known.write_text('{}')
            hashes={str(known):inputs.digest(known)}
            hashes.update({f'bound-{i}':'hash' for i in range(412)})
            def inventory(errors):
                return list(hashes)
            def digest(path):
                return hashes[str(path)] if str(path) in hashes else inputs_digest(path)
            inputs_digest=inputs.digest
            with patch.object(a,'OUTPUT',output), patch.object(a.subprocess,'check_output',side_effect=['','abc']), patch.object(inputs,'input_paths',side_effect=inventory), patch.object(inputs,'digest',side_effect=digest), patch.object(inputs,'bindings',return_value=hashes), patch.object(inputs,'source_cases',return_value=[('homogeneous',known),('homogeneous',missing)]+[('homogeneous',missing)]*238), patch.object(inputs,'read',side_effect=[fixture(),OSError('unreadable source')]):
                with self.assertRaises(OSError):a.main()
            meta=json.loads((output/'metadata.json').read_text())
            self.assertEqual(meta['status'],'failed')
            self.assertEqual((meta['completed_cases'],meta['saved_steps'],meta['slot_steps']),(1,32,96))
            self.assertEqual(len(json.loads((output/'records.json').read_text())),1)
            self.assertEqual(meta['input_sha256'],hashes)
            self.assertIn('unreadable source',meta['error'])
            self.assertEqual(meta['output_sha256']['records.json'],inputs.digest(output/'records.json'))

    def records(self):
        base=a.analyze_case(fixture(),'homogeneous')
        return [dict(deepcopy(base),genotype=g,mode=m,exchange=e,seed=s) for g,m,e,s in a.GRID]

    def test_summary_negative_cells_and_denominators(self):
        cells=a.summarize(self.records())
        self.assertEqual(len(cells),12)
        self.assertEqual((cells[0]['n'],cells[0]['saved_steps'],cells[0]['slot_steps']),(20,640,1920))
        self.assertEqual(cells[0]['totals']['copy'],640)
        self.assertEqual(cells[-1]['new_double_steps'],0)

    def test_strict_summary_mutations(self):
        for mutation in ('seed','flag','count','roots','episode','extra','placement','missing','new','tick','identity'):
            records=self.records(); r=records[0]; slot=r['rows'][0]['slots'][0]
            if mutation=='seed': r['seed']=True
            if mutation=='flag': slot['copy']=1
            if mutation=='count': r['rows'][0]['copy_count']=0
            if mutation=='roots': slot['roots'][0]=True
            if mutation=='episode': r['episodes']=[[1,2]]
            if mutation=='extra': slot['extra']=0
            if mutation=='placement': r['placements'][0]=[86,85]
            if mutation=='missing': records.pop()
            if mutation=='new': slot['all_new']=True
            if mutation=='tick': r['rows'][0]['tick']=True
            if mutation=='identity': slot['identities'][0]=True
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):a.summarize(records)

    def test_first_real_case_only(self):
        case=json.loads(Path('data/v4-study-019/cases/seed-120000-random-direction-exchange-false.json').read_text())
        r=a.analyze_case(case,'homogeneous')
        self.assertEqual(len(r['rows']),32)
        self.assertEqual(r['placements'],[[85,86],[101,102],[117,118]])

if __name__=='__main__':unittest.main()
