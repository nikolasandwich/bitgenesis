"""Saved interaction/proposal actor ledger; no simulation or random draws."""
from collections import Counter
from pathlib import Path
import subprocess
import time

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
REASONS = ('dissolved', 'energy', 'occupied', 'raw_material', 'collision', 'formed')
GRID = [(g, m, e, s) for g in GENOTYPES for m in MODES for e in (False, True) for s in range(120000, 120020)]
OUTPUT = Path('data/v4-study-026')


def require(value, message):
    if not value:
        raise ValueError(message)


def target_site(site, direction):
    x, y = site % 16, site // 16
    return (y*16+(x+1)%16, y*16+(x-1)%16, ((y+1)%16)*16+x, ((y-1)%16)*16+x)[direction]


def analyze_case(case, genotype):
    require(type(case['seed']) is int and type(case['exchange']) is bool and
            (genotype, case['mode'], case['exchange'], case['seed']) in GRID, 'case identity')
    from scripts.run_v4_copy_control import CONFIG
    require(case['config'] == CONFIG and len(case['rows']) == 32, 'fixed source configuration')
    parents = case['final']['parents']
    roots = []
    for i, parent in enumerate(parents):
        require((i < 3 and parent is None) or (i >= 3 and type(parent) is int and 0 <= parent < i), 'ordered root ancestry')
        roots.append(i if parent is None else roots[parent])

    def indexed(ids, units):
        require(len(ids) == len(units) == 256, 'full sites')
        found = {}
        for site, (identity, unit) in enumerate(zip(ids, units)):
            require((identity is None) == (unit is None), 'identity occupancy')
            if identity is not None:
                require(type(identity) is int and 0 <= identity < len(parents) and identity not in found, 'unique identity')
                require(type(unit['energy']) is int and 0 <= unit['energy'] <= 64, 'unit energy')
                found[identity] = site
        return found

    previous = case['initial']
    ids, units, raw = previous['site_ids'], previous['units'], previous['raw']
    require(indexed(ids, units) == {0: 85, 1: 86, 2: 204}, 'initial identities')
    expected_raw = [int(site in (101, 102, 117, 118)) for site in range(256)]
    require(raw == expected_raw, 'fixed initial raw')
    for site, label in ((85, 1), (86, 2), (204, 3)):
        program = [3]*4 if site == 204 else [0, 0, 0, label if genotype == 'heterogeneous' else 0]
        require(units[site] == dict(material=3 if site == 204 else 0, energy=64, program=program), 'initial genotype')
    seen = {0, 1, 2}
    steps = []
    for tick, row in enumerate(case['rows'], 1):
        p = row['physical']; interaction = p['interaction_units']; material = p['material']; driven = p['driven']
        require(type(row['tick']) is int and row['tick'] == p['tick'] == tick, 'ordered ticks')
        before = indexed(ids, units); after = indexed(row['site_ids'], p['units'])
        require(indexed(ids, interaction) == before, 'interaction actor coverage')
        require(len(raw) == len(p['raw']) == len(p['directions']) == len(driven['inputs']) == 256, 'full input grid')
        require(all(type(n) is int and n >= 0 for n in raw+p['raw']), 'raw tokens')
        require(all(type(d) is int and 0 <= d < 4 for d in p['directions']), 'direction tickets')
        for site, inp in enumerate(driven['inputs']):
            require(type(inp['site']) is int and inp['site'] == site, 'input site order')
            require(all(type(inp[k]) is int and inp[k] >= 0 for k in ('proposed', 'accepted', 'rejected', 'leakage')), 'integer inputs')
            accepted = 0 if units[site] is None else min(inp['proposed'], 64-units[site]['energy'])
            require(inp['accepted'] == accepted and inp['rejected'] == inp['proposed']-accepted, 'accepted input capacity')
            require(inp['leakage'] == (0 if units[site] is None else min(1, units[site]['energy']+accepted)), 'input leakage')
        require(driven['imported'] == p['imported'] == sum(v['accepted'] for v in driven['inputs']), 'import ledger')
        require(driven['rejected_import'] == p['rejected_import'] == sum(v['rejected'] for v in driven['inputs']), 'rejected ledger')
        energy_before = sum(u['energy'] for u in units if u is not None)
        energy_interaction = sum(u['energy'] for u in interaction if u is not None)
        require(p['energy_before'] == driven['energy_before'] == energy_before and
                driven['energy_after'] == material['energy_before'] == energy_interaction == energy_before+p['imported']-driven['spent'], 'interaction energy ledger')
        dissolved = [s for s, u in enumerate(interaction) if u is not None and u['energy'] == 0]
        require(material['dissolved'] == dissolved, 'dissolution coverage')
        stock = list(raw)
        for s in dissolved:
            stock[s] += 1
        survivors = {s for s, u in enumerate(interaction) if u is not None and u['energy'] > 0}
        proposals = material['proposals']
        require([v['source'] for v in proposals] == sorted(survivors), 'proposal actor coverage')
        by_site = {v['source']: v for v in proposals}
        candidates = Counter()
        preliminary = {}
        for site in survivors:
            target = target_site(site, p['directions'][site])
            reason = ('energy' if interaction[site]['energy'] < 16 else 'occupied' if target in survivors else 'raw_material' if stock[target] < 1 else 'candidate')
            preliminary[site] = reason
            if reason == 'candidate':
                candidates[target] += 1
        actors = []
        formed = []
        for site, identity in enumerate(ids):
            if identity is None:
                continue
            u = units[site]; inter = interaction[site]; direction = p['directions'][site]; target = target_site(site, direction)
            require(all(u[k] == inter[k] for k in ('material', 'program')), 'interaction genotype')
            reason = 'dissolved'
            expressed = None
            if site in survivors:
                proposal = by_site[site]
                reason = preliminary[site]
                if reason == 'candidate':
                    reason = 'collision' if candidates[target] > 1 else 'formed'
                require(proposal['target'] == target and proposal['direction'] == direction and proposal['reason'] == reason, 'saved proposal branch')
                if reason == 'formed':
                    expressed = proposal['material']
                    require(expressed == u['program'][direction], 'encoded material expression')
                    child = row['site_ids'][target]
                    require(type(child) is int and child not in seen and parents[child] == identity, 'birth ancestry')
                    require(p['units'][target]['material'] == expressed and p['units'][target]['program'] == u['program'], 'child genotype')
                    require(proposal['cost'] == 5 and proposal['child_energy'] == (inter['energy']-5)//2 and
                            proposal['parent_energy'] == inter['energy']-5-proposal['child_energy'], 'formation energy split')
                    require(p['units'][target]['energy'] == proposal['child_energy'] and p['units'][site]['energy'] == proposal['parent_energy'], 'saved formation energy')
                    formed.append((site, target, child))
            inp = driven['inputs'][site]
            actors.append(dict(tick=tick, site=site, identity=identity, root=roots[identity], direction=direction,
                               proposed=inp['proposed'], accepted=inp['accepted'], energy_before=u['energy'],
                               energy_interaction=inter['energy'], target=target, target_occupied=target in survivors,
                               raw_available=stock[target], reason=reason, encoded_material=u['program'][direction], formed_material=expressed))
        deaths = {ids[s] for s in dissolved}; births = {child for _, _, child in formed}
        require(deaths == set(before)-set(after) and births == set(after)-set(before) and len(births) == len(formed), 'identity event coverage')
        for identity in set(before)&set(after):
            site = before[identity]
            require(after[identity] == site and all(units[site][k] == p['units'][site][k] for k in ('material', 'program')), 'survivor identity')
            if by_site[site]['reason'] != 'formed':
                require(p['units'][site]['energy'] == interaction[site]['energy'], 'survivor energy')
        final_raw = list(stock)
        for _, target, _ in formed:
            final_raw[target] -= 1
        require(p['raw'] == final_raw, 'raw material ledger')
        final_energy = sum(u['energy'] for u in p['units'] if u is not None)
        require(material['spent'] == 5*len(formed) and p['spent'] == driven['spent']+material['spent'] and
                p['energy'] == p['energy_after'] == material['energy_after'] == final_energy == energy_before+p['imported']-p['spent'], 'final energy ledger')
        require(sum(raw)+len(before) == sum(final_raw)+len(after) == material['material_before'] == material['material_after'] == p['material_before'] == p['material_after'], 'mass ledger')
        steps.append(actors); seen.update(births)
        ids, units, raw = row['site_ids'], p['units'], p['raw']
    require(seen == set(range(len(parents))), 'complete ancestry coverage')
    require(ids == case['final']['site_ids'] and units == case['final']['units'] and raw == case['final']['raw'], 'final state')
    return dict(genotype=genotype, mode=case['mode'], seed=case['seed'], exchange=case['exchange'], steps=steps)


