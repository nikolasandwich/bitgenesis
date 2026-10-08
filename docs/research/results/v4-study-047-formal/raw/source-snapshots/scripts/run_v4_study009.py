"""Observe every frozen study005 world under the study009 boundary protocol."""
from hashlib import sha256
from itertools import product
import json
from pathlib import Path
import subprocess
from bitgenesis.v4.structure_trace import trace
from bitgenesis.v4.structure_audit import audit


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, separators=(',', ':'))+'\n', encoding='utf-8')


def sources():
    root = Path('data/v4-study-005')
    for name in ('metadata', 'results'):
        if (root/f'{name}.json').read_bytes() != Path(f'docs/research/results/v4-study-005-{name}.json').read_bytes():
            raise ValueError('archived source cohort binding')
    metadata, rows = read(root/'metadata.json'), read(root/'results.json')
    if metadata['status'] != 'complete' or len(rows) != 20:
        raise ValueError('incomplete source cohort')
    if {(r['seed'], r['drive'], r['mutation']) for r in rows} != set(product(range(96000,96005),(250,500),(0,100))):
        raise ValueError('source grid')
    for row in rows:
        directory = root/f"seed-{row['seed']}-drive-{row['drive']}-mutation-{row['mutation']}"
        m = read(directory/'metadata.json')
        if m['git_commit'] != metadata['git_commit'] or m['git_dirty'] is not False:
            raise ValueError('source revision')
        for name, digest in m['source_sha256'].items():
            if sha256((Path('src/bitgenesis/v4')/name).read_bytes()).hexdigest() != digest:
                raise ValueError('historical source bytes')
        for name, digest in m['output_sha256'].items():
            if sha256((directory/name).read_bytes()).hexdigest() != digest:
                raise ValueError('historical output bytes')
        if read(directory/'summary.json') != row['summary']:
            raise ValueError('historical summary')
    return rows


def main():
    if subprocess.check_output(['git','status','--porcelain'],text=True).strip():
        raise ValueError('clean launch required')
    rows = sources()
    root = Path('data/v4-study-009')
    root.mkdir(exist_ok=False)
    meta = dict(status='running', planned_sources=20, completed_sources=0,
        git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
        source_results_sha256=sha256(Path('data/v4-study-005/results.json').read_bytes()).hexdigest(),
        protocol_sha256=sha256(Path('experiments/v4/study-009.md').read_bytes()).hexdigest(),
        script_sha256=sha256(Path(__file__).read_bytes()).hexdigest())
    save(root/'metadata.json',meta)
    results = []
    try:
        for row in rows:
            if sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) >= 2*1024**3:
                meta['status'] = 'storage_limit'
                return
            name = f"seed-{row['seed']}-drive-{row['drive']}-mutation-{row['mutation']}"
            source = Path('data/v4-study-005')/name
            observed = trace(source)
            path = root/(name+'.json')
            save(path, observed)
            checked = audit(source, path)
            if (checked['ticks'], checked['partitions'], checked['transitions']) != (500,2502,2497):
                raise ValueError('structural observation coverage')
            save(root/(name+'-audit.json'), checked)
            results.append(dict(seed=row['seed'], drive=row['drive'], mutation=row['mutation'],
                observation=path.name, audit=name+'-audit.json',
                observation_sha256=checked['observation_sha256'],
                input_sha256=checked['input_sha256'], partitions=checked['partitions'], transitions=checked['transitions']))
            meta['completed_sources'] = len(results)
            save(root/'results.json', results)
            save(root/'metadata.json', meta)
            print(f'{len(results)}/20 observed and independently verified: {name}', flush=True)
        meta['status'] = 'complete'
    except BaseException as error:
        meta.update(status='failed',error=f'{type(error).__name__}: {error}')
        raise
    finally:
        save(root/'metadata.json',meta)


if __name__ == '__main__':
    main()
