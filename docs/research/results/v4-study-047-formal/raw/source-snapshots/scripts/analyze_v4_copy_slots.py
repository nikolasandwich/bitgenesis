"""Fixed-support translated template slots on saved observations only."""
from pathlib import Path
import subprocess
import time

GENOTYPES = ('homogeneous', 'heterogeneous')
MODES = ('random-direction', 'random-feed', 'random-both')
GRID = [(g,m,e,s) for g in GENOTYPES for m in MODES for e in (False,True) for s in range(120000,120020)]
FLAGS = ('occupied','material_match','genetic_match','whole_component','descendant','all_new','copy','new_copy')
FIXED_PLACEMENTS = [[85,86],[101,102],[117,118]]
OUTPUT = Path('data/v4-study-034')


def require(value, message):
    if not value:
        raise ValueError(message)


def integer(value):
    return type(value) is int


def placements(support):
    support = set(support)
    require(all(integer(s) and 0 <= s < 256 for s in support), 'support sites')
    found = []
    for dy in range(16):
        for dx in range(16):
            pair = [((s//16+dy)%16)*16+(s%16+dx)%16 for s in (85,86)]
            if all(s in support for s in pair):
                found.append(pair)
    return sorted(found)


def episodes(counts):
    result = []; start = None
    for tick, count in enumerate(counts, 1):
        if count >= 2 and start is None:
            start = tick
        if count < 2 and start is not None:
            result.append([start,tick-1]); start = None
    if start is not None:
        result.append([start,len(counts)])
    return result


def identity(record):
    require(type(record['genotype']) is str and type(record['mode']) is str and type(record['exchange']) is bool and integer(record['seed']), 'strict case identity')
    value = tuple(record[k] for k in ('genotype','mode','exchange','seed'))
    require(value in GRID, 'fixed case identity')
    return value


def analyze_case(case, genotype):
    record = dict(genotype=genotype, mode=case['mode'], exchange=case['exchange'], seed=case['seed'])
    identity(record)
    initial = case['initial']; parents = case['final']['parents']; roots = []
    require(type(parents) is list and len(parents)>=3, 'parent list')
    for i, p in enumerate(parents):
        require((i < 3 and p is None) or (i >= 3 and integer(p) and 0 <= p < i), 'ordered ancestry')
        roots.append(i if p is None else roots[p])
    require(len(initial['raw']) == len(initial['units']) == len(initial['site_ids']) == 256, 'initial site coverage')
    require(initial['site_ids'][85:87] == [0,1], 'original template identities')
    require(all(integer(v) and v>=0 for v in initial['raw']), 'initial raw')
    support = {s for s in range(256) if initial['raw'][s]+int(initial['units'][s] is not None)>0}
    record['placements'] = placements(support)
    require(record['placements']==FIXED_PLACEMENTS, 'fixed initial template placements')
    template = [initial['units'][s] for s in (85,86)]
    require(all(type(u) is dict for u in template), 'initial template present')
    require(type(case['rows']) is list and len(case['rows'])==32, '32 saved rows')
    rows = []
    for tick, row in enumerate(case['rows'],1):
        require(integer(row['tick']) and row['tick']==tick, 'ordered saved ticks')
        ids = row['site_ids']; units = row['physical']['units']; groups = row['observation']['components']['material']
        require(type(ids) is list and type(units) is list and len(ids)==len(units)==256, 'saved full site coverage')
        live = []
        for i,u in zip(ids,units):
            require((i is None)==(u is None), 'saved occupancy identity')
            if i is not None:
                require(integer(i) and 0<=i<len(parents), 'live identity')
                require(type(u) is dict and integer(u['material']) and 0<=u['material']<4 and type(u['program']) is list and len(u['program'])==4 and all(integer(v) and 0<=v<4 for v in u['program']), 'saved material and program')
                live.append(i)
        require(len(live)==len(set(live)), 'unique live identities')
        require(type(groups) is list and all(type(g) is list and g and all(integer(i) for i in g) for g in groups), 'saved component schema')
        flat = [i for g in groups for i in g]
        require(len(flat)==len(set(flat)) and set(flat)==set(live), 'complete disjoint material components')
        whole = {tuple(sorted(g)) for g in groups}
        slots = []
        for sites in record['placements']:
            members = [ids[s] for s in sites]; lineage = [None if i is None else roots[i] for i in members]
            occupied = all(i is not None for i in members)
            material = occupied and all(units[s]['material']==t['material'] for s,t in zip(sites,template))
            genetic = material and all(units[s]['program']==t['program'] for s,t in zip(sites,template))
            component = occupied and tuple(sorted(members)) in whole
            descendant = occupied and all(r in (0,1) for r in lineage)
            new = occupied and all(i not in (0,1) for i in members)
            copy = genetic and component and descendant
            slots.append(dict(sites=list(sites), identities=members, roots=lineage, occupied=occupied, material_match=material,
                              genetic_match=genetic, whole_component=component, descendant=descendant, all_new=new, copy=copy, new_copy=copy and new))
        rows.append(dict(tick=tick, slots=slots, copy_count=sum(s['copy'] for s in slots), new_copy_count=sum(s['new_copy'] for s in slots)))
    record['rows'] = rows
    record['episodes'] = episodes([r['copy_count'] for r in rows])
    record['longest'] = max((b-a+1 for a,b in record['episodes']),default=0)
    validate_record(record)
    return record


def validate_record(r):
    require(type(r) is dict and set(r)=={'genotype','mode','exchange','seed','placements','rows','episodes','longest'}, 'record schema')
    identity(r)
    require(type(r['placements']) is list and len(r['placements'])==3 and all(type(p) is list and len(p)==2 and all(integer(s) for s in p) for p in r['placements']) and r['placements']==FIXED_PLACEMENTS, 'fixed ordered placements')
    require(type(r['rows']) is list and len(r['rows'])==32, '32 observation rows')
    for tick,row in enumerate(r['rows'],1):
        require(type(row) is dict and set(row)=={'tick','slots','copy_count','new_copy_count'} and integer(row['tick']) and row['tick']==tick, 'row schema and tick')
        require(type(row['slots']) is list and len(row['slots'])==3, 'three slots')
        seen = set()
        for pair,s in zip(r['placements'],row['slots']):
            require(type(s) is dict and set(s)==set(FLAGS)|{'sites','identities','roots'}, 'slot schema')
            require(type(s['sites']) is list and all(integer(x) for x in s['sites']) and s['sites']==pair, 'slot site order')
            for key in ('identities','roots'):
                require(type(s[key]) is list and len(s[key])==2 and all(v is None or integer(v) and v>=0 for v in s[key]), 'identity and root types')
            for i,root in zip(s['identities'],s['roots']):
                require((i is None)==(root is None) and (root is None or root in (0,1,2)), 'root coverage')
                if i is not None:
                    require(i not in seen and (i>=3 or root==i), 'distinct identities and original roots'); seen.add(i)
            require(all(type(s[k]) is bool for k in FLAGS), 'strict booleans')
            occupied = all(i is not None for i in s['identities'])
            require(s['occupied']==occupied, 'occupied definition')
            if not occupied:
                require(not any(s[k] for k in FLAGS), 'missing member clears all flags')
            require(not s['material_match'] or occupied, 'material occupancy')
            require(not s['genetic_match'] or s['material_match'], 'genetic material subset')
            require(not s['whole_component'] or occupied, 'whole component occupancy')
            require(s['descendant']==(occupied and all(v in (0,1) for v in s['roots'])), 'descendant definition')
            require(s['all_new']==(occupied and all(v not in (0,1) for v in s['identities'])), 'all new definition')
            require(s['copy']==(s['genetic_match'] and s['whole_component'] and s['descendant']), 'copy definition')
            require(s['new_copy']==(s['copy'] and s['all_new']), 'new copy definition')
        for key,flag in (('copy_count','copy'),('new_copy_count','new_copy')):
            require(integer(row[key]) and row[key]==sum(s[flag] for s in row['slots']), 'recomputed slot count')
    spans = episodes([row['copy_count'] for row in r['rows']])
    require(type(r['episodes']) is list and all(type(p) is list and len(p)==2 and all(integer(t) for t in p) for p in r['episodes']) and r['episodes']==spans, 'inclusive episodes')
    require(integer(r['longest']) and r['longest']==max((b-a+1 for a,b in spans),default=0), 'longest episode')


def summarize(records):
    require(type(records) is list, 'record list')
    for r in records:
        validate_record(r)
    require([identity(r) for r in records]==GRID, 'complete ordered240 grid')
    cells = []
    for offset in range(0,240,20):
        group = records[offset:offset+20]; first = group[0]
        rows = [row for r in group for row in r['rows']]
        slots = [s for row in rows for s in row['slots']]
        cell = {k:first[k] for k in ('genotype','mode','exchange')}
        cell.update(n=20,saved_steps=640,slot_steps=1920,totals={k:sum(s[k] for s in slots) for k in FLAGS},
                    slots=[dict(sites=list(pair), **{k:sum(row['slots'][i][k] for row in rows) for k in FLAGS}) for i,pair in enumerate(FIXED_PLACEMENTS)],
                    double_steps=sum(row['copy_count']>=2 for row in rows),new_double_steps=sum(row['new_copy_count']>=2 for row in rows),triple_steps=sum(row['copy_count']==3 for row in rows),
                    cases_ever_double=sum(r['longest']>0 for r in group),cases_persistent10=sum(r['longest']>=10 for r in group),max_double_run=max(r['longest'] for r in group))
        cells.append(cell)
    return cells

def main():
    from scripts.copy_slots_inputs import bindings, source_cases, input_paths, read, save, digest
    require(not subprocess.check_output(['git', 'status', '--porcelain'], text=True).strip(), 'clean launch')
    OUTPUT.mkdir(exist_ok=False)
    started = time.monotonic(); records = []; inventory = []
    meta = dict(status='running', planned_cases=240, completed_cases=0, saved_steps=0, slot_steps=0, new_simulation_steps=0,
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
        before = bindings(); require(len(before) == 413 and before == meta['input_sha256'], 'validated initial inputs')
        sources = list(source_cases())
        require(len(sources) == 240, 'complete source cases')
        for genotype, path in sources:
            budget()
            records.append(analyze_case(read(path), genotype))
            meta.update(completed_cases=len(records), saved_steps=32*len(records), slot_steps=96*len(records), elapsed_seconds=time.monotonic()-started)
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