def summarize(records):
    require(all(type(r['seed']) is int and type(r['exchange']) is bool for r in records), 'strict identity')
    require([(r['genotype'], r['mode'], r['exchange'], r['seed']) for r in records] == GRID, 'complete ordered240 grid')
    for r in records:
        require(len(r['steps']) == 32, '32 saved steps')
        for tick, step in enumerate(r['steps'], 1):
            require([a['site'] for a in step] == sorted(set(a['site'] for a in step)) and all(a['tick'] == tick and a['root'] in (0, 1, 2) and a['reason'] in REASONS for a in step), 'ordered valid actors')
    def stats(actors):
        north = [a for a in actors if a['direction'] == 3]
        masks = Counter((a['energy_interaction'] < 16) + 2*a['target_occupied'] + 4*(a['raw_available'] < 1) for a in north if a['reason'] != 'dissolved')
        return dict(actor_steps=len(actors), proposed=sum(a['proposed'] for a in actors), accepted=sum(a['accepted'] for a in actors),
                    north_tickets=len(north), north_proposals=sum(a['reason'] != 'dissolved' for a in north),
                    north_nonzero_formed=sum(a['reason'] == 'formed' and a['formed_material'] != 0 for a in north),
                    reasons={k: sum(a['reason'] == k for a in actors) for k in REASONS},
                    north_reasons={k: sum(a['reason'] == k for a in north) for k in REASONS},
                    north_predicates={str(k): masks[k] for k in range(8)})
    result = []
    for g in GENOTYPES:
        for m in MODES:
            for e in (False, True):
                cases = [r for r in records if (r['genotype'], r['mode'], r['exchange']) == (g, m, e)]
                actors = [a for r in cases for step in r['steps'] for a in step]
                result.append(dict(genotype=g, mode=m, exchange=e, cases=len(cases), all=stats(actors), target=stats([a for a in actors if a['root'] in (0, 1)])))
    return result


