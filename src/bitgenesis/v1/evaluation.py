"""Read-only analysis tools; no scores feed back into simulation."""
from fractions import Fraction
from hashlib import sha256
from itertools import permutations
import json
from pathlib import Path
from random import Random

from .audit import audit


def action_distribution(weights, values, mode='intact'):
    """Exact probabilities, preserving all 24 permutation multiplicities."""
    if len(weights) != 35 or any(type(w) is not int or not -100 <= w <= 100 for w in weights):
        raise ValueError('invalid weights')
    if len(values) != 7 or any(type(v) is not int or not 0 <= v <= 1000 for v in values) or values[-1] != 1000:
        raise ValueError('invalid normalized inputs')
    if mode == 'intact':
        variants = [list(values)]
    elif mode == 'blind':
        variants = [[0]*5 + list(values[5:])]
    elif mode == 'shuffled':
        variants = [[values[0]] + [values[i+1] for i in order] + list(values[5:])
                    for order in permutations(range(4))]
    else:
        raise ValueError('invalid mode')
    probabilities = [Fraction(0) for _ in range(5)]
    for variant in variants:
        scores = [sum(weights[action*7+i]*variant[i] for i in range(7)) for action in range(5)]
        winners = [i for i, value in enumerate(scores) if value == max(scores)]
        for winner in winners:
            probabilities[winner] += Fraction(1, len(variants)*len(winners))
    return tuple(probabilities)


def total_variation(first, second):
    if len(first) != 5 or len(second) != 5 or any(v < 0 for v in (*first, *second)) or sum(first) != 1 or sum(second) != 1:
        raise ValueError('five normalized action probabilities required')
    return sum((abs(a-b) for a,b in zip(first,second)), Fraction(0)) / 2


def sample_endpoint(directory, count, analysis_seed):
    """Uniform survivors, sorted-ID input, exact parent-chain founder trace.

    The analysis stream is separate from every world stream. This function
    never writes into the input run or draws simulation random numbers.
    """
    if type(count) is not int or count < 1 or type(analysis_seed) is not int:
        raise ValueError('positive count and integer analysis seed required')
    root = Path(directory)
    verification = audit(root)
    initial = json.loads((root/'initial.json').read_text(encoding='utf-8'))
    final = json.loads((root/'final.json').read_text(encoding='utf-8'))
    meta = json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    lineage = {o['id']:o for o in final['lineage']}
    founders = {o['id']:o for o in initial['lineage']}
    survivors = sorted(i for i,o in lineage.items() if o['death_tick'] is None)
    selected = Random(analysis_seed).sample(survivors, min(count,len(survivors)))
    samples = []
    for identifier in selected:
        current = identifier
        chain = []
        while True:
            if current in chain:
                raise ValueError('ancestry cycle')
            chain.append(current)
            parent = lineage[current]['parent']
            if parent is None:
                break
            current = parent
        if current != lineage[identifier]['founder'] or current not in founders:
            raise ValueError('untraceable founder')
        samples.append({'id':identifier, 'founder_id':current, 'ancestry':chain,
                        'genome':lineage[identifier]['genome'],
                        'founder_genome':founders[current]['genome']})
    return {'schema':'v1-endpoint-sample-1', 'training_seed':meta['seed'],
            'tick':final['tick'], 'requested_count':count, 'sample_count':len(samples),
            'survivors':len(survivors), 'status':'available' if samples else 'extinct',
            'analysis_seed':analysis_seed, 'samples':samples,
            'conditional_estimate':None,
            'input_sha256':verification['input_sha256'],
            'metadata_sha256':verification['metadata_sha256'],
            'analysis_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}
