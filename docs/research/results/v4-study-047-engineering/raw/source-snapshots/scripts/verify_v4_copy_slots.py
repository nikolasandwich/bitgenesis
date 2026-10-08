"""Study034 independent ordered-pair geometry and replayed material components."""
from itertools import product
import json
import math
from pathlib import Path
from time import monotonic
from scripts import verify_v4_north_opportunities as old
from bitgenesis.v4.structure_audit import reconstruct

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
GRID = tuple(product(GENOTYPES, MODES, (False, True), range(120000, 120020)))
IDENTITY = ('genotype', 'mode', 'exchange', 'seed')
FLAGS = ('occupied', 'material_match', 'genetic_match', 'whole_component', 'descendant', 'all_new', 'copy', 'new_copy')
EXPECTED = [[85,86],[101,102],[117,118]]
OUTPUT = Path('data/v4-study-034')
require, same = old.require, old.same


def natural(n):
    return type(n) is int and n >= 0


def placements(support):
    require(all(natural(s) and s < 256 for s in support), 'support sites')
    return [[a,b] for a in sorted(set(support)) for b in sorted(set(support))
            if a // 16 == b // 16 and (b-a) % 16 == 1]


def episodes(counts):
    intervals = []
    for tick, count in enumerate(counts,1):
        if count >= 2:
            if intervals and intervals[-1][1] == tick-1:
                intervals[-1][1] = tick
            else:
                intervals.append([tick,tick])
    return intervals, max((b-a+1 for a,b in intervals), default=0)


def analyze_case(case, genotype):
    old.recount(case, genotype)
    initial = case['initial']
    same(reconstruct(initial['units'],initial['site_ids'],16,16,'final'),initial['observation'],'initial observation')
    positions = placements([s for s in range(256) if initial['raw'][s] + int(initial['units'][s] is not None) > 0])
    same(positions, EXPECTED, 'fixed three placements')
    template = [initial['units'][s] for s in (85,86)]
    parents = case['final']['parents']
    def root(identity):
        if identity is None:
            return None
        require(natural(identity) and identity < len(parents), 'identity bounds')
        while parents[identity] is not None:
            parent = parents[identity]
            require(natural(parent) and parent < identity, 'acyclic ancestry')
            identity = parent
        require(identity in (0,1,2), 'founder root')
        return identity
    result = dict(genotype=genotype, **{k:case[k] for k in IDENTITY[1:]},placements=positions,rows=[])
    for row in case['rows']:
        units, ids = row['physical']['units'], row['site_ids']
        observed = reconstruct(units,ids,16,16,'final')
        same(observed,row['observation'],'final observation')
        slots = []
        for sites in positions:
            identities = [ids[s] for s in sites]
            roots = [root(i) for i in identities]
            flags = dict.fromkeys(FLAGS,False)
            if all(units[s] is not None for s in sites):
                flags['occupied'] = True
                flags['material_match'] = all(units[s]['material'] == t['material'] for s,t in zip(sites,template))
                flags['genetic_match'] = flags['material_match'] and all(units[s]['program'] == t['program'] for s,t in zip(sites,template))
                flags['whole_component'] = sorted(identities) in observed['components']['material']
                flags['descendant'] = all(r in (0,1) for r in roots)
                flags['all_new'] = all(i not in (0,1) for i in identities)
                flags['copy'] = flags['genetic_match'] and flags['whole_component'] and flags['descendant']
                flags['new_copy'] = flags['copy'] and flags['all_new']
            slots.append(dict(sites=sites.copy(),identities=identities,roots=roots,**flags))
        result['rows'].append(dict(tick=row['tick'],slots=slots,copy_count=sum(s['copy'] for s in slots),new_copy_count=sum(s['new_copy'] for s in slots)))
    result['episodes'], result['longest'] = episodes([r['copy_count'] for r in result['rows']])
    validate(result)
    return result


def validate(record):
    require(type(record) is dict and set(record) == set(IDENTITY) | {'placements','rows','episodes','longest'}, 'record schema')
    require(record['genotype'] in GENOTYPES and record['mode'] in MODES and type(record['exchange']) is bool and natural(record['seed']) and record['seed'] in range(120000,120020), 'identity types')
    same(record['placements'],EXPECTED,'ordered placements')
    require(type(record['rows']) is list and len(record['rows']) == 32,'32 rows')
    for tick,row in enumerate(record['rows'],1):
        require(type(row) is dict and set(row) == {'tick','slots','copy_count','new_copy_count'},'row schema')
        same(row['tick'],tick,'row tick')
        require(type(row['slots']) is list and len(row['slots']) == 3,'three slots')
        living = []
        for sites,slot in zip(EXPECTED,row['slots']):
            require(type(slot) is dict and set(slot) == set(FLAGS) | {'sites','identities','roots'},'slot schema')
            same(slot['sites'],sites,'slot sites')
            for name in ('identities','roots'):
                require(type(slot[name]) is list and len(slot[name]) == 2 and all(i is None or natural(i) for i in slot[name]),'identity/root arrays')
            require(all(r is None or r in (0,1,2) for r in slot['roots']),'root bounds')
            require(all((i is None) == (r is None) for i,r in zip(slot['identities'],slot['roots'])),'root presence')
            require(all(i is None or i > 2 or i == r for i,r in zip(slot['identities'],slot['roots'])),'founder self roots')
            require(all(type(slot[f]) is bool for f in FLAGS),'native booleans')
            occupied = all(i is not None for i in slot['identities'])
            same(slot['occupied'],occupied,'occupied identities')
            living += [i for i in slot['identities'] if i is not None]
            if not occupied:
                require(not any(slot[f] for f in FLAGS),'missing cell predicates')
            else:
                same(slot['descendant'],all(r in (0,1) for r in slot['roots']),'descendant roots')
                same(slot['all_new'],all(i not in (0,1) for i in slot['identities']),'new identities')
            require(not slot['genetic_match'] or slot['material_match'],'genetic material relation')
            same(slot['copy'],slot['genetic_match'] and slot['whole_component'] and slot['descendant'],'copy definition')
            same(slot['new_copy'],slot['copy'] and slot['all_new'],'new copy definition')
        require(len(living) == len(set(living)),'unique living identities')
        for count,flag in (('copy_count','copy'),('new_copy_count','new_copy')):
            same(row[count],sum(s[flag] for s in row['slots']),'slot count')
    intervals,longest = episodes([r['copy_count'] for r in record['rows']])
    same(record['episodes'],intervals,'closed double intervals')
    same(record['longest'],longest,'longest double interval')


def summarize(records):
    require(type(records) is list and len(records) == 240,'240 records')
    for record in records:
        validate(record)
    same([[r[k] for k in IDENTITY] for r in records],[list(k) for k in GRID],'ordered complete grid')
    cells = []
    for offset in range(0,240,20):
        group = records[offset:offset+20]
        rows = [row for r in group for row in r['rows']]
        cell = {k:group[0][k] for k in IDENTITY[:3]}
        cell.update(n=20,saved_steps=640,slot_steps=1920,
                    totals={f:sum(s[f] for row in rows for s in row['slots']) for f in FLAGS},
                    slots=[dict(sites=sites.copy(),**{f:sum(row['slots'][i][f] for row in rows) for f in FLAGS}) for i,sites in enumerate(EXPECTED)],
                    double_steps=sum(row['copy_count'] >= 2 for row in rows),
                    new_double_steps=sum(row['new_copy_count'] >= 2 for row in rows),
                    triple_steps=sum(row['copy_count'] == 3 for row in rows),
                    cases_ever_double=sum(r['longest'] > 0 for r in group),
                    cases_persistent10=sum(r['longest'] >= 10 for r in group),
                    max_double_run=max(r['longest'] for r in group))
        cells.append(cell)
    return cells


def write_proof(path, proof, budget):
    payload = json.dumps(proof, indent=2, allow_nan=False) + '\n'
    budget(len(payload.encode()))
    created = False
    try:
        with path.open('x') as stream:
            created = True
            stream.write(payload)
        budget()
    except BaseException:
        if created:
            path.unlink()
        raise


def main():
    from scripts.copy_slots_inputs import bindings, read, digest, input_paths, source_cases
    root = OUTPUT
    proof_path = root / 'independent-verification.json'
    require(not proof_path.exists(), 'proof already exists')
    started = monotonic()
    names = ('metadata.json', 'records.json', 'summary.json')
    before = {}; input_before = {}; errors = {}; paths = []

    def snapshot(mapping, failures):
        hashes = {}
        for name, path in mapping.items():
            try:
                hashes[name] = digest(path)
            except Exception as error:
                failures[name] = f'{type(error).__name__}: {error}'
        return hashes

    def budget(extra=0):
        require(monotonic() - started < 300, 'verification time budget')
        require(sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) + extra < 67108864, 'verification storage budget')

    try:
        before = snapshot({n: root/n for n in names}, errors)
        paths = input_paths(errors)
        input_before = snapshot({p: Path(p) for p in paths}, errors)
        bound = bindings()
        require(type(bound) is dict and len(bound) == 413, '413 bound inputs')
        same(input_before, bound, 'readable input inventory')
        require(not errors, 'input inventory and read errors')
        same(digest(Path(__file__)), bound['scripts/verify_v4_copy_slots.py'], 'running verifier binding')
        meta = read(root/'metadata.json')
        for key, value in dict(status='complete', planned_cases=240, completed_cases=240, saved_steps=7680,
                slot_steps=23040, new_simulation_steps=0, new_environment_sources=0,
                reused_environment_sources=20, new_independent_initial_worlds=0, time_limit_seconds=300,
                storage_limit_bytes=67108864).items():
            same(meta[key], value, 'metadata ' + key)
        require(type(meta['git_commit']) is str and len(meta['git_commit']) == 40 and all(c in '0123456789abcdef' for c in meta['git_commit']), 'recorded commit')
        require(type(meta['elapsed_seconds']) in (float, int) and math.isfinite(meta['elapsed_seconds']) and 0 <= meta['elapsed_seconds'] < 300, 'analysis time budget')
        same(meta['input_paths'], paths, 'metadata input paths')
        same(meta['input_sha256'], bound, 'before bindings')
        same(meta['input_sha256_after'], bound, 'after bindings')
        for key in ('input_inventory_errors', 'input_read_errors_before'):
            if key in meta:
                same(meta[key], {}, 'metadata ' + key)
        same(meta['output_sha256'], {n: before[n] for n in names[1:]}, 'output hashes')
        require({p.name for p in root.iterdir()} == set(names) and all((root/n).is_file() and not (root/n).is_symlink() for n in names), 'exclusive output inventory')
        saved = read(root/'records.json')
        require(type(saved) is list and len(saved) == 240, '240 saved records')
        sources = list(source_cases())
        require(len(sources) == 240, '240 sources')
        records = []
        for index, (genotype, path) in enumerate(sources):
            budget()
            case = read(path)
            same([genotype, case['mode'], case['exchange'], case['seed']], list(GRID[index]), 'source order')
            record = analyze_case(case, genotype)
            same(saved[index], record, 'entire independent copy slots record')
            records.append(record)
        same(read(root/'summary.json'), summarize(records), 'all twelve cells')
        same(bindings(), bound, 'inputs unchanged')
        same({n: digest(root/n) for n in names}, before, 'outputs unchanged')
        require({p.name for p in root.iterdir()} == set(names), 'exclusive output inventory after verification')
        proof = dict(status='verified', cases=240, saved_steps=7680, slot_steps=23040,
            input_files=413, new_simulation_steps=0, new_environment_sources=0, reused_environment_sources=20,
            new_independent_initial_worlds=0, input_paths=paths, input_sha256=input_before, input_sha256_after=bound,
            files_sha256=before, verifier_sha256=digest(Path(__file__)), elapsed_seconds=monotonic()-started,
            scope='independent full dictionary physics replay, initial and final material components, ordered template slots, identities and ancestry, twelve summary cells')
        write_proof(proof_path, proof, budget)
        print('verified 240 cases, 7680 saved steps, 23040 slot steps and 413 bindings')
    except BaseException as error:
        failure = root/'verification-failure.json'
        if root.is_dir() and not failure.exists():
            after_errors = {}
            evidence = dict(status='failed', error=f'{type(error).__name__}: {error}',
                input_paths=paths, input_sha256=input_before, files_sha256_before=before,
                input_sha256_after=snapshot({p: Path(p) for p in paths}, after_errors),
                files_sha256_after=snapshot({n: root/n for n in names}, after_errors),
                read_errors_before=errors, read_errors_after=after_errors,
                completed_cases=len(records) if 'records' in locals() else 0,
                elapsed_seconds=monotonic()-started)
            with failure.open('x') as stream:
                stream.write(json.dumps(evidence, indent=2, allow_nan=False) + '\n')
        raise


if __name__ == '__main__':
    main()
