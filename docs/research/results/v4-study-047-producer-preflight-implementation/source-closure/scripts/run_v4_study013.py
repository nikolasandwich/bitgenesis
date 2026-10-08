"""Fixed historical reset pairs; python -m scripts.run_v4_study013."""
from dataclasses import asdict
from fractions import Fraction
from itertools import product
import json
from pathlib import Path
import subprocess
import time
from bitgenesis.v4.hereditary_growing import step
from bitgenesis.v4.heredity import HeritableUnit
from bitgenesis.v4.hereditary_runner import encode
from bitgenesis.v4.hereditary_audit import audit as source_audit
from bitgenesis.v4.exchange_branch_audit import physical_step
from scripts.run_v4_study010 import read, save, digest, hashes
from scripts.run_v4_study011 import preflight
from scripts.run_v4_study012 import binding_paths as previous_bindings, source_bindings, check_source_bindings, check_bindings

OUTPUT=Path('data/v4-study-013')
STORAGE_LIMIT=1024**3
TIME_LIMIT=1800
SEEDS=tuple(range(96000,96005))
METRICS=('births','deaths','energy_eligible','occupied')
REASONS=('dissolved','energy','occupied','raw_material','collision','formed')


def require(condition,message):
    if not condition:raise ValueError(message)


def measure(initial_units,on,off,threshold):
    actors={i for i,u in enumerate(initial_units) if u is not None}
    categories={};counts={}
    for label,record in (('on',on),('off',off)):
        dissolved=record['material']['dissolved']
        proposals=record['material']['proposals']
        by_site={i:'dissolved' for i in dissolved}
        require(len(by_site)==len(dissolved),'duplicate dissolved actor')
        for proposal in proposals:
            i=proposal['source'];reason=proposal['reason']
            require(i not in by_site and reason in REASONS[1:],'invalid actor proposal')
            by_site[i]=reason
        require(set(by_site)==actors,'actor coverage')
        eligible=sum(record['interaction_units'][i]['energy']>=threshold for i in actors)
        count=dict(births=sum(v=='formed' for v in by_site.values()),deaths=len(dissolved),energy_eligible=eligible,occupied=sum(u is not None for u in record['units']))
        require(eligible==sum(v not in ('energy','dissolved') for v in by_site.values()),'energy eligible margin')
        require(count['occupied']==len(actors)+count['births']-count['deaths'],'population ledger')
        categories[label]=by_site;counts[label]=count
    a,b=on['driven'],off['driven']
    require({k:v for k,v in a.items() if k!='interaction'}=={k:v for k,v in b.items() if k!='interaction'},'first stage or post interaction energy mismatch')
    require(all(a['interaction'][k]==b['interaction'][k] for k in ('bonds','spent')),'bond isolation')
    require(off['driven']['interaction']['transfers']==[],'off transfers')
    require(on['directions']==off['directions'] and on['mutation_tickets']==off['mutation_tickets'],'paired tickets')
    if not a['interaction']['transfers']:require(on==off,'zero transfer full record mismatch')
    matrix=[[0]*6 for _ in range(6)]
    for i in actors:matrix[REASONS.index(categories['on'][i])][REASONS.index(categories['off'][i])]+=1
    differences={k:counts['on'][k]-counts['off'][k] for k in METRICS}
    gains=sum(matrix[5][:5]);losses=sum(matrix[i][5] for i in range(5))
    require(gains-losses==differences['births'],'birth cancellation')
    require(differences['occupied']==differences['births']-differences['deaths'],'population difference')
    return dict(initial_occupied=len(actors),counts=counts,differences=differences,actor_matrix=matrix,birth_gains=gains,birth_losses=losses)


def summarize(metrics):
    require(bool(metrics),'nonempty step coverage required')
    n=len(metrics)
    totals={s:{k:sum(r['counts'][s][k] for r in metrics) for k in METRICS} for s in ('on','off')}
    diffs={k:totals['on'][k]-totals['off'][k] for k in METRICS}
    return dict(steps=n,totals=totals,differences=diffs,means={k:str(Fraction(v,n)) for k,v in diffs.items()},
        step_signs={k:{sign:sum((r['differences'][k]>0 if sign=='positive' else r['differences'][k]<0 if sign=='negative' else r['differences'][k]==0) for r in metrics) for sign in ('positive','zero','negative')} for k in METRICS},
        actor_matrix=[[sum(r['actor_matrix'][i][j] for r in metrics) for j in range(6)] for i in range(6)],
        birth_gains=sum(r['birth_gains'] for r in metrics),birth_losses=sum(r['birth_losses'] for r in metrics))


def aggregate(results):
    keys=[(r['seed'],r['drive'],r['mutation']) for r in results]
    require(len(keys)==10 and set(keys)==set(product(SEEDS,(250,),(0,100))),'complete unique ten-source grid required')
    for row in results:
        s=row['summary']
        require(row['status']=='complete' and s['steps']==400,'complete 400-step sources required')
        for k in METRICS:
            require(s['differences'][k]==s['totals']['on'][k]-s['totals']['off'][k] and s['means'][k]==str(Fraction(s['differences'][k],400)),'summary fraction mismatch')
    return dict(groups=[dict(drive=250,mutation=m,metrics={k:dict(mean=str(sum((Fraction(r['summary']['means'][k]) for r in results if r['mutation']==m),Fraction(0))/5),available=5,missing=0) for k in METRICS}) for m in (0,100)])


