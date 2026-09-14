"""Passive B-unit attribution under explicit oldest/newest-first conventions."""
from collections import Counter, deque


def trace(initial_b, final_b, lineage, steps, convention):
    if convention not in ('oldest_first','newest_first'):
        raise ValueError('unknown attribution convention')
    pools=[deque([None]*amount) for amount in initial_b]
    founders={o['id']:o['founder'] for o in lineage}
    transfers=Counter()
    consumed=released=0
    for row in steps:
        for actor in row['actors']:
            feeding=actor['feeding']
            if feeding is None:
                continue
            pool=pools[feeding['site']]
            if len(pool)!=feeding['b_before']:
                raise ValueError('provenance pool does not match recorded stock')
            recipient=actor['id']
            for _ in range(feeding['consumed_b']):
                donor=pool.popleft() if convention=='oldest_first' else pool.pop()
                transfers[(donor,recipient)]+=1
                consumed+=1
            # Only retained release enters the pool; overflow already dissipated.
            pool.extend([recipient]*feeding['released_b'])
            released+=feeding['released_b']
            if len(pool)!=feeding['remaining_b']:
                raise ValueError('postfeeding stock mismatch')
    if [len(pool) for pool in pools]!=final_b:
        raise ValueError('terminal provenance stock mismatch')
    categories=dict(initial=0,self=0,same_founder_other_individual=0,other_founder=0)
    edges=[]
    for (donor,recipient),amount in sorted(transfers.items(),key=lambda pair: (-1 if pair[0][0] is None else pair[0][0],pair[0][1])):
        category=('initial' if donor is None else 'self' if donor==recipient else
                  'same_founder_other_individual' if founders[donor]==founders[recipient] else 'other_founder')
        categories[category]+=amount
        edges.append(dict(donor=donor,recipient=recipient,units=amount,category=category))
    if sum(initial_b)+released-consumed!=sum(final_b):
        raise ValueError('global attribution ledger mismatch')
    return dict(convention=convention,consumed_b=consumed,released_b=released,
                retained_b=sum(final_b),categories=categories,edges=edges)
