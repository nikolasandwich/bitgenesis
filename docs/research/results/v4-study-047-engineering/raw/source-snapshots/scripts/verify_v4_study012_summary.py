"""Independent saved-cohort recount, paired estimands and intervention invariants."""
import json
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path

METRICS=('continuous','replacement','endpoint_closed','lineage_survival','original_retention','descendants')


def check_coverage(rows,fields,expected):
    keys=[tuple(r[k] for k in fields) for r in rows]
    if len(keys)!=len(expected) or set(keys)!=expected:
        raise ValueError('missing, repeated or unexpected coverage: '+','.join(fields))


def recount(records):
    chosen=[r for r in records if r['anchor_size']>1 and not r['whole_world_anchor']]
    counts=dict(continuous=0,replacement=0,endpoint_closed=0,lineage_survival=0)
    retention=Fraction(0);descendants=0
    for r in chosen:
        end=r['endpoint']
        counts['continuous']+=bool(r['continuous_closed_multi'])
        counts['replacement']+=bool(r['primary'])
        counts['endpoint_closed']+=end['state']=='closed_multi'
        counts['lineage_survival']+=end['descendants']>0
        retention+=Fraction(end['original_survivors'],r['anchor_size'])
        descendants+=end['descendants']
    n=len(chosen)
    nums={**counts,'original_retention':retention,'descendants':descendants}
    return dict(initial_components=len(records),eligible_components=n,counts=counts,
        sums=dict(original_retention=str(retention),descendants=descendants),
        fractions={k:str(Fraction(v)/n) if n else None for k,v in nums.items()})


def average(values):
    present=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(present)/len(present)) if present else None,
                available=len(present),missing=len(values)-len(present))


def verify_bindings(recorded,expected):
    if set(recorded)!={str(p) for p in expected}:
        raise ValueError('incomplete or extra binding inventory')
    for path,value in recorded.items():
        if sha256(Path(path).read_bytes()).hexdigest()!=value:
            raise ValueError('binding content mismatch')


def expected_bindings():
    """Derive complete required provenance, independently of runner inventories."""
    code=set(Path('src/bitgenesis/v4').glob('*.py'))
    code.add(Path('experiments/v4/study-012.md'))
    for study in ('009','010','011','012'):
        code.add(Path(f'scripts/run_v4_study{study}.py'))
    code.add(Path('scripts/verify_v4_study012_summary.py'))
    for study in ('009','010'):
        code.update(Path(f'data/v4-study-{study}/{n}.json') for n in ('metadata','results'))
        code.update(Path(f'docs/research/results/v4-study-{study}-{n}.json') for n in ('metadata','results','summary'))
    indexes=[]
    full_grid=set(product(range(96000,96005),(250,500),(0,100)))
    for study in ('009','010'):
        rows=json.loads(Path(f'docs/research/results/v4-study-{study}-results.json').read_text())
        check_coverage(rows,('seed','drive','mutation'),full_grid)
        indexes.append({(r['seed'],r['drive'],r['mutation']):r for r in rows})
    sources=set()
    for key in full_grid:
        seed,drive,mutation=key
        directory=Path(f'data/v4-study-005/seed-{seed}-drive-{drive}-mutation-{mutation}')
        sources.update(p for p in directory.iterdir() if p.is_file())
        observation=indexes[0][key];continuity=indexes[1][key]
        sources.update((Path('data/v4-study-009')/observation['observation'],
                        Path('data/v4-study-009')/observation['audit'],
                        Path('data/v4-study-010')/continuity['file']))
    return code,sources


