"""Independent reconstruction and actor-level recount of one-step reset contrasts."""
import json
from fractions import Fraction
from hashlib import sha256
from itertools import product
from pathlib import Path
from bitgenesis.v4.exchange_branch_audit import physical_step
from bitgenesis.v4.hereditary_audit import audit as source_audit
from scripts.verify_v4_study012_summary import expected_bindings, verify_bindings, check_coverage

REASONS=('dissolved','energy','occupied','raw_material','collision','formed')
METRICS=('births','deaths','energy_eligible','occupied')
read=lambda p:json.loads(Path(p).read_text())
digest=lambda p:sha256(Path(p).read_bytes()).hexdigest()


def canonical_source(recorded, row):
    expected=Path('data/v4-study-005')/f"seed-{row['seed']}-drive-250-mutation-{row['mutation']}"
    source=Path(recorded).resolve()
    if source!=expected.resolve():raise ValueError('canonical historical source required')
    return source


def recount(initial,on,off,threshold):
    actors={i for i,u in enumerate(initial) if u is not None};labels={};counts={}
    for name,arm in (('on',on),('off',off)):
        assignments={i:'dissolved' for i in arm['material']['dissolved']}
        if len(assignments)!=len(arm['material']['dissolved']):raise ValueError('duplicate dissolved actor')
        for p in arm['material']['proposals']:
            if p['source'] in assignments or p['reason'] not in REASONS[1:]:raise ValueError('invalid proposal actor')
            assignments[p['source']]=p['reason']
        if set(assignments)!=actors:raise ValueError('actor coverage')
        labels[name]=assignments
        counts[name]=dict(births=sum(v=='formed' for v in assignments.values()),
            deaths=sum(v=='dissolved' for v in assignments.values()),
            energy_eligible=sum(u is not None and u['energy']>=threshold for u in arm['interaction_units']),
            occupied=sum(u is not None for u in arm['units']))
        if counts[name]['energy_eligible']!=sum(v in REASONS[2:] for v in assignments.values()):
            raise ValueError('energy eligibility and reason margins disagree')
        if counts[name]['occupied']!=len(actors)+counts[name]['births']-counts[name]['deaths']:
            raise ValueError('population balance')
    matrix=[[0]*6 for _ in range(6)]
    for i in actors:matrix[REASONS.index(labels['on'][i])][REASONS.index(labels['off'][i])]+=1
    differences={m:counts['on'][m]-counts['off'][m] for m in METRICS}
    return dict(initial_occupied=len(actors),counts=counts,differences=differences,actor_matrix=matrix,
        birth_gains=sum(matrix[5][:5]),birth_losses=sum(matrix[i][5] for i in range(5)))


def total(metrics):
    if not metrics:raise ValueError('nonempty complete observations required')
    n=len(metrics);totals={side:{m:sum(r['counts'][side][m] for r in metrics) for m in METRICS} for side in ('on','off')}
    differences={m:totals['on'][m]-totals['off'][m] for m in METRICS}
    signs={m:{'positive':sum(r['differences'][m]>0 for r in metrics),
              'zero':sum(r['differences'][m]==0 for r in metrics),
              'negative':sum(r['differences'][m]<0 for r in metrics)} for m in METRICS}
    return dict(steps=n,totals=totals,differences=differences,means={m:str(Fraction(differences[m],n)) for m in METRICS},
        step_signs=signs,actor_matrix=[[sum(r['actor_matrix'][i][j] for r in metrics) for j in range(6)] for i in range(6)],
        birth_gains=sum(r['birth_gains'] for r in metrics),birth_losses=sum(r['birth_losses'] for r in metrics))


