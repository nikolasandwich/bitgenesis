"""Fixed heterogeneous-program controls and explicitly reset expression probes."""
from dataclasses import asdict
from collections import Counter
from copy import deepcopy
import subprocess,time,json
from pathlib import Path
from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.lineage import Observer
from bitgenesis.v4.structure import snapshot
from scripts.analyze_v4_structure_copies import analyze
from scripts.run_v4_copy_control import CONFIG,NAMES,normalize

OUTPUT=Path('data/v4-study-022')

def run_case(name):
    if name not in NAMES:raise ValueError('unknown fixed control')
    exchange=name=='constructed-on';raw_tokens=0 if name=='no-raw-off' else 4
    units=[None]*256;raw=[0]*256
    for site,material in ((85,0),(86,0),(204,3)):
        program=(0,0,0,1) if site==85 else (0,0,0,2) if site==86 else (3,3,3,3)
        units[site]=HeritableUnit(material,64,program)
    if raw_tokens:
        for site in (101,102,117,118):raw[site]=1
    def serialized():return normalize([None if u is None else asdict(u) for u in units])
    observer=Observer(serialized())
    initial=dict(tick=0,units=serialized(),raw=list(raw),site_ids=list(observer.alive),observation=snapshot(serialized(),observer.alive,16,16,phase='final'))
    rows=[]
    for tick in range(1,33):
        proposals=[8 if site in (85,86,117,118) else 0 for site in range(256)]
        directions=[1 if site%16==6 else 0 for site in range(256)]
        if tick==1:
            for site in (85,86):directions[site]=2
        if tick==2:
            for site in (101,102):directions[site]=2
        tickets=[(999,0,1)]*256
        units,raw,record=step(units,raw,proposals=proposals,directions=directions,mutation_tickets=tickets,exchange=exchange,**CONFIG)
        physical=normalize(dict(tick=tick,units=serialized(),raw=list(raw),energy=sum(u.energy for u in units if u is not None),directions=directions,mutation_tickets=tickets,**record))
        observer.accept(physical)
        rows.append(dict(tick=tick,site_ids=list(observer.alive),physical=physical,observation=snapshot(physical['units'],observer.alive,16,16,phase='final')))
    lineage=observer.result()
    final=dict(tick=32,units=serialized(),raw=list(raw),site_ids=list(observer.alive),parents=[v['parent'] for v in lineage['individuals']])
    copies=analyze(initial,rows,final)
    assert len(copies)==1 and copies[0]['component']==0 and copies[0]['anchor_members']==[0,1]
    copy=copies[0]
    summary=dict(name=name,exchange=exchange,raw_tokens=raw_tokens,steps=32,births=lineage['summary']['births'],deaths=lineage['summary']['deaths'],initial_energy=192,final_energy=sum(u.energy for u in units if u is not None),imported=sum(r['physical']['imported'] for r in rows),spent=sum(r['physical']['spent'] for r in rows),initial_mass=3+raw_tokens,final_mass=sum(raw)+sum(u is not None for u in units),genetic_counts=copy['series']['descendant_genetic'],episodes=copy['episodes']['descendant_genetic'],longest=copy['longest']['descendant_genetic'],persistent10=copy['longest']['descendant_genetic']>=10)
    assert summary['final_energy']==summary['initial_energy']+summary['imported']-summary['spent'] and summary['initial_mass']==summary['final_mass']
    return dict(name=name,exchange=exchange,raw_tokens=raw_tokens,config=dict(CONFIG),initial=initial,rows=rows,final=final,copy_parents=copies,summary=summary)


def run_probe(case,source_id):
    if type(source_id) is not int or source_id not in (5,6):raise ValueError('fixed probe source')
    ids=case['final']['site_ids']
    if source_id not in ids:return dict(source_id=source_id,status='unavailable',source=None,initial=None,physical=None)
    site=ids.index(source_id);unit=deepcopy(case['final']['units'][site]);source=dict(site=site,**unit)
    units=[None]*256;units[85]=HeritableUnit(0,64,tuple(unit['program']));raw=[0]*256;raw[69]=1
    initial=dict(units=normalize([None if u is None else asdict(u) for u in units]),raw=raw.copy())
    directions=[3]*256;tickets=[(999,0,1)]*256
    units,raw,record=step(units,raw,proposals=[0]*256,directions=directions,mutation_tickets=tickets,exchange=False,**CONFIG)
    physical=normalize(dict(tick=1,units=[None if u is None else asdict(u) for u in units],raw=raw,energy=sum(u.energy for u in units if u is not None),directions=directions,mutation_tickets=tickets,**record))
    return dict(source_id=source_id,status='complete',source=source,initial=initial,physical=physical)


