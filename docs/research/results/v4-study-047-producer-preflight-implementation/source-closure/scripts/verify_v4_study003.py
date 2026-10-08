"""Complete recovery cohort verification and independent passive observations."""
from fractions import Fraction
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
from bitgenesis.v4.growing_audit import audit as prefix_audit
from bitgenesis.v4.branch_audit import audit as branch_audit

PATCH=[y*16+x for y in range(6,10) for x in range(6,10)]
CHECKPOINTS=(300,310,350,400,500)


def fraction(n,d):
    return str(Fraction(n,d)) if d else None


def observe(reference,current,sites):
    original=[i for i in sites if reference[i] is not None]
    occupied=sum(current[i] is not None for i in sites)
    refill=sum(current[i] is not None for i in original)
    match=sum(current[i] is not None and current[i]['material']==reference[i]['material'] for i in original)
    return dict(reference_occupied=len(original),occupied=occupied,refilled=refill,matched=match,
        occupied_fraction=fraction(occupied,len(sites)),refill_fraction=fraction(refill,len(original)),
        material_match_fraction=fraction(match,len(original)))


def grid(rows):
    p=[r for r in rows if r['kind']=='prefix']
    b=[r for r in rows if r['kind']=='branch']
    if len(rows)!=25 or len(p)!=5 or {r['seed'] for r in p}!=set(range(93000,93005)):
        raise ValueError('prefix grid')
    if len(b)!=20 or {(r['seed'],r['removal'],r['threshold']) for r in b}!=set(product(range(93000,93005),(False,True),(16,65))):
        raise ValueError('branch grid')
    return {r['seed']:r for r in p},{(r['seed'],r['removal'],r['threshold']):r for r in b}


def verify(root):
    def read(path):
        return json.loads(path.read_text(encoding='utf-8'))
    def require(ok,message):
        if not ok:
            raise ValueError(message)
    meta=read(root/'metadata.json')
    require((meta['status'],meta['completed_prefixes'],meta['completed_branches'],meta['planned_prefixes'],meta['planned_branches'])==('complete',5,20,5,20),'incomplete cohort')
    require(meta['protocol_sha256']==sha256(Path('experiments/v4/study-003.md').read_bytes()).hexdigest(),'protocol binding')
    prefixes,branches=grid(read(root/'results.json'))
    hashes={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('src/bitgenesis/v4').glob('*.py')}
    def source_check(m):
        require(m['git_commit']==meta['git_commit'] and m['git_dirty'] is False,'source commit/dirty')
        require(m['source_sha256']==hashes,'source byte binding')
    checks=[]
    contrasts=[]
    for seed in range(93000,93005):
        origin=root/f'seed-{seed}-prefix'
        require(prefixes[seed]['directory']==origin.name,'prefix directory')
        pm=read(origin/'metadata.json')
        config=dict(seed=seed,steps=300,width=16,height=16,occupancy=250,max_energy=64,initial_raw=1,
                    drive_per_thousand=500,drive_amount=8,capacity=64,leak=1,bond_cost=1,exchange=True,
                    threshold=16,construction_cost=4,max_site_records=77056)
        require(all(pm[k]==v for k,v in config.items()),'prefix config')
        source_check(pm)
        pc=prefix_audit(origin)
        require(pc==read(origin/'audit.json') and pc['summary']==prefixes[seed]['summary'],'prefix audit/summary')
        before=read(origin/'final.json')
        reference=before['units']
        states={}
        branch_checks=[]
        rng=None
        for removal,threshold in product((False,True),(16,65)):
            item=branches[seed,removal,threshold]
            directory=root/f'seed-{seed}-removal-{int(removal)}-threshold-{threshold}'
            require(item['directory']==directory.name,'branch directory')
            bm=read(directory/'metadata.json')
            source_check(bm)
            require(bm['steps']==200 and bm['start_tick']==300 and bm['max_site_records']==51456
                    and bm['sites']==(PATCH if removal else []) and bm['config']['threshold']==threshold,'branch config')
            bc=branch_audit(directory,origin)
            require(bc==read(directory/'audit.json') and bc['summary']==item['summary'],'branch audit/summary')
            require(read(directory/'before.json')==before,'matched before')
            final=read(directory/'final.json')
            current_rng=(final['drive_rng'],final['direction_rng'])
            require(rng is None or current_rng==rng,'matched branch RNG')
            rng=current_rng
            selected={300:read(directory/'initial.json')['units']}
            ticks=[]
            with (directory/'steps.jsonl').open() as stream:
                for line in stream:
                    row=json.loads(line)
                    ticks.append(row['tick'])
                    if row['tick'] in CHECKPOINTS:
                        selected[row['tick']]=row['units']
            require(ticks==list(range(301,501)) and set(selected)==set(CHECKPOINTS),'checkpoint horizon')
            states[removal,threshold]=selected
            branch_checks.append(dict(removal=removal,threshold=threshold,audit=bc,
                                      boundary=read(directory/'boundary.json')))
        observations=[]
        outside=[i for i in range(256) if i not in PATCH]
        original=[i for i in PATCH if reference[i] is not None]
        endpoints={}
        for removal,threshold in product((False,True),(16,65)):
            for tick in CHECKPOINTS:
                current=states[removal,threshold][tick]
                result=observe(reference,current,PATCH)
                sham=states[False,threshold][tick]
                matched=sum(current[i] is not None and sham[i] is not None and current[i]['material']==sham[i]['material'] for i in original)
                observations.append(dict(removal=removal,threshold=threshold,tick=tick,patch=result,
                    outside=observe(reference,current,outside),
                    contemporary_sham_match_fraction=fraction(matched,len(original)) if removal else None))
                if tick==500:
                    endpoints[removal,threshold]=result['material_match_fraction']
        for name,hi,lo in (('removal_threshold16',(True,16),(False,16)),
                           ('removal_threshold65',(True,65),(False,65)),
                           ('formation_under_removal',(True,16),(True,65))):
            a,b=endpoints[hi],endpoints[lo]
            contrasts.append(dict(seed=seed,contrast=name,difference=None if a is None or b is None else str(Fraction(a)-Fraction(b))))
        checks.append(dict(seed=seed,prefix_audit=pc,branches=branch_checks,observations=observations))
        print(f'Verified recovery source {seed}',flush=True)
    means=[]
    for name in sorted({r['contrast'] for r in contrasts}):
        values=[Fraction(r['difference']) for r in contrasts if r['contrast']==name and r['difference'] is not None]
        means.append(dict(contrast=name,defined_sources=len(values),mean=str(sum(values,Fraction())/len(values)) if values else None))
    return dict(scope='independent prefix/branch dynamics and registered recovery observations; no ancestry inference',
                checks=checks,contrasts=contrasts,contrast_means=means,
                protocol_sha256=meta['protocol_sha256'],source_sha256=hashes,
                script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())


if __name__=='__main__':
    root=Path('data/v4-study-003')
    result=verify(root)
    with (root/'verification.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
