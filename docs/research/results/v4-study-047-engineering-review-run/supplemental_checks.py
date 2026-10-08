from pathlib import Path
import json, hashlib, subprocess
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results={'historical_red':[]}
for suffix in ['producer-preflight-implementation/red-off','verifier-implementation/remediation-1-red']:
    root=ROOT/('docs/research/results/v4-study-047-'+suffix); ex=json.loads((root/'execution.json').read_bytes()); assert ex['exit_code']==1
    mapping=ex.get('raw_output_sha256',ex.get('evidence_sha256')); assert mapping
    for name in ['stdout.bin','stderr.bin']: assert sha(root/name)==mapping[name]
    log=(root/'stderr.bin').read_text(); assert 'FAILED' in log
    results['historical_red'].append(dict(path=str((root/'execution.json').relative_to(ROOT)),exit_code=1,raw_output_hashes_verified=2,raw_final_lines=log.splitlines()[-8:],reexecuted=False))
no_index=[]
for p in sorted((ROOT/'docs/research/results/v4-study-047-engineering').rglob('*')):
    if not p.is_file() or p.suffix not in ['.py','.md','.json','.txt','.toml','.yaml','.yml']: continue
    r=subprocess.run(['git','diff','--no-index','--check','/dev/null',str(p.relative_to(ROOT))],cwd=ROOT,capture_output=True,text=True)
    if r.stdout or r.stderr: no_index.append(dict(path=str(p.relative_to(ROOT)),exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr))
results['all_new_text_diff_check']=no_index
assert len(no_index)==1 and no_index[0]['path'].endswith('raw/source-snapshots/src/bitgenesis/v4/competition.py')
snapshot=ROOT/no_index[0]['path'];source=ROOT/'src/bitgenesis/v4/competition.py';assert snapshot.read_bytes()==source.read_bytes()
results['historical_eof_blank_line']=dict(classification='原源码既有尾部空行，快照逐字节保存；不是新增行为或作者格式错误。',source=str(source.relative_to(ROOT)),snapshot=str(snapshot.relative_to(ROOT)),sha256=sha(source),byte_identical=True)
for version in ['audit-execution','audit-execution-v2']:
    exdir=OUT/version;ex=json.loads((exdir/'execution.json').read_bytes());req=json.loads((exdir/'request.json').read_bytes());script=ROOT/req['command'][1]
    assert sha(script)==req['source_sha256']==ex['source_sha256_before']==ex['source_sha256_after']
    for n,h in ex['raw_output_sha256'].items():assert sha(exdir/n)==h
results['reviewer_audit_correction']=dict(original_exit_code=1,corrected_exit_code=0,cause='独立审查脚本首次假定帮助记录使用raw_output_sha256，实际历史生产help使用evidence_sha256。v2仅适配字段；两版源码和原始输出保留。',new_scientific_calls=0,science_failure=False)
results['exploratory_red_mapping_note']='一次补充交互读取误将旧RED evidence_sha256中的临时fixture归档成员当当前路径，发生FileNotFoundError；随即改为核实本任务所需的原始stdout/stderr。旧fixture归档由已核对当前字节的1985/3023审批闭包承载；不将临时路径当现存文件或声称本轮恢复旧fixture。'
results['status']='PASS'
with (OUT/'supplemental-checks.json').open('x') as f:json.dump(results,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(results,ensure_ascii=False,indent=2))
