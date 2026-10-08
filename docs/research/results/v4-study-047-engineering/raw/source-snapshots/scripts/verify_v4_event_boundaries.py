"""Independent raw-ledger and partition proof for the retrospective event mapping."""
import hashlib
import json
from pathlib import Path
from bitgenesis.v4.structure_audit import reconstruct


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    root = Path('data/v4-study-011-event-boundaries')
    metadata = read(root/'metadata.json')
    assert metadata['status'] == 'complete'
    results = read(root/'results.json')
    upstream = read(Path('data/v4-study-011/results.json'))
    key = lambda row: (row['seed'], row['drive'], row['mutation'])
    index = {key(row): row for row in upstream}
    assert len(results) == len(index) == 20
    assert {key(row) for row in results} == set(index)
    counts = dict(sources=0, panels=0, events=0, references=0, boundary_correspondences=0)
    for result in results:
        source = index[key(result)]
        payload = Path('data/v4-study-011')/source['file']
        assert digest(payload) == source['sha256'] == result['demography_sha256']
        panels = read(payload)['panels']
        assert len(panels) == 20
        assert result['denominators'] == source['summary']
        directory = Path('data/v4-study-005')/payload.stem
        assert {p.name:digest(p) for p in directory.iterdir() if p.is_file()} == result['input_sha256']
        meta = read(directory/'metadata.json')
        units = read(directory/'initial.json')['units']
        identities = [None]*len(units)
        parents = {}
        for site, unit in enumerate(units):
            if unit is not None:
                identities[site] = len(parents)
                parents[len(parents)] = None
        states = {0:set(parents)}
        ledger = {}
        needed = {e['tick'] for e in result['events']}
        following = {t+1 for t in needed}
        partitions = {}
        with (directory/'steps.jsonl').open() as stream:
            for tick, line in enumerate(stream, 1):
                row = json.loads(line)
                assert row['tick'] == tick
                if tick in needed|following:
                    partitions[tick, 'interaction'] = reconstruct(row['interaction_units'], identities,
                        meta['width'], meta['height'], 'interaction', row['driven']['interaction']['bonds'])['components']
                for site in row['material']['dissolved']:
                    identity = identities[site]
                    assert identity is not None
                    ledger['death', identity] = tick
                    identities[site] = None
                for proposal in row['material']['proposals']:
                    if proposal['reason'] == 'formed':
                        identity = len(parents)
                        parent = identities[proposal['source']]
                        assert parent is not None and identities[proposal['target']] is None
                        parents[identity] = parent
                        identities[proposal['target']] = identity
                        ledger['birth', identity] = tick
                states[tick] = {i for i in identities if i is not None}
                if tick in needed:
                    partitions[tick, 'final'] = reconstruct(row['units'], identities,
                        meta['width'], meta['height'], 'final')['components']
        expected = {}
        for panel in panels:
            start = panel['anchor'] - int(panel['phase'] == 'interaction')
            end = start + panel['horizon']
            for record in panel['records']:
                members = set(record['anchor_members'])
                assert record['whole_world_anchor'] == (members == states[start])
                if record['whole_world_anchor']:
                    continue
                actual = {'birth':[], 'death':[]}
                for (kind, identity), tick in ledger.items():
                    if start < tick <= end:
                        ancestor = identity
                        while ancestor not in states[start] and ancestor is not None:
                            ancestor = parents[ancestor]
                        if ancestor in members:
                            actual[kind].append(identity)
                            ref = {name:panel[name] for name in ('phase','boundary','anchor','horizon')}
                            ref['component'] = record['component']
                            expected.setdefault((tick,kind,identity), []).append(ref)
                for kind in actual:
                    assert sorted(actual[kind]) == record[kind+'_ids']
        actual_keys = [(e['tick'],e['kind'],e['identity']) for e in result['events']]
        assert len(actual_keys) == len(set(actual_keys)) and set(actual_keys) == set(expected)
        for event in result['events']:
            event_key = event['tick'],event['kind'],event['identity']
            assert event['references'] == expected[event_key]
            assert event['parent'] == parents[event['identity']]
            for boundary in ('contact','material','bond'):
                tick = event['tick']
                pre = partitions[tick,'interaction'][boundary]
                post_key = (tick+1,'interaction') if boundary == 'bond' else (tick,'final')
                saved = event['boundaries'][boundary]
                if post_key not in partitions:
                    assert boundary == 'bond' and tick == meta['steps'] and saved is None
                    continue
                focus = event['parent'] if event['kind'] == 'birth' else event['identity']
                before = next(group for group in pre if focus in group)
                post = partitions[post_key][boundary]
                relevant_ids = set(before)
                if event['kind'] == 'birth':
                    relevant_ids.add(event['identity'])
                after = [group for group in post if any(i in relevant_ids for i in group)]
                after_ids = {i for group in after for i in group}
                assert saved == dict(before_members=before, after_components=after,
                    gained=sorted(after_ids-set(before)), lost=sorted(set(before)-after_ids))
                counts['boundary_correspondences'] += 1
            counts['references'] += len(event['references'])
        counts['sources'] += 1
        counts['panels'] += len(panels)
        counts['events'] += len(result['events'])
    assert digest(root/'results.json') == metadata['results_sha256']
    proof = dict(status='verified', **counts, results_sha256=digest(root/'results.json'),
        verifier_sha256=digest(Path(__file__)),
        partition_verifier_sha256=digest(Path('src/bitgenesis/v4/structure_audit.py')),
        method='Independent raw identity/event reconstruction; ancestry-derived full event references; raw geometric and bond partition reconstruction; no mapper imports')
    with (root/'independent-verification.json').open('x') as stream:
        json.dump(proof, stream, indent=2)
        stream.write('\n')
    print(json.dumps(proof))


if __name__ == '__main__':
    main()
