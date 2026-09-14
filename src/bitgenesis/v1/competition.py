"""Matched founder allocations; group labels remain analysis-only."""
from fractions import Fraction
import json
from pathlib import Path

from .audit import audit
from .controller import Genome
from .runner import run, save


def compete(output, config, seed, steps, genome, control='blind', swap=0,
            max_actor_records=1000000):
    if type(swap) is not int or swap not in (0,1):
        raise ValueError('swap must be 0 or 1')
    if config.founders < 2 or config.founders % 2 or config.mutation_per_thousand != 0:
        raise ValueError('competition requires even founder count and disabled mutation')
    if control not in ('intact','blind','shuffled') or not isinstance(genome, Genome):
        raise ValueError('invalid competition controller or control')
    half = config.founders // 2
    groups = {str(i): ('intact' if (i < half) != bool(swap) else 'control')
              for i in range(config.founders)}
    assignments = [{'weights': list(genome.weights),
                    'mode': 'intact' if groups[str(i)] == 'intact' else control}
                   for i in range(config.founders)]
    run(output, config, seed, steps, max_actor_records=max_actor_records,
        founder_assignments=assignments)
    verification = audit(output)
    root = Path(output)
    save(root/'audit.json', verification)
    lineage = json.loads((root/'final.json').read_text(encoding='utf-8'))['lineage']
    result = {'seed':seed, 'swap':swap, 'control':control, 'initial_per_group':half,
              'founder_groups':groups, 'verification':verification,
              'groups':{}}
    for group in ('intact','control'):
        members = [o for o in lineage if groups[str(o['founder'])] == group]
        living = [o for o in members if o['death_tick'] is None]
        result['groups'][group] = {'population':len(living),
            'births':sum(o['parent'] is not None for o in members),
            'deaths':len(members)-len(living), 'energy':sum(o['energy'] for o in living)}
    n = result['groups']['intact']['population']
    m = result['groups']['control']['population']
    result['contrast'] = str(Fraction(n-m,half))
    result['intact_fraction'] = str(Fraction(n,n+m)) if n+m else None
    result['status'] = 'both_present' if n and m else 'intact_only' if n else 'control_only' if m else 'both_extinct'
    save(root/'competition.json',result)
    return result
