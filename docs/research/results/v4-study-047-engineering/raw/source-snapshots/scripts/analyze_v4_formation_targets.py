"""Read-only post hoc formation-target accounting over the complete study013 cohort."""
import json
import subprocess
import time
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path

REASONS=('dissolved','energy','occupied','raw_material','collision','formed')
STRATA=('net_receive','net_output','gross_zero','throughflow_zero')
OUTPUT=Path('data/v4-study-013-targets')
STUDY=Path('data/v4-study-013')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def require(ok,message):
    if not ok: raise ValueError(message)


def preformation(units,raw,directions,width,height,threshold):
    n=width*height
    require(len(units)==len(raw)==len(directions)==n,'geometry coverage')
    dead=[i for i,u in enumerate(units) if u is not None and u['energy']==0]
    occupied=[u is not None and u['energy']>0 for u in units]
    resources=[v+int(i in dead) for i,v in enumerate(raw)]
    targets={};reasons={};candidates={i:[] for i in range(n)}
    for i,u in enumerate(units):
        if u is None:continue
        x,y=i%width,i//width
        require(type(directions[i]) is int and 0<=directions[i]<4,'direction ticket')
        t=(y*width+(x+1)%width,y*width+(x-1)%width,((y+1)%height)*width+x,((y-1)%height)*width+x)[directions[i]]
        targets[i]=t
        reason=('dissolved' if u['energy']==0 else 'energy' if u['energy']<threshold else 'occupied' if occupied[t] else 'raw_material' if resources[t]<1 else 'candidate')
        reasons[i]=reason
        if reason=='candidate': candidates[t].append(i)
    for i,r in reasons.items():
        if r=='candidate':reasons[i]='formed' if len(candidates[targets[i]])==1 else 'collision'
    return dict(dead=dead,occupied=occupied,raw=resources,target=targets,reason=reasons,candidates=candidates)


