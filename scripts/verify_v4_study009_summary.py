"""Cross-check study009 aggregates against independently audited metric records.

Run as python -m scripts.verify_v4_study009_summary after summarization.
"""
import json
from hashlib import sha256
from fractions import Fraction
from pathlib import Path
from scripts.summarize_v4_study009 import summarize
root = Path('data/v4-study-009')
saved = json.loads((root/'summary.json').read_text())
by_source = {(r['seed'], r['drive'], r['mutation']): r for r in saved['sources']}
assert len(by_source) == len(saved['sources']) == 20
assert json.loads((root/'metadata.json').read_text())['status'] == 'complete'
verified = 0
for entry in json.loads((root/'results.json').read_text()):
    observed = json.loads((root/entry['observation']).read_text())
    summary = summarize(observed)
    assert summary == by_source[(entry['seed'], entry['drive'], entry['mutation'])]['summary']
    for window in summary['windows']:
        rows = observed['observations'][window['start']-1:window['end']]
        for key in window['boundaries']:
            phase, boundary = key.split('/')
            metrics = [r[phase]['metrics'][boundary] for r in rows]
            for field in ('component_count', 'largest_fraction', 'singleton_fraction'):
                values = []
                for m in metrics:
                    if field == 'component_count': values.append(Fraction(m['component_count']))
                    elif m['occupied_units']:
                        numerator = max(m['sizes']) if field == 'largest_fraction' else m['singleton_units']
                        values.append(Fraction(numerator, m['occupied_units']))
                actual = window['boundaries'][key][field]
                assert actual['mean'] == (str(sum(values)/len(values)) if values else None)
                assert actual['available'] == len(values)
        for field, pair in [('material_bond', ('material', 'bond')), ('contact_material', ('contact', 'material'))]:
            values = []
            for row in rows:
                d = next(v for v in row['interaction']['boundary_disagreement'] if (v['first'], v['second']) == pair)
                if d['denominator']: values.append(Fraction(d['numerator'], d['denominator']))
            assert window[field]['mean'] == (str(sum(values)/len(values)) if values else None)
            assert window[field]['available'] == len(values)
    verified += 1
assert verified == 20
for group in saved['groups']:
    source_rows = [r for r in saved['sources'] if (r['drive'], r['mutation']) == (group['drive'], group['mutation'])]
    assert len(source_rows) == 5
    values = [Fraction(r['summary']['primary']['mean']) for r in source_rows if r['summary']['primary']['mean'] is not None]
    assert group['primary'] == dict(mean=str(sum(values)/len(values)) if values else None,
                                   available=len(values), missing=5-len(values))
report = dict(status='complete', sources=verified, windows=2*verified,
    scope='cross-check summary against independently audited metrics and disagreement numerators; primary seed weighting',
    summary_sha256=sha256((root/'summary.json').read_bytes()).hexdigest(),
    verifier_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
with (root/'summary-verification.json').open('x', encoding='utf-8') as stream:
    json.dump(report, stream, indent=2)
    stream.write('\n')
print(json.dumps(report))
