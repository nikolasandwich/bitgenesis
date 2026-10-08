"""Study040 passive east/west barriers; reuse Study037 observer unchanged."""
from pathlib import Path
from time import monotonic
import subprocess
import json
from scripts import analyze_v4_reformation_barriers as old
from scripts.position_barrier_inputs import bindings,sources,read,save,digest,input_paths,capture
OUTPUT=Path('data/v4-study-040')

def analyze_case(encoding,branch,source):
    result=old.analyze_case(branch,source)
    result['encoding']=encoding
    result['prior039']=result.pop('prior036')
    return result

def summarize(records):
    return dict(cells=[dict(encoding=e,category=c,**old.summarize([r for r in records if r['encoding']==e and r['selection']['category']==c])['overall']) for e in ('east','west') for c in ('short_window','remaining_conditional')],overall=old.summarize(records)['overall'])

def main():
    old.require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch')
    OUTPUT.mkdir(exist_ok=False);start=monotonic();records=[]
    paths=[]
    meta=dict(status='running',planned_cases=8,completed_cases=0,saved_steps=0,slot_steps=0,diagnostic_states=0,new_simulation_steps=0,time_limit_seconds=600,storage_limit_bytes=134217728)
    def budget():old.require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'bounded audit')
    try:
        save(OUTPUT/'records.json',records)
        paths=input_paths();meta['input_sha256'],meta['input_read_errors_before']=capture(paths)
        before=bindings();old.require(before==meta['input_sha256'],'validated initial bindings');meta.update(input_sha256=before,git_commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip());save(OUTPUT/'metadata.json',meta);save(OUTPUT/'records.json',records)
        for enc,path,source in sources():
            budget();records.append(analyze_case(enc,read(path),read(source)))
            meta.update(completed_cases=len(records),saved_steps=sum(len(r['rows']) for r in records),slot_steps=3*sum(len(r['rows']) for r in records),diagnostic_states=len(records))
            save(OUTPUT/'records.json',records);save(OUTPUT/'metadata.json',meta)
        old.require(meta['completed_cases']==8 and meta['saved_steps']==116,'complete fixed cohort')
        save(OUTPUT/'summary.json',summarize(records));meta['input_sha256_after']=bindings();old.require(meta['input_sha256_after']==before,'unchanged inputs')
        meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('records.json','summary.json')});budget()
    except BaseException as exc:
        meta.update(status='failed',error=repr(exc));raise
    finally:
        meta['elapsed_seconds']=monotonic()-start
        meta['input_sha256_after'],meta['input_read_errors_after']=capture(paths)
        try:
            if meta['status']=='complete':
                old.require(meta['input_sha256_after']==meta['input_sha256'] and not meta['input_read_errors_after'],'final input binding')
                meta['elapsed_seconds']=monotonic()-start
                old.require(meta['elapsed_seconds']<600,'final time budget')
                payload=json.dumps(meta,ensure_ascii=False).encode()
                old.require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(payload)<134217728,'final output budget')
        except BaseException as exc:
            meta.update(status='failed',error=repr(exc))
            save(OUTPUT/'metadata.json',meta)
            raise
        save(OUTPUT/'metadata.json',meta)
if __name__=='__main__':main()