def production_step(origin,config,tape,exchange):
    require(type(exchange) is bool,'boolean exchange required')
    units=[None if u is None else HeritableUnit(u['material'],u['energy'],tuple(u['program'])) for u in origin['units']]
    units,raw,record=step(units,list(origin['raw']),config['width'],config['height'],[i['proposed'] for i in tape['driven']['inputs']],list(tape['directions']),[tuple(t) for t in tape['mutation_tickets']],exchange=exchange,**{k:config[k] for k in ('capacity','leak','bond_cost','threshold','construction_cost','copy_cost','mutation_per_thousand')})
    return json.loads(encode(dict(tick=tape['tick'],units=[None if u is None else asdict(u) for u in units],raw=raw,energy=record['energy_after'],directions=tape['directions'],mutation_tickets=tape['mutation_tickets'],**record)))


def run_source(output,source,start=101,end=500):
    require(type(start) is int and type(end) is int and 1<=start<=end,'positive inclusive interval required')
    root,source=Path(output),Path(source)
    root.mkdir(parents=True,exist_ok=False)
    meta=dict(schema='v4-study013-source-1',status='running',source=str(source.resolve()),start=start,end=end,steps=0)
    save(root/'metadata.json',meta)
    try:
        meta['source_sha256']=hashes(source)
        meta['source_audit']=source_audit(source)
        config=read(source/'metadata.json')
        require(config['exchange'] is True,'historical exchange must be enabled')
        history=[json.loads(line) for line in (source/'steps.jsonl').read_text().splitlines()]
        require(end<=len(history) and [r['tick'] for r in history]==list(range(1,len(history)+1)),'source tick coverage')
        initial=read(source/'initial.json');metrics=[]
        with (root/'paired-steps.jsonl').open('w') as stream:
            for tick in range(start,end+1):
                origin=history[tick-2] if tick>1 else initial
                tape=history[tick-1]
                on=production_step(origin,config,tape,True)
                off=production_step(origin,config,tape,False)
                require(on==tape,'full historical on record mismatch')
                for flag,record in ((True,on),(False,off)):
                    require(record==physical_step(origin['units'],origin['raw'],config,tape,flag),'independent physical record mismatch')
                measured=measure(origin['units'],on,off,config['threshold'])
                stream.write(encode(dict(tick=tick,on=on,off=off,metrics=measured)))
                metrics.append(measured)
        summary=summarize(metrics);save(root/'summary.json',summary)
        meta['source_sha256_after']=hashes(source)
        require(meta['source_sha256']==meta['source_sha256_after'],'source bytes changed')
        meta.update(status='complete',steps=len(metrics),output_sha256={name:digest(root/name) for name in ('paired-steps.jsonl','summary.json')})
        save(root/'metadata.json',meta)
        return summary
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',meta)
        raise


def binding_paths():
    return sorted(previous_bindings()+[Path('experiments/v4/study-013.md'),Path('scripts/run_v4_study013.py'),Path('scripts/verify_v4_study013_summary.py')])


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    root=OUTPUT;root.mkdir(exist_ok=False)
    metadata=dict(status='preflight',planned_sources=10,completed_sources=0,planned_pairs=4000,completed_pairs=0,
        independent_new_samples=0,known_first_pairs=40,known_first_pair_ticks=[101,201,301,401],storage_limit_bytes=STORAGE_LIMIT,time_limit_seconds=TIME_LIMIT)
    started=time.monotonic();results=[]
    save(root/'metadata.json',metadata);save(root/'results.json',results)
    def budget():
        if sum(p.stat().st_size for p in root.rglob('*') if p.is_file())>=STORAGE_LIMIT:return 'storage_limit'
        if time.monotonic()-started>=TIME_LIMIT:return 'time_limit'
    try:
        metadata['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
        bound={str(p):digest(p) for p in binding_paths()};metadata['bindings_sha256']=bound
        save(root/'metadata.json',metadata)
        rows,observations,by_observation,by_continuity=preflight()
        sources=source_bindings(rows,observations,by_observation,by_continuity);metadata['source_bindings_sha256']=sources
        low=[r for r in rows if r['drive']==250]
        require(len(low)==10 and {(r['seed'],r['mutation']) for r in low}==set(product(SEEDS,(0,100))),'all ten low-drive sources required')
        metadata['status']='running';save(root/'metadata.json',metadata)
        for row in sorted(low,key=lambda r:(r['seed'],r['mutation'])):
            check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
            limit=budget()
            if limit:metadata['status']=limit;return
            name=f"seed-{row['seed']}-drive-250-mutation-{row['mutation']}";directory=root/name
            summary=run_source(directory,Path('data/v4-study-005')/name)
            require(read(directory/'metadata.json')['status']=='complete' and summary['steps']==400,'source incomplete')
            check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
            results.append(dict(seed=row['seed'],drive=250,mutation=row['mutation'],directory=name,status='complete',summary=summary,
                metadata_sha256=digest(directory/'metadata.json'),steps_sha256=digest(directory/'paired-steps.jsonl'),summary_sha256=digest(directory/'summary.json')))
            metadata.update(completed_sources=len(results),completed_pairs=len(results)*400)
            save(root/'results.json',results);save(root/'metadata.json',metadata)
            print(f'{len(results)}/10 audited sources: {name}',flush=True)
            limit=budget()
            if limit:metadata['status']=limit;return
        check_bindings(bound);check_source_bindings(sources,rows,observations,by_observation,by_continuity)
        save(root/'summary.json',aggregate(results));metadata['status']='complete'
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        metadata['elapsed_seconds']=time.monotonic()-started
        save(root/'metadata.json',metadata)


if __name__=='__main__':main()
