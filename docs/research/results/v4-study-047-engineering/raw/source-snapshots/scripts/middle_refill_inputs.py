"""Study046 immutable input binding and JSON references; no scientific projection.

The accepted method manifest authenticates the completed 041/045 evidence chains.
The current producer/verifier epoch is added without rewriting historical epochs.
Only engineering callers may omit the not-yet-implemented verifier from inventory.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

BASE = 'docs/research/results/v4-study-046-design-sources.json'
CENSUS = 'docs/research/results/v4-study-046-design-census.json'
REVIEW = 'docs/research/results/v4-study-046-design-review.json'
NEW = ('scripts/middle_refill_inputs.py', 'scripts/analyze_v4_middle_refill.py',
       'scripts/verify_v4_middle_refill.py')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()


def normalized_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    ensure_ascii=False).encode()).hexdigest()


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture(paths):
    hashes, errors = {}, {}
    for path in sorted(paths):
        try:
            hashes[path] = digest(path)
        except Exception as error:
            errors[path] = repr(error)
    return hashes, errors


def pointer_value(document, pointer):
    require(isinstance(pointer, str) and (pointer == '' or pointer.startswith('/')), 'JSON pointer syntax')
    value = document
    try:
        for token in pointer.split('/')[1:] if pointer else []:
            token = token.replace('~1', '/').replace('~0', '~')
            if isinstance(value, list):
                require(token.isdigit() and str(int(token)) == token, 'JSON pointer array index')
                value = value[int(token)]
            else:
                value = value[token]
    except (KeyError, IndexError, TypeError, ValueError) as error:
        raise ValueError('unresolved JSON pointer ' + pointer) from error
    return value


class SourceReader:
    """Read each immutable file once per projection; the runner checks both epochs."""
    def __init__(self):
        self.documents = {}
        self.hashes = {}

    def resolve(self, reference):
        require(isinstance(reference, dict) and set(reference) == {
            'path', 'file_sha256', 'json_pointer', 'normalized_sha256'}, 'source reference schema')
        path = reference['path']
        if path not in self.documents:
            try:
                content = Path(path).read_bytes()
                self.documents[path] = json.loads(content)
                self.hashes[path] = hashlib.sha256(content).hexdigest()
            except Exception as error:
                raise ValueError('unreadable reference ' + path) from error
        require(self.hashes[path] == reference['file_sha256'], 'reference file hash ' + path)
        value = pointer_value(self.documents[path], reference['json_pointer'])
        require(normalized_hash(value) == reference['normalized_sha256'], 'reference normalized hash')
        return deepcopy(value)

    def child_ref(self, reference, suffix):
        self.resolve(reference)
        pointer = reference['json_pointer'] + suffix
        value = pointer_value(self.documents[reference['path']], pointer)
        return dict(path=reference['path'], file_sha256=reference['file_sha256'],
                    json_pointer=pointer, normalized_sha256=normalized_hash(value))


def make_ref(path, pointer):
    content = Path(path).read_bytes()
    return dict(path=str(path), file_sha256=hashlib.sha256(content).hexdigest(), json_pointer=pointer,
                normalized_sha256=normalized_hash(pointer_value(json.loads(content), pointer)))


def input_paths(errors=None, *, include_verifier=True):
    errors = {} if errors is None else errors
    paths = set(NEW if include_verifier else NEW[:2]) | {BASE, CENSUS, REVIEW}
    for path, key in ((BASE, 'files_sha256'), (REVIEW, 'files_sha256')):
        try:
            paths.update(read(path)[key])
        except Exception as error:
            errors[path] = repr(error)
    return sorted(paths)


def bindings(*, include_verifier=True):
    errors = {}
    paths = input_paths(errors, include_verifier=include_verifier)
    captured, failures = capture(paths)
    require(not errors and not failures, 'complete immutable input inventory')
    method, review, census = read(BASE), read(REVIEW), read(CENSUS)
    expected = method['files_sha256']
    require(len(expected) == 947 and expected == method['files_sha256_after'], 'frozen method source epochs')
    require(all(captured.get(p) == sha for p, sha in expected.items()), 'frozen method source hashes')
    require(method['status'] == 'complete' and method['task'] == '1' and method['physical_steps'] == 0
            and method['scientific_slot_classification'] is False, 'completed method boundary')
    require(not method['input_inventory_errors'] and not method['input_read_errors_before']
            and not method['input_read_errors_after'], 'method input reads')
    require(review['verdict'] == 'APPROVED' and review['task'] == '1', 'approved method review')
    require(all(captured.get(p) == sha for p, sha in review['files_sha256'].items()), 'method review hashes')
    require(captured[CENSUS] == method['census_sha256'], 'method census binding')
    require(census['phase'] == 'method' and census['scientific_slot_classification'] is False,
            'unclassified structural census')
    counts = census['counts']
    required = dict(index=100, not_applicable=72, pairs=28, arms=56, saved_states=780,
                    diagnostic_states=56, short_window_pairs=10, target_ticks=1560, source_slots=6240,
                    reuse_arms=8, reuse_rows=116, existing_041_events=596, existing_041_deaths=22,
                    projection_arms=48, projection_rows=664, gap_references=226,
                    gap_target_ticks=601, gap_source_slots=2404)
    require(all(counts.get(k) == value for k, value in required.items()), 'complete method census')
    reader = SourceReader()

    def refs(value):
        if isinstance(value, dict):
            if {'path', 'file_sha256', 'json_pointer', 'normalized_sha256'} <= value.keys():
                require(captured.get(value['path']) == value['file_sha256'], 'reference inventory membership')
                reader.resolve(value)
            else:
                for child in value.values():
                    refs(child)
        elif isinstance(value, list):
            for child in value:
                refs(child)
    refs(census)
    return captured
