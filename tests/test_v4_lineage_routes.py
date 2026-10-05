"""Saved-evidence boundary fixtures; no physics execution."""
import copy
import unittest
from scripts.analyze_v4_lineage_routes import analyze_case, summarize


def fixture(actors, raw=None, directions=None, reasons=None, births=None):
    units=[None]*256;ids=[None]*256
    for site,(identity,energy) in actors.items():
        units[site]=dict(material=0,energy=energy,program=[1,0,0,0]);ids[site]=identity
    parents=[None,None,None,0,1,3]
    initial=dict(tick=30,units=copy.deepcopy(units),site_ids=ids[:],raw=[0]*256)
    for site,value in (raw or {}).items():initial['raw'][site]=value
    dirs=[0]*256
    for site,d in (directions or {}).items():dirs[site]=d
    dead=[s for s,u in enumerate(units) if u is not None and u['energy']==0]
    finalunits=copy.deepcopy(units);finalids=ids[:];endraw=initial['raw'][:]
    for s in dead:finalunits[s]=None;finalids[s]=None;endraw[s]+=1
    proposals=[]
    for s,u in enumerate(units):
        if u is None or s in dead:continue
        d=dirs[s];x,y=s%16,s//16;t=(y*16+(x+1)%16,y*16+(x-1)%16,((y+1)%16)*16+x,((y-1)%16)*16+x)[d]
        reason=(reasons or {}).get(s,'raw_material');proposals.append(dict(source=s,target=t,direction=d,reason=reason))
    for site,identity in (births or {}).items():finalids[site]=identity;finalunits[site]=dict(material=0,energy=8,program=[1,0,0,0]);endraw[site]-=1
    row=dict(tick=31,site_ids=finalids,physical=dict(tick=31,units=finalunits,raw=endraw,interaction_units=units,directions=dirs,material=dict(dissolved=dead,proposals=proposals)),deaths=[ids[s] for s in dead],births=[dict(id=i) for i in (births or {}).values()])
    return dict(selection=dict(t0=30,remaining_steps=1,offspring_sites=[117,118],offspring_ids=[3,4],seed=1,category='short_window'),ablation=dict(initial=initial,rows=[row],final=dict(parents=parents,site_ids=finalids,individuals=[dict(parent=p) for p in parents])))


class LineageRouteTests(unittest.TestCase):
    def test_dissolution_returns_raw_and_newborn_not_actor(self):
        b=fixture({101:(3,16),85:(2,0)},directions={101:3},reasons={101:'formed'},births={85:5})
        r=analyze_case('east',b);e=r['rows'][0]['events'][0]
        self.assertEqual((e['target_raw'],e['target_empty'],e['target_dissolved'],e['child_id']),(1,True,True,5))
        self.assertEqual(len(r['rows'][0]['events']),1)
        self.assertEqual(r['rows'][0]['deaths'][0]['lineage'],'other')
        self.assertEqual(r['arrivals']['left']['upper'],dict(diagnostic_present=False,first_future_tick=31))
    def test_energy_priority_keeps_multiple_failed_gates(self):
        b=fixture({117:(3,15),118:(4,20)},reasons={117:'energy'})
        e=analyze_case('west',b)['rows'][0]['events'][0]
        self.assertFalse(e['energy_ok']);self.assertFalse(e['target_empty']);self.assertFalse(e['raw_ok'])
        b['ablation']['rows'][0]['physical']['material']['proposals'][0]['reason']='occupied'
        with self.assertRaises(ValueError):analyze_case('west',b)
    def test_collision_and_other_ancestry(self):
        b=fixture({84:(3,16),86:(2,16)},raw={85:1},directions={86:1},reasons={84:'collision',86:'collision'})
        r=analyze_case('east',b);a,c=r['rows'][0]['events']
        self.assertEqual((a['candidate_count'],c['candidate_count']),(2,2));self.assertEqual(c['lineage'],'other');self.assertIsNone(c['ancestor'])
    def test_diagnostic_is_separate_and_empty_future(self):
        b=fixture({85:(3,0)},reasons={})
        r=analyze_case('east',b)
        self.assertEqual(r['arrivals']['left']['upper'],dict(diagnostic_present=True,first_future_tick=None))
        self.assertEqual(r['upper_coexist_ticks'],[])
        self.assertEqual(r['counts']['right']['other']['formed'],0)
        self.assertEqual(summarize([r])['overall']['saved_steps'],1)
    def test_reject_newborn_proposal_and_bad_tick(self):
        b=fixture({101:(3,16)},raw={85:1},directions={101:3},reasons={101:'formed'},births={85:5})
        b['ablation']['rows'][0]['physical']['material']['proposals'].append(dict(source=85,target=86,direction=0,reason='energy'))
        with self.assertRaises(ValueError):analyze_case('east',b)
        b=fixture({204:(2,16)});b['ablation']['rows'][0]['tick']=30
        with self.assertRaises(ValueError):analyze_case('east',b)


class ProducerLifecycleTests(unittest.TestCase):
    def test_failure_preserves_records_and_hashes(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts import analyze_v4_lineage_routes as producer
        from scripts import lineage_route_inputs as inputs
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'run'
            with patch.object(producer,'OUTPUT',output),patch.object(producer.subprocess,'check_output',return_value=''),patch.object(inputs,'input_paths',return_value=['missing']),patch.object(inputs,'capture',return_value=({'source':'hash'},{})),patch.object(inputs,'bindings',return_value={'source':'hash'}),patch.object(inputs,'sources',side_effect=ValueError('injected source failure')):
                with self.assertRaisesRegex(ValueError,'injected source failure'):producer.main()
            meta=inputs.read(output/'metadata.json')
            self.assertEqual(meta['status'],'failed');self.assertEqual(meta['completed_cases'],0)
            self.assertEqual(meta['input_sha256'],meta['input_sha256_after'])
            self.assertEqual(inputs.read(output/'records.json'),[])
            self.assertEqual(meta['output_sha256']['records.json'],inputs.digest(output/'records.json'))
    def test_output_directory_is_exclusive(self):
        import tempfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts import analyze_v4_lineage_routes as producer
        with tempfile.TemporaryDirectory() as d:
            output=Path(d);sentinel=output/'existing';sentinel.write_text('untouched')
            with patch.object(producer,'OUTPUT',output),patch.object(producer.subprocess,'check_output',return_value=''):
                with self.assertRaises(FileExistsError):producer.main()
            self.assertEqual(sentinel.read_text(),'untouched')
