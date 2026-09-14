"""Full matched assay gate and preregistered hierarchical occupation contrasts."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.competition_audit import audit
from scripts.run_v4_study006 import verify_selection


def role_counts(rows,sites):
    if [r['tick'] for r in rows]!=list(range(1,201)):
        raise ValueError('competition horizon')
    alive=[None]*64
    for role,site in enumerate(sites):
        alive[site]=role
    result=[]
    for row in rows:
        for site in row['material']['dissolved']:
            if alive[site] is None:
                raise ValueError('role dissolution mismatch')
            alive[site]=None
        for proposal in row['material']['proposals']:
            if proposal['reason']=='formed':
                source,target=proposal['source'],proposal['target']
                if alive[source] is None or alive[target] is not None:
                    raise ValueError('role formation mismatch')
                alive[target]=alive[source]
        if [r is not None for r in alive]!=[u is not None for u in row['units']]:
            raise ValueError('role occupancy mismatch')
        result.append(dict(tick=row['tick'],counts=[alive.count(0),alive.count(1)]))
    return result


def primary(counts):
    numerator=sum(r['counts'][0]-r['counts'][1] for r in counts)
    return dict(numerator=numerator,denominator=12800,value=str(Fraction(numerator,12800)))


LAYOUTS={'adjacent':(34,35),'intermediate':(34,36),'separated':(34,38)}


def aggregate(contrasts):
    from scripts.verify_v4_study007 import aggregate as base_aggregate
    if len(contrasts)!=720 or any(r['layout'] not in LAYOUTS for r in contrasts):
        raise ValueError('layout observation coverage')
    sources=[]
    groups=[]
    for layout in LAYOUTS:
        s,g=base_aggregate([r for r in contrasts if r['layout']==layout])
        sources.extend(dict(**r,layout=layout) for r in s)
        groups.extend(dict(**r,layout=layout) for r in g)
    differences=[]
    for seed,td,mutation,drive,layout in product(range(96000,96005),(250,500),(0,100),(250,500),('adjacent','intermediate')):
        values={r['layout']:Fraction(r['mean']) for r in sources if
            (r['source_seed'],r['training_drive'],r['training_mutation'],r['drive'])==(seed,td,mutation,drive)}
        differences.append(dict(source_seed=seed,training_drive=td,training_mutation=mutation,drive=drive,
            layout=layout,reference='separated',difference=str(values[layout]-values['separated'])))
    grouped=[]
    for td,mutation,drive,layout in product((250,500),(0,100),(250,500),('adjacent','intermediate')):
        values=[Fraction(r['difference']) for r in differences if
            (r['training_drive'],r['training_mutation'],r['drive'],r['layout'])==(td,mutation,drive,layout)]
        if len(values)!=5:
            raise ValueError('layout contrast source coverage')
        grouped.append(dict(training_drive=td,training_mutation=mutation,drive=drive,layout=layout,
            reference='separated',sources=5,mean=str(sum(values,Fraction())/5)))
    return sources,groups,differences,grouped


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    pairs,selection_hash=verify_selection()
    meta=read(root/'metadata.json')
    if (meta['status'],meta['completed_runs'],meta['planned_runs'])!=('complete',1440,1440):
        raise ValueError('incomplete assay cohort')
    if meta['selection_sha256']!=selection_hash or meta['protocol_sha256']!=sha256(Path('experiments/v4/study-008.md').read_bytes()).hexdigest():
        raise ValueError('protocol/selection binding')
    rows=read(root/'results.json')
    fields=('source_seed','training_drive','training_mutation','descendant_id','environment','drive','layout','swapped')
    by_key={tuple(r[k] for k in fields):r for r in rows}
    expected={(s['seed'],s['drive'],s['mutation'],p['descendant']['id'],e,d,layout,swapped)
              for s,p in pairs for e,d,layout,swapped in product((101000,101001),(250,500),LAYOUTS,(False,True))}
    if len(rows)!=1440 or set(by_key)!=expected:
        raise ValueError('assay grid')
    hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('src/bitgenesis/v4').glob('*.py')}
    checks=[]
    contrasts=[]
    neutral_pairs=0
    random_pairing={}
    for source,pair in pairs:
        for environment,drive,layout in product((101000,101001),(250,500),LAYOUTS):
            sites=LAYOUTS[layout]
            observations={}
            matched={}
            for swapped in (False,True):
                key=(source['seed'],source['drive'],source['mutation'],pair['descendant']['id'],environment,drive,layout,swapped)
                row=by_key[key]
                directory=root/row['directory']
                m=read(directory/'metadata.json')
                config=dict(seed=environment,programs=[pair['descendant']['program'],pair['founder']['program']],steps=200,width=8,height=8,
                    initial_sites=list(sites[::-1] if swapped else sites),initial_material=0,initial_energy=64,initial_raw=1,
                    drive_per_thousand=drive,drive_amount=8,capacity=64,leak=1,bond_cost=1,
                    exchange=True,threshold=16,construction_cost=4,copy_cost=1,
                    mutation_per_thousand=0,max_site_records=12864)
                if any(m[k]!=v for k,v in config.items()) or m['git_commit']!=meta['git_commit'] or m['git_dirty'] is not False or m['source_sha256']!=hashes:
                    raise ValueError('assay configuration/source binding')
                checked=audit(directory)
                if checked!=read(directory/'audit.json') or checked['summary']!=row['summary']:
                    raise ValueError('assay audit/summary binding')
                with (directory/'steps.jsonl').open() as stream:
                    trajectory=[json.loads(line) for line in stream]
                counts=role_counts(trajectory,config['initial_sites'])
                saved_lineage=read(directory/'lineage.json')
                if saved_lineage['counts']!=counts or saved_lineage['dynamics_audit']!=checked:
                    raise ValueError('saved role counts mismatch')
                value=primary(counts)
                initial=read(directory/'initial.json')
                for site in sites:
                    initial['units'][site].pop('program')
                final=read(directory/'final.json')
                random_key=(source['seed'],source['drive'],source['mutation'],pair['descendant']['id'],environment,drive)
                random_states=([initial[k] for k in ('drive_rng','direction_rng','mutation_rng')],
                               [final[k] for k in ('drive_rng','direction_rng','mutation_rng')])
                if random_key in random_pairing and random_pairing[random_key]!=random_states:
                    raise ValueError('cross-layout random pairing')
                random_pairing[random_key]=random_states
                matched[swapped]=(initial,[final[k] for k in ('drive_rng','direction_rng','mutation_rng')],checked['output_sha256'],counts)
                observations[swapped]=Fraction(value['value'])
                checks.append(dict(**{k:row[k] for k in fields},directory=row['directory'],primary=value,role_counts=counts,audit=checked))
            if matched[False][:2]!=matched[True][:2]:
                raise ValueError('physical initial state/random pairing')
            if pair['equal_program']:
                if matched[False][2]!=matched[True][2] or any(a['counts']!=b['counts'][::-1] for a,b in zip(matched[False][3],matched[True][3])):
                    raise ValueError('neutral byte identity')
                neutral_pairs+=1
            contrasts.append(dict(source_seed=source['seed'],training_drive=source['drive'],training_mutation=source['mutation'],
                descendant_id=pair['descendant']['id'],environment=environment,drive=drive,layout=layout,
                equal_program=pair['equal_program'],difference=str((observations[False]+observations[True])/2)))
        print(f'{len(checks)}/1440 fully verified competitions',flush=True)
    if neutral_pairs!=660:
        raise ValueError('neutral pair coverage')
    source_rows,groups,layout_sources,layout_groups=aggregate(contrasts)
    return dict(scope='independent competition dynamics/role counts, swapped neutral controls and source-level scores',
        layout_source_contrasts=layout_sources,layout_group_contrasts=layout_groups,
        checks=checks,contrasts=contrasts,source_means=source_rows,group_means=groups,neutral_environment_pairs=neutral_pairs,
        selection_sha256=selection_hash,protocol_sha256=meta['protocol_sha256'],
        aggregation_dependency_sha256=sha256(Path('scripts/verify_v4_study007.py').read_bytes()).hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v4-study-008')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
