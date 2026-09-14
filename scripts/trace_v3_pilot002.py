"""Attribute all pilot002 B transfers after complete independent verification."""
from hashlib import sha256
import json
from pathlib import Path

from verify_v3_pilot002 import verify
from v3_provenance import trace


def main():
    root=Path('data/v3-pilot-002')
    gate=verify(root)
    if gate!=json.loads((root/'verification.json').read_text()):
        raise ValueError('verification changed')
    worlds=[]
    for checked in gate['checks']:
        directory=root/checked['directory']
        initial=json.loads((directory/'initial.json').read_text())
        final=json.loads((directory/'final.json').read_text())
        results=[]
        for convention in ('oldest_first','newest_first'):
            with (directory/'steps.jsonl').open(encoding='utf-8') as stream:
                result=trace(initial['substrate_b'],final['substrate_b'],final['lineage'],
                             (json.loads(line) for line in stream),convention)
            if result['consumed_b']!=checked['audit']['summary']['resource_flows']['consumed_b']:
                raise ValueError('consumption summary mismatch')
            results.append(result)
        worlds.append(dict(directory=directory.name,attributions=results))
    result=dict(scope='passive unit attribution, not particle identity or causal benefit; '
                'two ordering conventions are sensitivity examples, not rigorous bounds',worlds=worlds,
                verification_sha256=sha256((root/'verification.json').read_bytes()).hexdigest(),
                source_sha256={name:sha256(Path('scripts',name).read_bytes()).hexdigest()
                    for name in ('trace_v3_pilot002.py','v3_provenance.py')})
    with (root/'provenance.json').open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print('40 worlds attributed under both conventions')


if __name__=='__main__':
    main()
