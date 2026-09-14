"""Common-prefix ecological removal assay with explicit provenance and limits."""
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

from .audit import audit
from .branches import run_branch, donor_schedule
from .branch_replay import verify
from .runner import run, save, state, encoded
from .world import World


def select_target(final, steps):
    """Largest cumulative retained B release among living founder lineages.

    Require at least two living lineages, positive release, and break ties by
    smallest founder ID. This selects a putative donor, not proven mutualism.
    """
    founders={o['id']:o['founder'] for o in final['lineage']}
    living={o['founder'] for o in final['lineage'] if o['death_tick'] is None}
    release=Counter()
    for row in steps:
        for actor in row['actors']:
            if actor['feeding'] is not None:
                release[founders[actor['id']]]+=actor['feeding']['released_b']
    eligible=[f for f in living if release[f]>0] if len(living)>=2 else []
    target=min(eligible,key=lambda f:(-release[f],f)) if eligible else None
    return dict(target=target,living_founders=sorted(living),
                retained_release={str(f):release[f] for f in sorted(set(founders.values()))},
                status='available' if target is not None else 'unavailable')


def run_assay(output,config,seed,prefix_steps,branch_steps,*,founder_genomes=None,max_actor_records=1000000):
    if type(prefix_steps) is not int or prefix_steps<1 or type(branch_steps) is not int or branch_steps<1:
        raise ValueError('positive prefix and branch horizons required')
    if max(prefix_steps,branch_steps)>100000 or config.width*config.height*max(prefix_steps,branch_steps)>max_actor_records:
        raise ValueError('assay horizon or record budget exceeded')
    root=Path(output)
    root.mkdir(parents=True,exist_ok=False)
    metadata=dict(schema='v3-assay-1',status='running',seed=seed,prefix_steps=prefix_steps,
                  branch_steps=branch_steps,verification_scope='independent base-prefix audit and boundary reconstruction; same-engine branch replay')
    save(root/'metadata.json',metadata)
    try:
        run(root/'prefix',config,seed,prefix_steps,founder_genomes=founder_genomes,max_actor_records=max_actor_records)
        prefix_audit=audit(root/'prefix')
        save(root/'prefix-audit.json',prefix_audit)
        final=json.loads((root/'prefix/final.json').read_text())
        with (root/'prefix/steps.jsonl').open(encoding='utf-8') as stream:
            selection=select_target(final,(json.loads(line) for line in stream))
        save(root/'selection.json',selection)
        metadata['prefix_final_sha256']=sha256((root/'prefix/final.json').read_bytes()).hexdigest()
        if selection['target'] is None:
            result=dict(selection=selection,outcomes=None)
            save(root/'result.json',result)
            metadata.update(status='complete',outcome='unavailable',generated_ticks=prefix_steps)
            save(root/'metadata.json',metadata)
            return result
        origin=World(config,seed,founder_genomes=founder_genomes)
        for _ in range(prefix_steps):
            origin.step()
            origin.events.clear()
        if encoded(state(origin))!=encoded(final):
            raise ValueError('regenerated origin does not match audited prefix')
        target=selection['target']
        run_branch(root/'intact',origin,branch_steps,max_actor_records=max_actor_records)
        save(root/'intact-verification.json',verify(root/'intact',origin))
        schedule=donor_schedule(root/'intact',target)
        save(root/'schedule.json',dict(reference_steps_sha256=sha256((root/'intact/steps.jsonl').read_bytes()).hexdigest(),
                                      target=target,boundary_deposits=schedule))
        for name,deposits in (('removed',None),('replayed',schedule)):
            run_branch(root/name,origin,branch_steps,remove_founder=target,deposits=deposits,max_actor_records=max_actor_records)
            save(root/(name+'-verification.json'),verify(root/name,origin))
        outcomes={}
        for name in ('intact','removed','replayed'):
            endpoint=json.loads((root/name/'final.json').read_text())
            others=[o for o in endpoint['lineage'] if o['founder']!=target]
            outcomes[name]=dict(other_population=sum(o['death_tick'] is None for o in others),
                other_new_births=sum(o['birth_tick']>prefix_steps for o in others),
                summary=json.loads((root/name/'summary.json').read_text()))
        result=dict(selection=selection,outcomes=outcomes)
        save(root/'result.json',result)
        metadata.update(status='complete',outcome='available',
                        generated_ticks=2*prefix_steps+3*branch_steps,replay_ticks=3*branch_steps)
        save(root/'metadata.json',metadata)
        return result
    except BaseException as error:
        metadata.update(status='failed',error=f'{type(error).__name__}: {error}')
        save(root/'metadata.json',metadata)
        raise
