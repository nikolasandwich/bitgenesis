"""Study040 independent passive route; only Study037 independent science."""
from pathlib import Path
from time import monotonic
import json
from scripts import verify_v4_reformation_barriers as old
from scripts.position_barrier_inputs import bindings,read,save,digest,input_paths,capture
OUTPUT=Path('data/v4-study-040')

def verify_case(encoding,branch,source):
    result=old.verify_case(branch,source);result['encoding']=encoding
    result['prior039']=result.pop('prior036')
    return result

def summarize(records):
    cells=[]
    for encoding in ('east','west'):
        for category in ('short_window','remaining_conditional'):
            chosen=[r for r in records if (r['encoding'],r['selection']['category'])==(encoding,category)]
            cells.append(dict(encoding=encoding,category=category,**old.summarize(chosen)['overall']))
    return dict(cells=cells,overall=old.summarize(records)['overall'])

def main():
    proof=OUTPUT/'independent-verification.json';old.require(not proof.exists(),'exclusive proof')
    start=monotonic();result=dict(status='running',completed_cases=0,new_simulation_steps=0,review_mode='parent inline fallback independent algorithm');before={};paths=[]
    def budget():old.require(monotonic()-start<600 and sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())<134217728,'verification budget')
    try:
        paths=input_paths();result['input_sha256'],result['input_read_errors_before']=capture(paths)
        bound=bindings();old.same(result['input_sha256'],bound,'validated initial bindings')
        before={n:digest(OUTPUT/n) for n in ('metadata.json','records.json','summary.json')}
        meta=read(OUTPUT/'metadata.json')
        for k,val in dict(status='complete',planned_cases=8,completed_cases=8,saved_steps=116,slot_steps=348,diagnostic_states=8,new_simulation_steps=0).items():old.same(meta[k],val,'metadata '+k)
        old.require(0<=meta['elapsed_seconds']<600,'production duration')
        old.same(meta['time_limit_seconds'],600,'time budget')
        old.same(meta['storage_limit_bytes'],134217728,'storage budget')
        old.same(meta['input_sha256'],bound,'producer sources');old.same(meta['input_sha256_after'],bound,'producer final sources')
        old.same(meta['output_sha256'],{n:before[n] for n in ('records.json','summary.json')},'producer output binding')
        # Independently enumerate frozen census, not producer source selector.
        census=read('docs/research/results/v4-study-039-design-census.json')['cases']
        chosen=[c for c in census if c['encoding'] in ('east','west') and c['trigger']]
        old.same(len(chosen),8,'eight source cases')
        old.same([sum(c['encoding']==e for c in chosen) for e in ('east','west')],[5,3],'encoding counts')
        old.same(sum(c['short_window'] for c in chosen),2,'short windows')
        policy=read('data/v4-study-039/records.json');old.same(len(policy),100,'full policy denominator');records=[]
        for c in chosen:
            budget();branch=read(f"data/v4-study-039/cases/{c['encoding']}-{c['seed']}.json")
            matched=[r for r in policy if (r['encoding'],r['seed'])==(c['encoding'],c['seed'])]
            old.same(len(matched),1,'one policy source');r=matched[0]
            old.same(branch['selection'],r['selection'],'full policy selection')
            old.same(branch['ablation']['episodes'],r['ablation_episodes'],'policy intervals')
            old.same(branch['ablation']['metrics'],r['ablation_future_metrics'],'policy future metrics')
            old.same(branch['selection']['t0'],c['t0'],'frozen trigger')
            old.same(branch['selection']['source'],c['source'],'frozen source')
            records.append(verify_case(c['encoding'],branch,read(c['source'])));result['completed_cases']+=1
        old.same(sum(len(r['rows']) for r in records),116,'116 future states')
        old.same(read(OUTPUT/'records.json'),records,'all predicates witnesses transitions episodes')
        old.same(read(OUTPUT/'summary.json'),summarize(records),'all four cells')
        after=bindings();old.same(after,bound,'unchanged sources');result['input_sha256_after']=after
        old.same({n:digest(OUTPUT/n) for n in before},before,'unchanged outputs');budget()
        result.update(status='verified',saved_steps=116,slot_steps=348,diagnostic_states=8,files_sha256=before)
    except BaseException as exc:
        result.update(status='failed',error=repr(exc));raise
    finally:
        result['elapsed_seconds']=monotonic()-start
        result['input_sha256_after'],result['input_read_errors_after']=capture(paths)
        result['files_sha256_before']=before
        try:
            if result['status']=='verified':
                old.require(result['input_sha256_after']==result['input_sha256'] and not result['input_read_errors_after'],'final input binding')
                result['elapsed_seconds']=monotonic()-start
                old.require(result['elapsed_seconds']<600,'final time budget')
                payload=json.dumps(result,ensure_ascii=False).encode()
                old.require(sum(p.stat().st_size for p in OUTPUT.rglob('*') if p.is_file())+len(payload)<134217728,'final output budget')
        except BaseException as exc:
            result.update(status='failed',error=repr(exc))
            save(proof,result)
            raise
        save(proof,result)
if __name__=='__main__':main()