def main():
    root=Path('data/v4-study-012')
    read=lambda p:json.loads(p.read_text())
    digest=lambda p:sha256(p.read_bytes()).hexdigest()
    meta=read(root/'metadata.json');results=read(root/'results.json');summary=read(root/'summary.json')
    if meta['status']!='complete' or meta['completed_branches']!=80:
        raise ValueError('complete audited cohort required')
    required_code,required_sources=expected_bindings()
    verify_bindings(meta['bindings_sha256'],required_code)
    verify_bindings(meta['source_bindings_sha256'],required_sources)
    grid=set(product(range(96000,96005),(250,),(0,100),(100,200,300,400),(True,False)))
    fields=('seed','drive','mutation','anchor','exchange')
    check_coverage(results,fields,grid)
    check_coverage(summary['pairs'],fields[:-1],{k[:-1] for k in grid})
    check_coverage(summary['source_means'],fields[:3],{k[:3] for k in grid})
    check_coverage(summary['groups'],('drive','mutation'),{(250,0),(250,100)})
    saved={};initials={};cohorts={};directories={};count=0
    code={p.name:digest(p) for p in Path('src/bitgenesis/v4').glob('*.py')}
    for row in results:
        key=tuple(row[k] for k in fields);directory=root/row['directory']
        assert row['status']=='complete' and row['horizon']==100 and type(row['exchange']) is bool
        for name in ('metadata','audit','continuity'):
            assert digest(directory/f'{name}.json')==row[name+'_sha256']
        branch=read(directory/'metadata.json');audit=read(directory/'audit.json')
        assert branch['status']=='complete' and branch['exchange']==row['exchange'] and branch['anchor']==row['anchor'] and branch['horizon']==100
        assert branch['code_sha256']==code
        assert audit['auditor_sha256']==code['exchange_branch_audit.py']
        source=Path(branch['source'])
        source_meta=read(source/'metadata.json')
        assert (source_meta['seed'],source_meta['drive_per_thousand'],source_meta['mutation_per_thousand'])==key[:3]
        source_hashes={p.name:digest(p) for p in source.iterdir() if p.is_file()}
        assert source_hashes==branch['source_sha256']==branch['source_sha256_after']==audit['input_sha256']
        assert audit==row['audit']
        assert audit['ticks']==100 and audit['output_sha256']==branch['output_sha256']
        verify_bindings({str(directory/name):h for name,h in branch['output_sha256'].items()},
            {directory/name for name in ('initial.json','steps.jsonl','final.json','continuity.json','summary.json')})
        records=read(directory/'continuity.json');count+=len(records)
        assert recount(records)==row['summary']
        saved[key]=row['summary']['fractions'];initials[key]=read(directory/'initial.json')
        cohorts[key]=[(r['component'],r['anchor_members'],r['anchor_size'],r['whole_world_anchor']) for r in records]
        directories[key]=directory
    by_pair={}
    for row in summary['pairs']:
        key=tuple(row[k] for k in fields[:-1]);on,off=(*key,True),(*key,False)
        assert initials[on]==initials[off] and cohorts[on]==cohorts[off]
        expected={}
        for metric in METRICS:
            a,b=saved[on][metric],saved[off][metric]
            assert (a is None)==(b is None)
            expected[metric]=dict(on=a,off=b,difference=str(Fraction(a)-Fraction(b)) if a is not None else None)
        assert row['metrics']==expected
        by_pair[key]={k:v['difference'] for k,v in expected.items()}
        with (directories[on]/'steps.jsonl').open() as left,(directories[off]/'steps.jsonl').open() as right:
            for tick,(a,b) in enumerate(zip(left,right,strict=True),1):
                a,b=json.loads(a)['physical'],json.loads(b)['physical']
                assert a['directions']==b['directions'] and a['mutation_tickets']==b['mutation_tickets']
                assert [i['proposed'] for i in a['driven']['inputs']]==[i['proposed'] for i in b['driven']['inputs']]
                assert b['driven']['interaction']['transfers']==[]
                if tick==1:
                    for field in ('inputs','energy_before','energy_after','imported','rejected_import','leakage','spent'):
                        assert a['driven'][field]==b['driven'][field]
                    for field in ('bonds','spent'):
                        assert a['driven']['interaction'][field]==b['driven']['interaction'][field]
            assert tick==100
    by_source={}
    for row in summary['source_means']:
        key=tuple(row[k] for k in fields[:3])
        expected={m:average([by_pair[(*key,a)][m] for a in (100,200,300,400)]) for m in METRICS}
        assert row['metrics']==expected
        by_source[key]=expected
    for row in summary['groups']:
        expected={m:average([by_source[(s,row['drive'],row['mutation'])][m]['mean'] for s in range(96000,96005)]) for m in METRICS}
        assert row['metrics']==expected
    proof=dict(status='verified',branches=80,pairs=40,sources=10,component_records=count,
        results_sha256=digest(root/'results.json'),summary_sha256=digest(root/'summary.json'),
        verifier_sha256=digest(Path(__file__)),
        scope='complete saved-record recount, same initial cohorts/tapes, first-step isolation, exact paired hierarchical means and audit hash bindings')
    with (root/'aggregation-verification.json').open('x') as stream:
        stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