def main():
    root=Path('data/v4-study-013');meta=read(root/'metadata.json');rows=read(root/'results.json');summary=read(root/'summary.json')
    if meta['status']!='complete' or meta['completed_sources']!=10 or meta['completed_pairs']!=4000:
        raise ValueError('complete reset cohort required')
    assert meta['planned_sources']==10 and meta['planned_pairs']==4000 and meta['independent_new_samples']==0
    assert meta['known_first_pairs']==40 and meta['known_first_pair_ticks']==[101,201,301,401]
    code,sources=expected_bindings()
    code.update(Path(p) for p in ('experiments/v4/study-013.md','scripts/run_v4_study013.py','scripts/verify_v4_study013_summary.py'))
    verify_bindings(meta['bindings_sha256'],code);verify_bindings(meta['source_bindings_sha256'],sources)
    check_coverage(rows,('seed','drive','mutation'),set(product(range(96000,96005),(250,),(0,100))))
    check_coverage(summary['groups'],('drive','mutation'),{(250,0),(250,100)})
    verified=[];n_pairs=0;actors=0;zero_transfer_pairs=0
    for row in rows:
        directory=root/row['directory'];sm=read(directory/'metadata.json')
        assert row['status']==sm['status']=='complete'
        assert sm['schema']=='v4-study013-source-1' and (sm['start'],sm['end'],sm['steps'])==(101,500,400)
        for name,filename in (('metadata','metadata.json'),('steps','paired-steps.jsonl'),('summary','summary.json')):
            assert digest(directory/filename)==row[name+'_sha256']
        verify_bindings({str(directory/name):h for name,h in sm['output_sha256'].items()},
                        {directory/'paired-steps.jsonl',directory/'summary.json'})
        source=canonical_source(sm['source'],row);cfg=read(source/'metadata.json')
        assert (cfg['seed'],cfg['drive_per_thousand'],cfg['mutation_per_thousand'])==(row['seed'],250,row['mutation'])
        original={str(p):digest(p) for p in source.iterdir() if p.is_file()}
        assert {Path(p).name:h for p,h in original.items()}==sm['source_sha256']==sm['source_sha256_after']
        assert sm['source_audit']==source_audit(source)
        history=[json.loads(line) for line in (source/'steps.jsonl').read_text().splitlines()]
        metrics=[]
        with (directory/'paired-steps.jsonl').open() as stream:
            for tick,line in enumerate(stream,101):
                pair=json.loads(line)
                assert pair['tick']==tick and tick<=500
                origin=history[tick-2];tape=history[tick-1]
                on,off=pair['on'],pair['off']
                assert on==physical_step(origin['units'],origin['raw'],cfg,tape,True)==tape
                assert off==physical_step(origin['units'],origin['raw'],cfg,tape,False)
                for field in ('inputs','energy_before','energy_after','imported','rejected_import','leakage','spent'):
                    assert on['driven'][field]==off['driven'][field]
                for field in ('bonds','spent'):assert on['driven']['interaction'][field]==off['driven']['interaction'][field]
                assert off['driven']['interaction']['transfers']==[]
                if not on['driven']['interaction']['transfers']:
                    assert on==off;zero_transfer_pairs+=1
                expected=recount(origin['units'],on,off,cfg['threshold'])
                assert pair['metrics']==expected
                assert expected['differences']['births']==expected['birth_gains']-expected['birth_losses']
                actors+=expected['initial_occupied'];metrics.append(expected)
        assert len(metrics)==400
        expected=total(metrics)
        assert row['summary']==read(directory/'summary.json')==expected
        verified.append((row['mutation'],expected));n_pairs+=len(metrics)
        verify_bindings(original,{Path(p) for p in original})
    for group in summary['groups']:
        selected=[s for mutation,s in verified if mutation==group['mutation']]
        expected={m:dict(mean=str(sum(Fraction(s['means'][m]) for s in selected)/5),available=5,missing=0) for m in METRICS}
        assert group['metrics']==expected
    verify_bindings(meta['bindings_sha256'],code);verify_bindings(meta['source_bindings_sha256'],sources)
    assert n_pairs==4000
    proof=dict(status='verified',sources=10,pairs=4000,physical_reconstructions=8000,actors=actors,
        zero_transfer_pairs=zero_transfer_pairs,reused_study012_first_pairs=40,
        results_sha256=digest(root/'results.json'),summary_sha256=digest(root/'summary.json'),
        verifier_sha256=digest(Path(__file__)),
        scope='independent full physical/hereditary reconstruction; all actor outcomes, margins, signs, reset states and exact means; full binding inventories')
    with (root/'aggregation-verification.json').open('x') as stream:stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':main()
