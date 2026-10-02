"""Original-member retention from the saved original-death ledger, exact weights."""
import json
import subprocess
from fractions import Fraction
from itertools import product
from pathlib import Path
from scripts.retention_weighting_inputs import bindings, read, digest, require, ROOT, TRADEOFF, POPULATION

OUTPUT=Path('data/v4-study-012-retention-weighting')
CLASSES=('world','singleton','local_multi','all')


def ledger_pair(pair):
    records=[];members=[]
    total=sum(r['on']['anchor_size'] for r in pair['records'])
    require(len(pair['records'])==pair['initial_components'],'all initial components')
    for c,r in enumerate(pair['records']):
        a,b=r['on'],r['off'];n=a['anchor_size']
        require(r['component']==a['component']==b['component']==c,'ordered components')
        require(all(a[k]==b[k] for k in ('anchor_members','anchor_size','whole_world_anchor')),'common anchor component')
        require(type(n) is int and n>0 and len(set(a['anchor_members']))==len(a['anchor_members'])==n,'initial size')
        require(a['whole_world_anchor']==(n==total),'whole world flag')
        members.extend(a['anchor_members']);counts={}
        for arm,v in (('on',a),('off',b)):
            d=v['original_deaths'];require(type(d) is int and 0<=d<=n,'original death count')
            counts[arm]=n-d
            require(counts[arm]==v['endpoint']['original_survivors'],'endpoint original identity balance')
        category='world' if n==total else 'singleton' if n==1 else 'local_multi'
        records.append(dict(component=c,category=category,size=n,**counts))
    require(len(set(members))==total,'initial partition disjoint')
    return dict(seed=pair['seed'],mutation=pair['mutation'],anchor=pair['anchor'],records=records)


def cell(records,total):
    c=len(records);n=sum(r['size'] for r in records);on=sum(r['on'] for r in records);off=sum(r['off'] for r in records)
    result=dict(components=c,initial=n,on=on,off=off,count_difference=on-off)
    for arm in ('on','off'):
        result[f'component_{arm}']=str(sum((Fraction(r[arm],r['size']) for r in records),Fraction())/c) if c else None
        result[f'individual_{arm}']=str(Fraction(result[arm],n)) if n else None
    for kind in ('component','individual'):
        result[f'{kind}_difference']=str(Fraction(result[f'{kind}_on'])-Fraction(result[f'{kind}_off'])) if c else None
    mean=Fraction(n,c) if c else None
    gap=Fraction(result['individual_difference'])-Fraction(result['component_difference']) if c else None
    covariance=sum(((r['size']-mean)*(Fraction(r['on']-r['off'],r['size'])-Fraction(result['component_difference'])) for r in records),Fraction())/c if c else None
    term=covariance/mean if c else None
    require(gap==term,'covariance identity')
    result.update(mean_size=str(mean) if c else None,covariance=str(covariance) if c else None,weighting_gap=str(gap) if c else None,covariance_term=str(term) if c else None,world_contribution=str(Fraction(on-off,total)) if total else '0')
    return result


def average(values):
    valid=[Fraction(v) for v in values if v is not None]
    return dict(mean=str(sum(valid)/len(valid)) if valid else None,available=len(valid),missing=len(values)-len(valid))


