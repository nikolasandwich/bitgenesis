"""Explicit between-step experimental operations, outside v3-run-1 semantics."""

INTERVENTION_VERSION = 'v3-boundary-1'


def boundary(world, *, remove_founder=None, b_additions=()):
    """Remove a living lineage, then inject B at ordered sites without RNG draws.

    Caller must save boundary records in a separate assay format. Ordinary V3
    audits intentionally do not accept this altered life history as a base run.
    """
    additions = list(b_additions)
    if remove_founder is not None:
        if (type(remove_founder) is not int or remove_founder not in world.lineage
                or world.lineage[remove_founder].parent is not None):
            raise ValueError('removal requires a successfully constructed founder ID')
    for item in additions:
        if (not isinstance(item, (tuple, list)) or len(item) != 2
                or any(type(v) is not int for v in item)
                or not 0 <= item[0] < len(world.substrate_b) or item[1] < 0):
            raise ValueError('B additions require valid (site, nonnegative amount) pairs')
    before = world.total_energy()
    removed = []
    if remove_founder is not None:
        for identifier, organism in list(world.organisms.items()):
            if organism.founder != remove_founder:
                continue
            removed.append(dict(id=identifier, founder=organism.founder, x=organism.x,
                                y=organism.y, exported_energy=organism.energy))
            organism.energy = 0
            organism.death_tick = world.tick
            del world.organisms[identifier]
            del world.occupied[(organism.x, organism.y)]
    deposits = []
    for site, proposed in additions:
        stock = world.substrate_b[site]
        accepted = min(proposed, world.config.capacity - stock)
        world.substrate_b[site] += accepted
        deposits.append(dict(site=site, before=stock, proposed=proposed, accepted=accepted,
                             rejected=proposed-accepted, after=world.substrate_b[site]))
    exported = sum(o['exported_energy'] for o in removed)
    accepted = sum(d['accepted'] for d in deposits)
    after = world.total_energy()
    if after != before - exported + accepted:
        raise AssertionError('boundary energy mismatch')
    record = dict(event='experimental_boundary', rules=INTERVENTION_VERSION, tick=world.tick,
                  remove_founder=remove_founder, removed=removed, b_deposits=deposits,
                  energy_before=before, exported_energy=exported, imported_energy=accepted,
                  rejected_import=sum(d['rejected'] for d in deposits), energy_after=after)
    world.events.append(record)
    return record
