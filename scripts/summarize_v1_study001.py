"""Exact source-level study001 aggregation, rejecting incomplete grids."""
from fractions import Fraction
from itertools import product
from random import Random


def summarize(rows, available_sources):
    sources=sorted(available_sources)
    if len(sources)!=len(set(sources)) or not sources or any(s not in range(72000,72010) for s in sources):
        raise ValueError('invalid available sources')
    expected=set(product(sources,('descendant','founder','randomized'),('blind','shuffled','intact'),
                         range(73000,73005),(15,30),(0,1)))
    values={}
    for row in rows:
        key=tuple(row[k] for k in ('source','kind','control','seed','renewal','swap'))
        if key not in expected or key in values:
            raise ValueError('unexpected or duplicate trial')
        counts=[row['groups'][g]['population'] for g in ('intact','control')]
        if any(type(n) is not int or n<0 for n in counts) or sum(counts)>256 or row['initial_per_group']!=16:
            raise ValueError('invalid terminal counts')
        contrast=Fraction(counts[0]-counts[1],16)
        if str(contrast)!=row['contrast']:
            raise ValueError('contrast inconsistent with raw counts')
        values[key]=contrast
    if set(values)!=expected:
        raise ValueError('incomplete evaluation grid')
    source_results=[]
    primary=[]
    for source in sources:
        effects={}
        regimes={}
        for kind,control in product(('descendant','founder','randomized'),('blind','shuffled','intact')):
            for renewal in (15,30):
                regimes[f'{kind}/{control}/{renewal}']=sum((values[(source,kind,control,seed,renewal,swap)]
                    for seed in range(73000,73005) for swap in (0,1)),Fraction(0))/10
            effects[f'{kind}/{control}']=(regimes[f'{kind}/{control}/15']+regimes[f'{kind}/{control}/30'])/2
        effect=effects['descendant/blind']-effects['founder/blind']
        primary.append(effect)
        source_results.append({'source':source,'primary':str(effect),
            'descendant_minus_randomized':str(effects['descendant/blind']-effects['randomized/blind']),
            'effects':{k:str(v) for k,v in effects.items()},
            'regimes':{k:str(v) for k,v in regimes.items()}})
    mean=sum(primary,Fraction(0))/len(primary)
    interval=None
    if len(primary)>=2:
        rng=Random(76000)
        bootstrap=sorted(sum((rng.choice(primary) for _ in primary),Fraction(0))/len(primary) for _ in range(10000))
        interval=[str(bootstrap[249]),str(bootstrap[9749])]
    return {'training_worlds':10,'available_sources':sources,
            'unavailable_sources':[s for s in range(72000,72010) if s not in sources],
            'evaluated_trials':len(rows),'sources':source_results,
            'primary_mean':str(mean),'exploratory_95pct_interval':interval,
            'minimum_mean_effect':'1/16','sufficient_available_sources':len(sources)>=5,
            'interpretation':'No positive stage claim without all preregistered outcome and behavioral gates.'}
