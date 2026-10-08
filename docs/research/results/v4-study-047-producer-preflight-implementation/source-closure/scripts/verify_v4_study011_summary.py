"""Independently recount saved demographic records and exact hierarchical means."""
import json
from pathlib import Path
from hashlib import sha256
from fractions import Fraction
from collections import defaultdict
from itertools import product



def require_coverage(rows, fields, expected):
    keys=[tuple(row[field] for field in fields) for row in rows]
    if len(keys)!=len(expected) or set(keys)!=expected:
        raise ValueError('incomplete or duplicate verification coverage: '+','.join(fields))


def main():
    root=Path('data/v4-study-011')
    read=lambda p:json.loads(p.read_text(encoding='utf-8'))
    metadata=read(root/'metadata.json')
    if metadata['status']!='complete' or metadata['completed_sources']!=20:
        raise ValueError('complete cohort required')
    results=read(root/'results.json');summary=read(root/'summary.json')
    fields=('stasis','births_only','with_deaths','with_original_deaths','with_descendant_deaths','eligible_rate')
    definitions=(('interaction','contact'),('interaction','material'),('interaction','bond'),('final','contact'),('final','material'))
    grid=set(product(range(96000,96005),(250,500),(0,100)))
    require_coverage(results,('seed','drive','mutation'),grid)
    expected_panels={(p,b,a,100) for p,b in definitions for a in (100,200,300,400)}
    require_coverage(summary['source_means'],('seed','drive','mutation','phase','boundary'),
                     {(s,d,m,p,b) for s,d,m in grid for p,b in definitions})
    require_coverage(summary['groups'],('phase','boundary','drive','mutation'),
                     {(p,b,d,m) for p,b in definitions for d,m in product((250,500),(0,100))})
    source_means={};total=panels_checked=0
    for source in results:
        path=root/source['file']
        assert sha256(path.read_bytes()).hexdigest()==source['sha256']
        data=read(path)
        require_coverage(data['panels'],('phase','boundary','anchor','horizon'),expected_panels)
        require_coverage(source['summary'],('phase','boundary','anchor','horizon'),expected_panels)
        saved={(p['phase'],p['boundary'],p['anchor'],p['horizon']):p for p in source['summary']}
        fractions=defaultdict(list)
        for panel in data['panels']:
            key=panel['phase'],panel['boundary'],panel['anchor'],panel['horizon']
            row=saved[key];records=panel['records'];n=len(records);denom=panel['initial_multi_components']
            assert n==row['eligible_components']==panel['eligible_components']
            assert denom==row['initial_multi_components']
            counts=dict(stasis=0,births_only=0,with_deaths=0,with_original_deaths=0,with_descendant_deaths=0)
            event_totals=dict(births=0,deaths=0,original_deaths=0,descendant_deaths=0)
            for r in records:
                assert r['births']==len(r['birth_ids']) and r['deaths']==len(r['death_ids'])
                assert r['deaths']==r['original_deaths']+r['descendant_deaths']
                assert r['endpoint_population']==r['anchor_size']+r['births']-r['deaths']
                assert r['endpoint_original_survivors']==r['anchor_size']-r['original_deaths']
                category='with_deaths' if r['deaths'] else 'births_only' if r['births'] else 'stasis'
                assert r['category']==category
                counts[category]+=1
                counts['with_original_deaths']+=r['original_deaths']>0
                counts['with_descendant_deaths']+=r['descendant_deaths']>0
                for metric in event_totals:event_totals[metric]+=r[metric]
            assert counts==row['counts'] and event_totals==row['event_totals']
            assert row['whole_world_cohorts']==sum(r['whole_world_anchor'] for r in records)
            assert row['non_world_with_events']==sum(not r['whole_world_anchor'] and (r['births']>0 or r['deaths']>0) for r in records)
            for metric in fields:
                divisor=denom if metric=='eligible_rate' else n
                numerator=n if metric=='eligible_rate' else counts[metric]
                value=Fraction(numerator,divisor) if divisor else None
                assert row['fractions'][metric]==(str(value) if value is not None else None)
                fractions[(panel['phase'],panel['boundary'],metric)].append(value)
            total+=n;panels_checked+=1
        for key,values in fractions.items():
            assert len(values)==4
            present=[v for v in values if v is not None]
            source_means[(source['seed'],source['drive'],source['mutation'],*key)]=(sum(present)/len(present) if present else None,len(present))
    assert len(results)==20 and panels_checked==400
    for row in summary['source_means']:
        for metric in fields:
            v,n=source_means[(row['seed'],row['drive'],row['mutation'],row['phase'],row['boundary'],metric)]
            assert row['metrics'][metric]==dict(mean=str(v) if v is not None else None,available=n,missing=4-n)
    for row in summary['groups']:
        for metric in fields:
            values=[source_means[(s,row['drive'],row['mutation'],row['phase'],row['boundary'],metric)][0] for s in range(96000,96005)]
            present=[v for v in values if v is not None]
            assert row['metrics'][metric]==dict(mean=str(sum(present)/len(present)) if present else None,available=len(present),missing=5-len(present))
    proof=dict(status='complete',sources=20,panels=panels_checked,cohort_windows=total,
        results_sha256=sha256((root/'results.json').read_bytes()).hexdigest(),
        summary_sha256=sha256((root/'summary.json').read_bytes()).hexdigest(),
        verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='independent demographic recount, conservation, conditional denominators, anchor/source means')
    with (root/'aggregation-verification.json').open('x',encoding='utf-8') as stream:
        stream.write(json.dumps(proof,indent=2)+'\n')
    print(json.dumps(proof))


if __name__=='__main__':
    main()