def summarize(cases,probes,old_cases):
    if [c['name'] for c in cases]!=list(NAMES) or [c['name'] for c in old_cases]!=list(NAMES) or [p['source_id'] for p in probes]!=[5,6]:raise ValueError('fixed complete case/probe order')
    def projected(case):
        def state(units,raw,ids):return dict(units=[None if u is None else dict(material=u['material'],energy=u['energy']) for u in units],raw=raw,site_ids=ids)
        return dict(initial=state(case['initial']['units'],case['initial']['raw'],case['initial']['site_ids']),
                    rows=[state(r['physical']['units'],r['physical']['raw'],r['site_ids']) for r in case['rows']],
                    final=state(case['final']['units'],case['final']['raw'],case['final']['site_ids']),parents=case['final']['parents'])
    directions=[];programs=[];equivalence=[]
    for case,old in zip(cases,old_cases):
        formed=[p for row in case['rows'] for p in row['physical']['material']['proposals'] if p['reason']=='formed']
        hist=Counter(tuple(p['child_program']) for p in formed)
        directions.append(dict(name=case['name'],counts=[sum(p['direction']==d for p in formed) for d in range(4)]))
        programs.append(dict(name=case['name'],counts=[dict(program=list(p),count=hist[p]) for p in sorted(hist)]))
        equivalence.append(dict(name=case['name'],equal=projected(case)==projected(old)))
    probe_rows=[]
    for p in probes:
        if p['status'] not in ('complete','unavailable'):raise ValueError('probe status')
        formed=[] if p['status']=='unavailable' else sorted(q['material'] for q in p['physical']['material']['proposals'] if q['reason']=='formed')
        probe_rows.append(dict(source_id=p['source_id'],status=p['status'],formed_materials=formed))
    expected=bool(cases[0]['summary']['persistent10'] and cases[2]['summary']['births']==0 and all(r['equal'] for r in equivalence) and
                  all(p['status']=='complete' and p['formed_materials']==[v] for p,v in zip(probe_rows,(1,2))))
    return dict(cases=[c['summary'] for c in cases],formation_directions=directions,formed_programs=programs,physical_equivalence=equivalence,probes=probe_rows,expectations_met=expected)


def main():
    from scripts.copy_program_inputs import bindings,read,save,digest
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():raise ValueError('clean launch')
    OUTPUT.mkdir(exist_ok=False);started=time.monotonic();cases=[];probes=[]
    meta=dict(status='running',planned_cases=3,completed_cases=0,planned_probes=2,completed_probes=0,new_simulation_steps=0,new_independent_sources=0,artificial_control=True,
              git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),time_limit_seconds=300,storage_limit_bytes=33554432)
    def check():
        if time.monotonic()-started>300 or sum(p.stat().st_size for p in OUTPUT.iterdir())>33554432:raise ValueError('bounded run')
    try:
        before=bindings();meta['input_sha256']=before;save(OUTPUT/'metadata.json',meta)
        save(OUTPUT/'cases.json',cases);save(OUTPUT/'probes.json',probes)
        for name in NAMES:
            check();cases.append(run_case(name));meta.update(completed_cases=len(cases),new_simulation_steps=32*len(cases))
            save(OUTPUT/'cases.json',cases);save(OUTPUT/'metadata.json',meta)
        for source_id in (5,6):
            check();probe=run_probe(cases[0],source_id);probes.append(probe)
            meta.update(completed_probes=len(probes),new_simulation_steps=96+sum(p['status']=='complete' for p in probes))
            save(OUTPUT/'probes.json',probes);save(OUTPUT/'metadata.json',meta)
        summary=summarize(cases,probes,read('data/v4-copy-control/cases.json'));save(OUTPUT/'summary.json',summary)
        meta['input_sha256_after']=bindings()
        if before!=meta['input_sha256_after']:raise ValueError('changed sources')
        meta.update(status='complete',expectations_met=summary['expectations_met'],elapsed_seconds=time.monotonic()-started,
                    output_sha256={n:digest(OUTPUT/n) for n in ('cases.json','probes.json','summary.json')})
        check();save(OUTPUT/'metadata.json',meta);print(json.dumps({k:v for k,v in meta.items() if 'sha256' not in k}))
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc),elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after']=bindings()
            if meta.get('input_sha256')!=meta['input_sha256_after']:
                meta['finalization_error']='bound inputs changed during failed run'
        except BaseException as final_error:
            meta['finalization_error']=repr(final_error)
        try:
            meta['output_sha256']={n:digest(OUTPUT/n) for n in ('cases.json','probes.json','summary.json') if (OUTPUT/n).exists()}
        except BaseException as hash_error:
            meta['output_hash_error']=repr(hash_error)
        save(OUTPUT/'metadata.json',meta)
        raise

if __name__=='__main__':main()