def aggregate(pairs):
    keys=[(p['seed'],p['mutation'],p['anchor']) for p in pairs]
    require(len(keys)==40 and set(keys)==set(product(range(96000,96005),(0,100),(100,200,300,400))),'complete unique pair grid')
    sizes=sorted({r['size'] for p in pairs for r in p['records']});anchors=[]
    for p in sorted(pairs,key=lambda p:(p['seed'],p['mutation'],p['anchor'])):
        rows=p['records'];total=sum(r['size'] for r in rows)
        require(total>0,'nonempty initial population')
        require([r['component'] for r in rows]==list(range(len(rows))),'component inventory')
        for r in rows:
            require(type(r['size']) is int and r['size']>0 and all(type(r[s]) is int and 0<=r[s]<=r['size'] for s in ('on','off')),'valid original counts')
            require(r['category']==('world' if r['size']==total else 'singleton' if r['size']==1 else 'local_multi'),'category priority')
        cells={k:cell([r for r in rows if k=='all' or r['category']==k],total) for k in CLASSES}
        require(sum(cells[k]['count_difference'] for k in CLASSES[:-1])==cells['all']['count_difference'],'count decomposition')
        require(sum(Fraction(cells[k]['world_contribution']) for k in CLASSES[:-1])==Fraction(cells['all']['individual_difference']),'weighted world decomposition')
        anchors.append(dict(seed=p['seed'],mutation=p['mutation'],anchor=p['anchor'],cells=cells,sizes={str(n):cell([r for r in rows if r['size']==n],total) for n in sizes}))
    def combined(selected,source=False):
        return {section:{k:{metric:average([row[section][k][metric]['mean'] if source else row[section][k][metric] for row in selected]) for metric in selected[0][section][k]} for k in selected[0][section]} for section in ('cells','sizes')}
    sources=[dict(seed=s,mutation=m,**combined([a for a in anchors if (a['seed'],a['mutation'])==(s,m)])) for s,m in product(range(96000,96005),(0,100))]
    groups=[dict(mutation=m,**combined([s for s in sources if s['mutation']==m],True)) for m in (0,100)]
    for level in (sources,groups):
        for row in level:
            for section in ('cells','sizes'):
                for c in row[section].values():
                    require(c['weighting_gap']==c['covariance_term'],'hierarchical covariance identity')
                    if c['weighting_gap']['mean'] is not None:require(Fraction(c['individual_difference']['mean'])-Fraction(c['component_difference']['mean'])==Fraction(c['weighting_gap']['mean']),'hierarchical weighting gap')
    return dict(anchors=anchors,sources=sources,groups=groups)


def validate_reproduction(summary,study,population):
    for a in summary['anchors']:
        key=lambda r:(r['seed'],r['mutation'],r['anchor'])
        old=next(p for p in study['pairs'] if key(p)==key(a))['metrics']['original_retention']
        for arm in ('on','off','difference'):require(a['cells']['local_multi'][f'component_{arm}']==old[arm],'study012 original retention')
        p=next(p for p in population['pairs'] if key(p)==key(a))['path']
        require(p[0]['on']['original_survivors']==p[0]['off']['original_survivors']==a['cells']['all']['initial'],'population initial count')
        for arm in ('on','off'):require(p[100][arm]['original_survivors']==a['cells']['all'][arm],'population original endpoint')
        require(p[100]['differences']['original_survivors']==a['cells']['all']['count_difference'],'population endpoint difference')

    for level,old_level in (('sources','source_means'),('groups','groups')):
        for row in summary[level]:
            keys=('seed','mutation') if level=='sources' else ('mutation',)
            match=lambda candidate:all(candidate[k]==row[k] for k in keys)
            old=next(r for r in study[old_level] if match(r))
            require(row['cells']['local_multi']['component_difference']==old['metrics']['original_retention'],'study012 hierarchical retention')
            endpoint=next(r for r in population[level] if match(r))['path'][100]
            for metric,arm in (('on','on'),('off','off'),('count_difference','differences')):
                value=endpoint[arm]['original_survivors'] if level=='sources' else endpoint['metrics']['original_survivors'][{'on':'on','off':'off','differences':'difference'}[arm]]
                require(row['cells']['all'][metric]['mean']==value,'population hierarchical endpoint')


def save(path,value):Path(path).write_text(json.dumps(value,separators=(',',':'))+'\n')


def main():
    require(not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'clean launch required')
    OUTPUT.mkdir(exist_ok=False);meta=dict(status='running',completed_pairs=0,planned_pairs=40,independent_new_samples=0);save(OUTPUT/'metadata.json',meta)
    try:
        meta['git_commit']=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip();meta['input_sha256']=bindings();save(OUTPUT/'metadata.json',meta)
        results=[]
        for p in read(TRADEOFF/'results.json'):
            results.append(ledger_pair(p));meta['completed_pairs']=len(results)
        summary=aggregate(results);validate_reproduction(summary,read(ROOT/'summary.json'),read(POPULATION/'summary.json'))
        save(OUTPUT/'results.json',results);save(OUTPUT/'summary.json',summary)
        meta['input_sha256_after']=bindings();require(meta['input_sha256_after']==meta['input_sha256'],'unchanged inputs')
        meta.update(status='complete',output_sha256={n:digest(OUTPUT/n) for n in ('results.json','summary.json')})
    except BaseException as e:
        meta.update(status='failed',error=f'{type(e).__name__}: {e}');raise
    finally:save(OUTPUT/'metadata.json',meta)


if __name__=='__main__':main()
