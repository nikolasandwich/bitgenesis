"""Independent target-stage reconstruction of the saved study013 cohort."""
import json
from hashlib import sha256
from pathlib import Path
from fractions import Fraction
from itertools import product

REASONS=('dissolved','energy','occupied','raw_material','collision','formed')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def flow_ledger(before, transfers):
    flows=[dict(gross_in=0,gross_out=0,net=0) for _ in before]
    for t in transfers:
        a,b,n=t['donor'],t['recipient'],t['amount']
        if any(type(x) is not int for x in (a,b,n)) or n<=0 or a==b or not (0<=a<len(before) and 0<=b<len(before)) or before[a] is None or before[b] is None:
            raise ValueError('invalid transfer')
        flows[a]['gross_out']+=n;flows[b]['gross_in']+=n
    for unit,flow in zip(before,flows):
        flow['net']=flow['gross_in']-flow['gross_out']
        if flow['gross_out']>4*((unit['energy'] if unit else 0)//8):raise ValueError('outflow bound')
    if sum(f['net'] for f in flows):raise ValueError('conservation')
    return flows


def before_formation(units, initial_raw, directions, width, height, threshold):
    if len(units)!=width*height or len(initial_raw)!=len(units) or len(directions)!=len(units):raise ValueError('geometry')
    if any(type(d) is not int or not 0<=d<4 for d in directions):raise ValueError('direction ticket')
    dead=[i for i,u in enumerate(units) if u is not None and u['energy']==0]
    occupied=[u is not None and u['energy']>0 for u in units]
    raw=[n+(i in dead) for i,n in enumerate(initial_raw)]
    targets={};reasons={};candidates={i:[] for i in range(len(units))}
    for i,u in enumerate(units):
        if u is None:continue
        x,y=i%width,i//width
        target=(y*width+(x+1)%width,y*width+(x-1)%width,((y+1)%height)*width+x,((y-1)%height)*width+x)[directions[i]]
        targets[i]=target
        reason='dissolved' if i in dead else 'energy' if u['energy']<threshold else 'occupied' if occupied[target] else 'raw_material' if raw[target]<1 else 'candidate'
        reasons[i]=reason
        if reason=='candidate':candidates[target].append(i)
    for i,r in list(reasons.items()):
        if r=='candidate':reasons[i]='formed' if len(candidates[targets[i]])==1 else 'collision'
    return dict(dead=dead,occupied=occupied,raw=raw,target=targets,reason=reasons,candidates=candidates)

STRATA=('net_receive','net_output','gross_zero','throughflow_zero')


def pair_evidence(origin,pair,config):
    on,off=pair['on'],pair['off'];tick=pair['tick'];threshold=config['threshold']
    original_actors={i for i,u in enumerate(origin['units']) if u is not None}
    if on['directions']!=off['directions'] or off['driven']['interaction']['transfers']:raise ValueError('paired isolation')
    for arm in (on,off):
        if {i for i,u in enumerate(arm['interaction_units']) if u is not None}!=original_actors:raise ValueError('interaction actor coverage')
    flows=flow_ledger(off['interaction_units'],on['driven']['interaction']['transfers'])
    states={name:before_formation(arm['interaction_units'],origin['raw'],arm['directions'],config['width'],config['height'],threshold) for name,arm in (('on',on),('off',off))}
    counts=dict(actors=0,pairs=1,discordant=0,birth_gain=0,birth_loss=0,zero_on=0,zero_off=0,new_zero=0,avoided_zero=0,zero_subset_violations=0,energy_identity_violations=0,gross_bound_violations=0,net_sum=0,occupied_rescue_match=0,occupied_rescue_mismatch=0)
    counts.update({f'reason:{a}:{b}':0 for a in REASONS for b in REASONS})
    counts.update({f'flow:{s}:{m}':0 for s in STRATA for m in ('actors','zero_on','zero_off','new_zero','avoided_zero')})
    counts.update({f'threshold:{side}:{outcome}':0 for side in ('on','off') for outcome in ('crossed','not_crossed')})
    records=[];actors=[]
    for side,arm in (('on',on),('off',off)):
        st=states[side];saved={i:'dissolved' for i in arm['material']['dissolved']}
        if len(saved)!=len(arm['material']['dissolved']):raise ValueError('duplicate dissolved actor')
        for p in arm['material']['proposals']:
            if p['source'] in saved:raise ValueError('duplicate actor')
            saved[p['source']]=p['reason']
            assert st['target'][p['source']]==p['target']
        assert saved==st['reason']
    for i,u in enumerate(origin['units']):
        if u is None:continue
        a,b=on['interaction_units'][i]['energy'],off['interaction_units'][i]['energy'];f=flows[i]
        assert a==b+f['net'] and not (a==0 and b>0)
        assert a>0 or b==0
        z={'zero_on':int(a==0),'zero_off':int(b==0),'new_zero':int(a==0 and b>0),'avoided_zero':int(b==0 and a>0)}
        stratum='net_receive' if f['net']>0 else 'net_output' if f['net']<0 else 'throughflow_zero' if f['gross_in'] else 'gross_zero'
        ra,rb=states['on']['reason'][i],states['off']['reason'][i]
        actors.append(dict(tick=tick,actor=i,on_energy=a,off_energy=b,on_reason=ra,off_reason=rb,**f,stratum=stratum))
        counts['actors']+=1;counts['net_sum']+=f['net'];counts[f'reason:{ra}:{rb}']+=1;counts[f'flow:{stratum}:actors']+=1
        for k,v in z.items():counts[k]+=v;counts[f'flow:{stratum}:{k}']+=v
        if (ra=='formed')==(rb=='formed'):continue
        counts['discordant']+=1;counts['birth_gain' if ra=='formed' else 'birth_loss']+=1
        target=states['on']['target'][i];assert target==states['off']['target'][i]
        arms={}
        for side,arm in (('on',on),('off',off)):
            st=states[side];tu=arm['interaction_units'][target]
            arms[side]=dict(energy=arm['interaction_units'][i]['energy'],reason=st['reason'][i],target_energy=None if tu is None else tu['energy'],target_dissolved=target in st['dead'],target_occupied=st['occupied'][target],target_raw=st['raw'][target],candidates=st['candidates'][target])
        ca,cb=set(arms['on']['candidates']),set(arms['off']['candidates'])
        extra=dict(on=sorted(ca-cb),off=sorted(cb-ca))
        evidence=[dict(actor=j,on_energy=on['interaction_units'][j]['energy'],off_energy=off['interaction_units'][j]['energy'],flow=flows[j]) for j in sorted(ca|cb)]
        records.append(dict(tick=tick,actor=i,target=target,direction=on['directions'][i],threshold=threshold,**arms,flow=f,extra_candidates=extra,candidate_evidence=evidence))
        if (ra,rb)==('occupied','formed'):
            match=arms['off']['target_dissolved'] and arms['on']['target_occupied'] and not arms['on']['target_dissolved']
            counts['occupied_rescue_match' if match else 'occupied_rescue_mismatch']+=1
        if (ra,rb) in (('energy','formed'),('formed','energy')):
            side='on' if ra=='formed' else 'off'
            crossed=(a>=threshold>b) if side=='on' else (b>=threshold>a)
            counts[f'threshold:{side}:{"crossed" if crossed else "not_crossed"}']+=1
    return dict(records=records,actors=actors,counts=counts)


def sum_counts(rows):
    assert rows and all(set(r)==set(rows[0]) for r in rows)
    return {k:sum(r[k] for r in rows) for k in rows[0]}


def checked_inputs():
    from scripts.verify_v4_study012_summary import expected_bindings, verify_bindings, check_coverage
    root=Path('data/v4-study-013');meta=read(root/'metadata.json');rows=read(root/'results.json');proof=read(root/'aggregation-verification.json')
    assert meta['status']=='complete' and meta['completed_pairs']==4000 and meta['completed_sources']==10
    assert proof['status']=='verified' and proof['pairs']==4000 and proof['actors']==973345
    assert proof['results_sha256']==digest(root/'results.json') and proof['summary_sha256']==digest(root/'summary.json')
    assert proof['verifier_sha256']==digest('scripts/verify_v4_study013_summary.py')
    codes,sources=expected_bindings()
    codes.update(Path(p) for p in ('experiments/v4/study-013.md','scripts/run_v4_study013.py','scripts/verify_v4_study013_summary.py'))
    verify_bindings(meta['bindings_sha256'],codes);verify_bindings(meta['source_bindings_sha256'],sources)
    check_coverage(rows,('seed','drive','mutation'),set(product(range(96000,96005),(250,),(0,100))))
    for r in rows:
        name=f"seed-{r['seed']}-drive-250-mutation-{r['mutation']}"
        assert r['directory']==name and r['status']=='complete'
        directory=root/name;sm=read(directory/'metadata.json')
        assert sm['status']=='complete' and sm['steps']==400 and (sm['start'],sm['end'])==(101,500)
        assert Path(sm['source']).resolve()==(Path('data/v4-study-005')/name).resolve()
        history_root=Path('data/v4-study-005')/name
        assert sm['source_sha256']==sm['source_sha256_after']=={p.name:digest(p) for p in history_root.iterdir() if p.is_file()}
        assert r['summary']==read(directory/'summary.json')
        assert set(sm['output_sha256'])=={'paired-steps.jsonl','summary.json'}
        for key,file in (('metadata','metadata.json'),('steps','paired-steps.jsonl'),('summary','summary.json')):
            assert r[key+'_sha256']==digest(directory/file)
        for file,h in sm['output_sha256'].items():assert digest(directory/file)==h
    return rows,meta


def main():
    from scripts.verify_v4_study012_summary import expected_bindings,verify_bindings
    root=Path('data/v4-study-013-targets');study=Path('data/v4-study-013')
    meta=read(root/'metadata.json');summary=read(root/'summary.json')
    assert meta['schema']=='v4-formation-targets-1' and meta['status']=='complete'
    assert meta['completed_sources']==10 and meta['completed_pairs']==4000 and meta['independent_new_samples']==0
    rows,upstream=checked_inputs()
    code,sources=expected_bindings()
    expected=code|sources|{Path(p) for p in ('experiments/v4/study-013.md','scripts/run_v4_study013.py','scripts/verify_v4_study013_summary.py','docs/design/v4-formation-targets-supplement.md','scripts/analyze_v4_formation_targets.py','scripts/verify_v4_formation_targets.py')}
    expected.update(study/p for p in ('metadata.json','results.json','summary.json','aggregation-verification.json'))
    expected.update(study/r['directory']/p for r in rows for p in ('metadata.json','paired-steps.jsonl','summary.json'))
    assert meta['input_sha256']==meta['input_sha256_after']
    verify_bindings(meta['input_sha256'],expected)
    assert set(meta['output_sha256'])=={'records.jsonl','actors.jsonl','summary.json'}
    verify_bindings({str(root/k):v for k,v in meta['output_sha256'].items()},{root/p for p in ('records.jsonl','actors.jsonl','summary.json')})
    source_results=[];n_actors=n_records=0
    with (root/'actors.jsonl').open() as ast,(root/'records.jsonl').open() as rst:
        for row in sorted(rows,key=lambda r:(r['seed'],r['mutation'])):
            name=row['directory'];history_root=Path('data/v4-study-005')/name
            cfg=read(history_root/'metadata.json');history=[json.loads(line) for line in (history_root/'steps.jsonl').open()]
            assert [h['tick'] for h in history]==list(range(1,len(history)+1))
            counts=[]
            with (study/name/'paired-steps.jsonl').open() as stream:
                for tick,line in enumerate(stream,101):
                    pair=json.loads(line);assert pair['tick']==tick<=500 and pair['on']==history[tick-1]
                    result=pair_evidence(history[tick-2],pair,cfg)
                    assert pair['metrics']['actor_matrix']==[[result['counts'][f'reason:{a}:{b}'] for b in REASONS] for a in REASONS]
                    for kind,file in (('actors',ast),('records',rst)):
                        for record in result[kind]:
                            saved=file.readline();assert saved and json.loads(saved)==dict(source=name,**record)
                    n_actors+=len(result['actors']);n_records+=len(result['records']);counts.append(result['counts'])
            assert len(counts)==400
            total=sum_counts(counts)
            source_results.append(dict(seed=row['seed'],drive=250,mutation=row['mutation'],directory=name,pairs=400,counts=total,means={k:str(Fraction(v,400)) for k,v in total.items()}))
        assert not ast.readline() and not rst.readline()
    groups=[]
    for m in (0,100):
        chosen=[s for s in source_results if s['mutation']==m];total=sum_counts([s['counts'] for s in chosen])
        groups.append(dict(mutation=m,drive=250,source_count=5,counts=total,means={k:str(sum(Fraction(s['means'][k]) for s in chosen)/5) for k in total}))
    expected_summary=dict(sources=source_results,groups=groups,counts=sum_counts([s['counts'] for s in source_results]))
    assert summary==expected_summary
    assert n_actors==973345 and n_records==summary['counts']['discordant']
    checked_inputs();verify_bindings(meta['input_sha256'],expected)
    verify_bindings({str(root/k):v for k,v in meta['output_sha256'].items()},{root/p for p in ('records.jsonl','actors.jsonl','summary.json')})
    proof=dict(status='verified',pairs=4000,actors=n_actors,discordant=n_records,independent_new_samples=0,
        metadata_sha256=digest(root/'metadata.json'),summary_sha256=digest(root/'summary.json'),records_sha256=digest(root/'records.jsonl'),actors_sha256=digest(root/'actors.jsonl'),verifier_sha256=digest(Path(__file__)),
        scope='independent pre-formation occupancy/raw/candidate reconstruction, gross transfer ledgers, all saved actor and discordant evidence, complete inventories and exact source means')
    with (root/'independent-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    try:main()
    except BaseException as error:
        target=Path('data/v4-study-013-targets/verification-failure.json')
        if target.parent.is_dir() and not target.exists():
            with target.open('x') as stream:stream.write(json.dumps(dict(status='failed',error=f'{type(error).__name__}: {error}',verifier_sha256=digest(Path(__file__))),indent=2)+'\n')
        raise