def ledger(units,transfers):
    flow=[dict(gross_in=0,gross_out=0,net=0) for _ in units]
    for t in transfers:
        a,b,v=t['donor'],t['recipient'],t['amount']
        require(all(type(x) is int for x in (a,b,v)) and 0<=a<len(units) and 0<=b<len(units) and a!=b and v>0,'invalid transfer')
        require(units[a] is not None and units[b] is not None,'transfer empty site')
        flow[a]['gross_out']+=v;flow[b]['gross_in']+=v
    for i,f in enumerate(flow):
        f['net']=f['gross_in']-f['gross_out']
        require(f['gross_out']<=4*(units[i]['energy']//8 if units[i] else 0),'gross outgoing bound')
    require(sum(f['net'] for f in flow)==0,'net conservation')
    return flow


def empty_counts():
    names=('actors','pairs','discordant','birth_gain','birth_loss','zero_on','zero_off','new_zero','avoided_zero','zero_subset_violations','energy_identity_violations','gross_bound_violations','net_sum','occupied_rescue_match','occupied_rescue_mismatch')
    c=dict.fromkeys(names,0)
    c.update({f'reason:{a}:{b}':0 for a,b in product(REASONS,repeat=2)})
    c.update({f'flow:{s}:{k}':0 for s in STRATA for k in ('actors','zero_on','zero_off','new_zero','avoided_zero')})
    c.update({f'threshold:{s}:{k}':0 for s in ('on','off') for k in ('crossed','not_crossed')})
    return c


def analyze_pair(origin,pair,config):
    actors=[i for i,u in enumerate(origin['units']) if u is not None]
    on,off=pair['on'],pair['off'];threshold=config['threshold']
    require(on['directions']==off['directions'],'paired directions')
    require(off['driven']['interaction']['transfers']==[],'off transfers')
    states={}
    for side,arm in (('on',on),('off',off)):
        require([i for i,u in enumerate(arm['interaction_units']) if u is not None]==actors,'interaction actor coverage')
        states[side]=preformation(arm['interaction_units'],origin['raw'],arm['directions'],config['width'],config['height'],threshold)
        recorded={i:'dissolved' for i in arm['material']['dissolved']}
        require(len(recorded)==len(arm['material']['dissolved']),'duplicate dissolved')
        for p in arm['material']['proposals']:
            require(p['source'] not in recorded,'duplicate actor')
            recorded[p['source']]=p['reason']
            if 'target' in p:require(p['target']==states[side]['target'][p['source']],'saved target mismatch')
        require(recorded==states[side]['reason'],'saved formation reason mismatch')
    flows=ledger(off['interaction_units'],on['driven']['interaction']['transfers'])
    counts=empty_counts();counts['pairs']=1;records=[];actor_rows=[]
    for i in actors:
        f=flows[i];a=on['interaction_units'][i]['energy'];b=off['interaction_units'][i]['energy']
        require(a==b+f['net'],'energy identity')
        require(not (a==0 and b>0),'zero set inclusion')
        stratum='net_receive' if f['net']>0 else 'net_output' if f['net']<0 else 'throughflow_zero' if f['gross_in'] else 'gross_zero'
        ra,rb=states['on']['reason'][i],states['off']['reason'][i]
        row=dict(tick=pair['tick'],actor=i,on_energy=a,off_energy=b,on_reason=ra,off_reason=rb,**f,stratum=stratum)
        actor_rows.append(row);counts[f'reason:{ra}:{rb}']+=1
        for k,v in dict(actors=1,zero_on=int(a==0),zero_off=int(b==0),new_zero=int(a==0 and b>0),avoided_zero=int(a>0 and b==0)).items():
            counts[k]+=v;counts[f'flow:{stratum}:{k}']+=v
        counts['net_sum']+=f['net']
        if (ra=='formed')==(rb=='formed'):continue
        counts['discordant']+=1;counts['birth_gain' if ra=='formed' else 'birth_loss']+=1
        target=states['on']['target'][i]
        evidence={}
        for side,arm in (('on',on),('off',off)):
            s=states[side];u=arm['interaction_units'][target]
            evidence[side]=dict(energy=arm['interaction_units'][i]['energy'],reason=s['reason'][i],target_energy=None if u is None else u['energy'],target_dissolved=target in s['dead'],target_occupied=s['occupied'][target],target_raw=s['raw'][target],candidates=s['candidates'][target])
        ca,cb=set(evidence['on']['candidates']),set(evidence['off']['candidates'])
        records.append(dict(tick=pair['tick'],actor=i,target=target,direction=on['directions'][i],threshold=threshold,**evidence,flow=f,extra_candidates=dict(on=sorted(ca-cb),off=sorted(cb-ca)),candidate_evidence=[dict(actor=j,on_energy=on['interaction_units'][j]['energy'],off_energy=off['interaction_units'][j]['energy'],flow=flows[j]) for j in sorted(ca|cb)]))
        if ra=='occupied' and rb=='formed':
            match=evidence['off']['target_dissolved'] and evidence['on']['target_occupied']
            counts['occupied_rescue_match' if match else 'occupied_rescue_mismatch']+=1
        for side,other in (('on','off'),('off','on')):
            if evidence[side]['reason']=='formed' and evidence[other]['reason']=='energy':
                crossed=evidence[side]['energy']>=threshold>evidence[other]['energy']
                counts[f"threshold:{side}:{'crossed' if crossed else 'not_crossed'}"]+=1
    if 'metrics' in pair:
        require(pair['metrics']['actor_matrix']==[[counts[f'reason:{a}:{b}'] for b in REASONS] for a in REASONS],'study013 matrix mismatch')
    return dict(records=records,actors=actor_rows,counts=counts)


def add_counts(rows):
    return {k:sum(row[k] for row in rows) for k in empty_counts()}


def summarize(sources):
    require(len(sources)==10 and {(s['seed'],s['mutation']) for s in sources}==set(product(range(96000,96005),(0,100))),'source grid')
    require(all(s['pairs']==400 for s in sources),'400 pairs per source')
    groups=[]
    for m in (0,100):
        chosen=[s for s in sources if s['mutation']==m];counts=add_counts([s['counts'] for s in chosen])
        groups.append(dict(mutation=m,drive=250,source_count=5,counts=counts,means={k:str(sum(Fraction(s['means'][k]) for s in chosen)/5) for k in counts}))
    return dict(sources=sources,groups=groups,counts=add_counts([s['counts'] for s in sources]))


def input_bindings():
    """Verify the already audited upstream inventories before taking a new snapshot."""
    from scripts.verify_v4_study012_summary import expected_bindings,verify_bindings,check_coverage
    meta=read(STUDY/'metadata.json');rows=read(STUDY/'results.json');proof=read(STUDY/'aggregation-verification.json')
    require(meta['status']=='complete' and meta['completed_pairs']==4000 and meta['completed_sources']==10,'complete study013 required')
    code,sources=expected_bindings()
    code.update(Path(p) for p in ('experiments/v4/study-013.md','scripts/run_v4_study013.py','scripts/verify_v4_study013_summary.py'))
    verify_bindings(meta['bindings_sha256'],code);verify_bindings(meta['source_bindings_sha256'],sources)
    require(proof['status']=='verified' and proof['pairs']==4000 and proof['actors']==973345,'upstream independent proof')
    for key,file in (('results_sha256','results.json'),('summary_sha256','summary.json')):require(proof[key]==digest(STUDY/file),'upstream proof binding')
    require(proof['verifier_sha256']==digest('scripts/verify_v4_study013_summary.py'),'upstream verifier binding')
    check_coverage(rows,('seed','drive','mutation'),set(product(range(96000,96005),(250,),(0,100))))
    paths=set(code)|set(sources)|{STUDY/f for f in ('metadata.json','results.json','summary.json','aggregation-verification.json')}
    for row in rows:
        name=f"seed-{row['seed']}-drive-250-mutation-{row['mutation']}"
        require(row['directory']==name and row['status']=='complete','canonical source directory')
        directory=STUDY/name;sm=read(directory/'metadata.json');source=Path('data/v4-study-005')/name
        require(Path(sm['source']).resolve()==source.resolve(),'canonical history directory')
        require(sm['status']=='complete' and (sm['start'],sm['end'],sm['steps'])==(101,500,400),'source completion')
        for key,file in (('metadata','metadata.json'),('steps','paired-steps.jsonl'),('summary','summary.json')):
            require(row[key+'_sha256']==digest(directory/file),'source index binding');paths.add(directory/file)
        require(sm['output_sha256']=={f:digest(directory/f) for f in ('paired-steps.jsonl','summary.json')},'source output inventory')
        require(sm['source_sha256']==sm['source_sha256_after']=={p.name:digest(p) for p in source.iterdir() if p.is_file()},'source historical inventory')
        require(row['summary']==read(directory/'summary.json'),'source summary binding')
    paths.update(Path(p) for p in ('docs/design/v4-formation-targets-supplement.md','scripts/analyze_v4_formation_targets.py','scripts/verify_v4_formation_targets.py'))
    return {str(p):digest(p) for p in sorted(paths)}


def save(path,value):
    Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False)
    meta=dict(schema='v4-formation-targets-1',status='running',completed_sources=0,completed_pairs=0,independent_new_samples=0)
    started=time.monotonic();save(OUTPUT/'metadata.json',meta)
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        meta['input_sha256']=input_bindings();save(OUTPUT/'metadata.json',meta);sources=[]
        with (OUTPUT/'records.jsonl').open('x') as records,(OUTPUT/'actors.jsonl').open('x') as actors:
            for row in sorted(read(STUDY/'results.json'),key=lambda r:(r['seed'],r['mutation'])):
                name=row['directory'];source=Path('data/v4-study-005')/name;cfg=read(source/'metadata.json')
                history=[json.loads(line) for line in (source/'steps.jsonl').open()]
                require([s['tick'] for s in history]==list(range(1,len(history)+1)),'historical ticks')
                counts=[]
                for tick,line in enumerate((STUDY/name/'paired-steps.jsonl').open(),101):
                    pair=json.loads(line);require(pair['tick']==tick<=500,'pair tick coverage')
                    require(pair['on']==history[tick-1],'historical on branch')
                    answer=analyze_pair(history[tick-2],pair,cfg);counts.append(answer['counts'])
                    for key,stream in (('records',records),('actors',actors)):
                        for entry in answer[key]:stream.write(json.dumps(dict(source=name,**entry),separators=(',',':'))+'\n')
                require(len(counts)==400,'full source pairs');total=add_counts(counts)
                sources.append(dict(seed=row['seed'],drive=250,mutation=row['mutation'],directory=name,pairs=400,counts=total,means={k:str(Fraction(v,400)) for k,v in total.items()}))
                meta.update(completed_sources=len(sources),completed_pairs=400*len(sources));save(OUTPUT/'metadata.json',meta)
                records.flush();actors.flush()
                require(time.monotonic()-started<1800,'time limit')
                require(sum(p.stat().st_size for p in OUTPUT.iterdir())<1024**3,'storage limit')
        summary=summarize(sources);save(OUTPUT/'summary.json',summary)
        require(summary['counts']['actors']==973345,'study013 actor coverage')
        meta['input_sha256_after']=input_bindings()
        require(meta['input_sha256']==meta['input_sha256_after'],'inputs changed during analysis')
        meta.update(status='complete',output_sha256={f:digest(OUTPUT/f) for f in ('records.jsonl','actors.jsonl','summary.json')})
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        meta['elapsed_seconds']=time.monotonic()-started;save(OUTPUT/'metadata.json',meta)


if __name__=='__main__':main()
