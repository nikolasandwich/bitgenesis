"""Independent V1 decision arithmetic from recorded inputs and birth genomes."""
from itertools import permutations


def check_decision(record, genome, mode):
    def require(condition, message):
        if not condition:
            raise ValueError(message)
    eligible_energy = record['energy_before'] - record['basal'] - record['decision']
    keys = ('inputs', 'sensed', 'permutation', 'tie_ticket')
    if eligible_energy <= 0:
        require(record['action'] is None and not any(k in record for k in keys),
                'decision fields on ineligible actor')
        return
    require(all(k in record for k in keys), 'missing decision fields')
    values, sensed = record['inputs'], record['sensed']
    require(len(values) == len(sensed) == 7, 'decision input dimensions')
    require(all(type(v) is int and 0 <= v <= 1000 for v in values + sensed), 'decision input bounds')
    require(values[5:] == [min(1000, 1000 * eligible_energy // 160), 1000], 'post-charge energy input')
    permutation, ticket = record['permutation'], record['tie_ticket']
    require(type(permutation) is int and 0 <= permutation < 24
            and type(ticket) is int and 0 <= ticket < 60, 'decision ticket bounds')
    if mode == 'intact':
        expected = values
    elif mode == 'blind':
        expected = [0] * 5 + values[5:]
    elif mode == 'shuffled':
        order = list(permutations(range(4)))[permutation]
        expected = [values[0]] + [values[i+1] for i in order] + values[5:]
    else:
        raise ValueError('unknown intervention')
    require(sensed == expected, 'sensory intervention mismatch')
    scores = [sum(genome[action * 7 + i] * sensed[i] for i in range(7)) for action in range(5)]
    maxima = [i for i, score in enumerate(scores) if score == max(scores)]
    require(type(record['action']) is int and record['action'] == maxima[ticket % len(maxima)], 'controller action mismatch')
