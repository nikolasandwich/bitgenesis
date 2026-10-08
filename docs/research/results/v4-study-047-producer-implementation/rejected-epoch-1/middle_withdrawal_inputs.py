"""Study047 immutable input contract shared by the two independent routes.

This module reads and validates saved evidence only: no physical evolution,
copy classification, or future random draws. Scientific reconstruction belongs
separately to each route. JSON comparisons require identical concrete types.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import random
import _random
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = 'docs/research/results/v4-study-047-'
SOURCES = BASE + 'design-revalidated-sources.json'
CENSUS = BASE + 'design-revalidated-census.json'
REVIEW = BASE + 'design-review.json'
ARMS = ('continue_north', 'withdraw_to_natural')
ENCODINGS = ('east', 'west', 'south', 'north', 'homogeneous')
SEEDS = tuple(range(120000, 120020))
CONFIG = dict(width=16, height=16, capacity=64, leak=1, bond_cost=1,
              threshold=16, construction_cost=4, copy_cost=1, mutation_per_thousand=0)
NEW_CODE = ('scripts/middle_withdrawal_inputs.py', 'scripts/run_v4_middle_withdrawal.py')
VERIFIER = 'scripts/verify_v4_middle_withdrawal.py'
SECONDS = 600
STORAGE = 128 * 1024**2
SCHEMA = 'study047-withdrawal-v1'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def same(actual, expected, label='strict object equality'):
    require(type(actual) is type(expected), label + ': concrete type')
    if type(actual) is dict:
        require(actual.keys() == expected.keys(), label + ': keys')
        for key in actual:
            require(type(key) is str, label + ': JSON key')
            same(actual[key], expected[key], label + '/' + key)
    elif type(actual) in (list, tuple):
        require(len(actual) == len(expected), label + ': length')
        for i, (a, b) in enumerate(zip(actual, expected)):
            same(a, b, label + '/' + str(i))
    else:
        require(type(actual) in (str, int, float, bool, type(None)) and actual == expected,
                label + ': value')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)


def object_hash(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def capture(paths):
    values, errors, first = {}, {}, None
    for path in sorted(paths):
        try:
            values[str(path)] = digest(path)
        except BaseException as error:
            errors[str(path)] = repr(error)
            if first is None:
                first = error
    return values, errors, first


def runtime_paths():
    return [str(Path(p).resolve()) for p in (random.__file__, _random.__file__, sys.executable)]


def runtime():
    files = runtime_paths()
    return dict(python_version=platform.python_version(), implementation=platform.python_implementation(),
                executable=sys.executable, random_module=random.__file__, random_extension=_random.__file__,
                random_state_version=random.Random.VERSION, files_sha256={p: digest(p) for p in files})


def new_stream(seed, kind):
    require(type(seed) is int and kind in ('directions', 'feeds'), 'exact environment seed/kind')
    return random.Random(int.from_bytes(hashlib.sha256(
        f'v4-copy-ablation-1:{seed}:{kind}'.encode('ascii')).digest(), 'big'))


def tuples(value):
    return tuple(tuples(v) for v in value) if type(value) is list else value


def fixed_proposals():
    return [8 if site in (85, 86, 117, 118) else 0 for site in range(256)]


def fixed_tickets():
    return [[999, 0, 1] for _ in range(256)]


def source_path(path):
    require(type(path) is str and not Path(path).is_absolute(), 'repository relative source path')
    resolved = (ROOT / path).resolve()
    require(resolved.is_relative_to(ROOT.resolve()), 'source path stays inside repository')
    return resolved


def resolve_ref(ref):
    same(sorted(ref), ['path', 'pointer', 'sha256', 'value_sha256'], 'reference fields')
    path = source_path(ref['path'])
    same(digest(path), ref['sha256'], 'reference bytes')
    value = read(path)
    require(ref['pointer'].startswith('/'), 'absolute JSON pointer')
    for part in ref['pointer'][1:].split('/'):
        key = part.replace('~1', '/').replace('~0', '~')
        value = value[int(key)] if type(value) is list else value[key]
    same(object_hash(value), ref['value_sha256'], 'reference object')
    return deepcopy(value)


def integer(value, low, high, label):
    require(type(value) is int and low <= value <= high, label)


def validate_state(state):
    same(sorted(state), sorted(('tick', 'units', 'raw', 'site_ids', 'parents', 'individuals')), 'boundary fields')
    same(state['tick'], 32, 'boundary tick')
    for key in ('units', 'raw', 'site_ids', 'parents', 'individuals'):
        require(type(state[key]) is list, 'boundary list: ' + key)
    same([len(state[k]) for k in ('units', 'raw', 'site_ids')], [256] * 3, 'boundary geometry')
    people = state['individuals']; require(len(people) >= 3, 'complete original founders')
    same(state['parents'], [p['parent'] for p in people], 'all historical parents')
    births_by_parent = [0] * len(people)
    fields = sorted(('id', 'site', 'birth_tick', 'death_tick', 'parent', 'founder', 'generation',
                     'material', 'program', 'birth_energy', 'mutated', 'offspring'))
    for i, person in enumerate(people):
        same(sorted(person), fields, 'individual fields')
        same(person['id'], i, 'identity order')
        integer(person['site'], 0, 255, 'birth site')
        integer(person['birth_tick'], 0, 32, 'historical birth')
        integer(person['material'], 0, 3, 'material')
        integer(person['birth_energy'], 0, 64, 'birth energy')
        require(type(person['program']) is list and len(person['program']) == 4, 'full program')
        for v in person['program']: integer(v, 0, 3, 'program entry')
        require(type(person['mutated']) is bool, 'mutation flag')
        integer(person['offspring'], 0, len(people), 'offspring count')
        if person['death_tick'] is not None:
            integer(person['death_tick'], person['birth_tick'] + 1, 32, 'natural death tick')
        if i < 3:
            same([person['parent'], person['founder'], person['generation'], person['birth_tick']],
                 [None, i, 0, 0], 'original founder')
        else:
            parent = person['parent']; integer(parent, 0, i - 1, 'ordered parent')
            ancestor = people[parent]; births_by_parent[parent] += 1
            same([person['founder'], person['generation']], [ancestor['founder'], ancestor['generation'] + 1], 'historical ancestry')
            require(ancestor['birth_tick'] < person['birth_tick'], 'no newborn cascade')
    same([p['offspring'] for p in people], births_by_parent, 'full offspring counts')
    alive = []
    for site, (unit, identity, raw) in enumerate(zip(state['units'], state['site_ids'], state['raw'])):
        integer(raw, 0, 7, 'raw integer')
        require((unit is None) == (identity is None), 'unit/identity occupancy')
        if unit is None:
            continue
        integer(identity, 0, len(people) - 1, 'living identity')
        require(identity not in alive and identity not in (0, 1), 'unique living ID excludes original removals')
        alive.append(identity)
        same(sorted(unit), ['energy', 'material', 'program'], 'unit fields')
        integer(unit['energy'], 0, 64, 'energy integer')
        p = people[identity]
        same([p['site'], p['death_tick'], p['material'], p['program']],
             [site, None, unit['material'], unit['program']], 'living history')
    same(sorted(alive), [p['id'] for p in people if p['death_tick'] is None and p['id'] not in (0, 1)], 'alive from sites with removal exception')
    same(sum(state['raw']) + len(alive), 7, 'boundary mass seven')
    same([people[i]['death_tick'] for i in (0, 1)], [None, None], 'original removals are not natural death')


def load_boundary(item):
    require(item['trigger'] is True, 'selected branch only')
    ref = item['boundary']
    same(ref['final']['path'], f"data/v4-study-043/cases/{item['encoding']}-{item['seed']}.json", '043 ablation source')
    same(ref['final']['pointer'], '/ablation/final', '043 ablation final only')
    same(ref['template']['path'], item['source'], 'encoding template source')
    same(ref['template']['pointer'], '/initial', 'original template pointer')
    final, template, removals = (resolve_ref(ref[k]) for k in ('final', 'template', 'historical_removals'))
    validate_state(final)
    branch = read(source_path(ref['final']['path']))
    same(branch['selection'], item['selection'], 'original selection')
    old = branch['ablation']
    same(old['initial']['removals'], removals, 'retained removal side ledger')
    same(old['initial']['energy_export'], ref['original_export'], 'retained export side ledger')
    same([ref['physical_tick'], ref['observer_tick'], ref['founders'], ref['next_identity']],
         [32, 32, 3, len(final['individuals'])], 'restoration dimensions')
    same(object_hash(dict(tick=32, alive=final['site_ids'], individuals=final['individuals'], founders=3)),
         ref['restored_observer_sha256'], 'full restoration object hash')
    same([r['tick'] for r in old['rows']], list(range(item['t0'] + 1, 33)), 'complete saved prefix suffix')
    last = old['rows'][-1]['physical'] if old['rows'] else old['initial']
    same([final['units'], final['raw']], [last['units'], last['raw']], 'last saved physical state')
    return dict(item=deepcopy(item), initial=final, template=template,
                prefix_initial=deepcopy(old['initial']), prefix_rows=deepcopy(old['rows']))


def input_paths(include_verifier=True):
    """Inventory is available before validation, so failures retain read hashes."""
    paths = {SOURCES, CENSUS, REVIEW, *NEW_CODE}
    if include_verifier:
        paths.add(VERIFIER)
    for path in (SOURCES, REVIEW):
        paths.update(read(source_path(path))['files_sha256'])
    paths.update(runtime_paths())
    return sorted(paths)


def bindings(include_verifier=True):
    """Validate the accepted latest method epoch and its full historical closure."""
    source, census, review = (read(source_path(p)) for p in (SOURCES, CENSUS, REVIEW))
    same([source['status'], census['status'], review['verdict'], review['task']],
         ['complete', 'complete', 'APPROVED', '1.1'], 'approved method epoch')
    same(review['independent_author_review'], True, 'independent method approval')
    same([source['physical_steps'], source['future_environment_draws'], census['future_environment_draws']], [0, 0, 0], 'method was past only')
    same(digest(source_path(CENSUS)), source['census_sha256'], 'approved census bytes')
    for manifest in (source, review):
        same(manifest['files_sha256'], manifest['files_sha256_after'], 'method immutable inputs')
        for path, expected in manifest['files_sha256'].items():
            actual_path = Path(path) if Path(path).is_absolute() else source_path(path)
            same(digest(actual_path), expected, 'method binding: ' + path)
    same(runtime(), source['runtime'], 'frozen Python random runtime')
    same([(c['encoding'], c['seed']) for c in census['cases']], [(e, s) for e in ENCODINGS for s in SEEDS], 'ordered 100 index')
    same([sum(c['trigger'] for c in census['cases'] if c['encoding'] == e) for e in ENCODINGS], [5, 3, 0, 9, 11], 'all 28 fixed selections')
    same(sum(c['short_window'] for c in census['cases']), 10, 'ten historical short windows')
    same([e['seed'] for e in census['environments']], list(SEEDS), 'twenty saved environments')
    values, errors, failure = capture(input_paths(include_verifier))
    if failure is not None: raise failure
    require(not errors, 'all inputs readable')
    return values


def approved_gate(path, task, required_files):
    gate = read(source_path(path))
    same([gate['verdict'], gate['task']], ['APPROVED', task], 'independent task approval')
    require(gate.get('independent_author_review') is True, 'independent author review')
    expected = gate['files_sha256']
    same(expected, gate['files_sha256_after'], 'review immutable code bindings')
    require(set(required_files) <= set(expected), 'approval binds current required code')
    for filename, h in expected.items():
        p = Path(filename) if Path(filename).is_absolute() else source_path(filename)
        same(digest(p), h, 'current approved file: ' + filename)
    return gate


def execution_gates(mode):
    require(mode in ('engineering', 'formal'), 'fixed execution stage')
    require(not subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip(), 'clean eligible code required')
    approved_gate(BASE + 'producer-review.json', '2.1', NEW_CODE)
    approved_gate(BASE + 'verifier-review.json', '2.2', (*NEW_CODE, VERIFIER))
    paths = [BASE + 'producer-review.json', BASE + 'verifier-review.json']
    if mode == 'formal':
        gate_path = BASE + 'engineering-review.json'
        gate = approved_gate(gate_path, '2.3', (*NEW_CODE, VERIFIER))
        engineering = gate['engineering_evidence']
        for key, status, count in (('producer', 'complete', 64), ('verifier', 'verified', 64)):
            meta_path = engineering[key]
            require(meta_path in gate['files_sha256'], 'engineering evidence bound by approval')
            meta = read(source_path(meta_path))
            same([meta['status'], meta['mode'], meta['physical_steps']], [status, 'engineering', count], 'unique first engineering evidence')
        paths.append(gate_path)
    return paths