def main():
    from scripts.north_opportunity_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic(); records = []; inventory = []
    meta = dict(status='running', planned_cases=240, completed_cases=0, saved_steps=0, new_simulation_steps=0,
                new_environment_sources=0, reused_environment_sources=20, new_independent_initial_worlds=0,
                time_limit_seconds=300, storage_limit_bytes=67108864,
                git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip())
    def budget():
        require(time.monotonic()-started < 300 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file()) < 67108864, 'bounded execution')
    def hashes():
        return {str(p.relative_to(OUTPUT)): digest(p) for p in sorted(OUTPUT.rglob('*.json')) if p.name != 'metadata.json'}
    def input_hashes(error_key):
        values = {}; meta[error_key] = {}
        for path in inventory:
            try:
                values[path] = digest(path)
            except BaseException as exc:
                meta[error_key][path] = repr(exc)
        return values
    try:
        meta['input_inventory_errors'] = {}
        inventory = input_paths(meta['input_inventory_errors']); meta['input_paths'] = inventory
        meta['input_sha256'] = input_hashes('input_read_errors_before')
        save(OUTPUT/'metadata.json', meta); save(OUTPUT/'records.json', records)
        before = bindings(); require(before == meta['input_sha256'], 'validated initial inputs')
        for genotype, path in source_cases():
            budget(); records.append(analyze_case(read(path), genotype))
            meta.update(completed_cases=len(records), saved_steps=32*len(records), elapsed_seconds=time.monotonic()-started)
            save(OUTPUT/'records.json', records); save(OUTPUT/'metadata.json', meta)
        save(OUTPUT/'summary.json', summarize(records))
        meta['input_sha256_after'] = bindings(); require(before == meta['input_sha256_after'], 'unchanged inputs')
        meta.update(status='complete', elapsed_seconds=time.monotonic()-started, output_sha256=hashes())
        budget(); save(OUTPUT/'metadata.json', meta); budget()
    except BaseException as exc:
        meta.update(status='failed', error=repr(exc), elapsed_seconds=time.monotonic()-started)
        try:
            meta['input_sha256_after'] = bindings()
            if meta.get('input_sha256') != meta['input_sha256_after']:
                meta['finalization_error'] = 'inputs changed during failure'
        except BaseException as err:
            meta['finalization_error'] = repr(err); meta['input_sha256_after'] = input_hashes('input_read_errors')
        try:
            meta['output_sha256'] = hashes()
        except BaseException as err:
            meta['output_hash_error'] = repr(err)
        save(OUTPUT/'metadata.json', meta)
        raise


if __name__ == '__main__':
    main()
