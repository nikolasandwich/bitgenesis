"""Construct distinct erased patterns with identical surviving dynamics."""
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
from random import Random
from bitgenesis.v4.damage import damage
from bitgenesis.v4.growing import step
from bitgenesis.v4.local import Unit


def check():
    width=height=5
    patch=[6,7,11,12]
    first=[Unit(i%4,32) for i in range(25)]
    second=list(first)
    for i in patch:
        second[i]=Unit((first[i].material+1)%4,first[i].energy)
    raw=[1]*25
    a,ar,alog=damage(first,raw,patch)
    b,br,blog=damage(second,raw,patch)
    assert a==b and ar==br
    assert alog!=blog  # Observer records retain erased labels; dynamics do not.
    rng=Random(90902)
    digest=sha256()
    for tick in range(1,129):
        proposals=[8 if rng.randrange(1000)<500 else 0 for _ in a]
        directions=[rng.randrange(4) for _ in a]
        a,ar,ra=step(a,ar,width,height,proposals,directions)
        b,br,rb=step(b,br,width,height,proposals,directions)
        assert (a,ar,ra)==(b,br,rb)
        digest.update(json.dumps(dict(tick=tick,units=[None if u is None else asdict(u) for u in a],raw=ar,record=ra),sort_keys=True).encode())
    return dict(scope='constructed information-erasure counterexample, not a scientific recovery cohort',
        seed=90902,steps=128,width=width,height=height,patch=patch,
        first_labels=[first[i].material for i in patch],second_labels=[second[i].material for i in patch],
        equal_after_damage=True,observer_records_differ=True,identical_continued_transitions=128,
        final_labels=[None if a[i] is None else a[i].material for i in patch],
        trajectory_sha256=digest.hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest(),
        source_sha256={p.name:sha256(p.read_bytes()).hexdigest() for p in Path('src/bitgenesis/v4').glob('*.py')})


if __name__=='__main__':
    result=check()
    with Path('docs/research/results/v4-information-loss.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result,indent=2))
