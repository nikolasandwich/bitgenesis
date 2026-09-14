"""Independent reconstruction of construction records; no simulator imports."""


def require(condition,message):
    if not condition:
        raise ValueError(message)


def reconstruct(genome,encoding,budget,padding=0):
    require(type(budget) is int and budget>=0,'invalid construction budget')
    zero=[0]*35
    if encoding=='direct':
        weights=genome['weights']
        require(len(weights)==35 and all(type(w) is int and -100<=w<=100 for w in weights),'direct genome')
        require(type(padding) is int and padding>=0,'invalid padding')
        active=sum(w!=0 for w in weights)
        if budget<35:
            cost,valid,reason=0,False,'read_budget'
        elif budget<35+active:
            cost,valid,reason=35,False,'expression_budget'
        elif budget<35+active+padding:
            cost,valid,reason=35+active,False,'padding_budget'
        else:
            cost,valid,reason=35+active+padding,bool(active),'constructed' if active else 'empty_structure'
        return dict(weights=weights if valid else zero,cost=cost,valid=valid,reason=reason)
    require(encoding=='developmental','unknown encoding')
    genes=genome['genes']
    bounds=((0,34),(-100,100),(0,34),(-100,100),(0,34),(-100,100),(0,4),(0,10),(0,100),(1,16))
    require(len(genes)==10 and all(type(v) is int and low<=v<=high for v,(low,high) in zip(genes,bounds)),'development genome')
    field=[0]*35
    for index in range(0,6,2):
        field[genes[index]]=min(100,max(-100,field[genes[index]]+genes[index+1]))
    history=[field[:]]
    d,decay,threshold,rounds=genes[6:]
    completed=min(rounds,budget//35)
    for _ in range(completed):
        after=[]
        for index,value in enumerate(field):
            y,x=divmod(index,7)
            adjacent=[]
            for dy,dx in ((-1,0),(1,0),(0,-1),(0,1)):
                yy,xx=y+dy,x+dx
                adjacent.append(field[yy*7+xx] if 0<=yy<5 and 0<=xx<7 else value)
            numerator=16*value+d*sum(n-value for n in adjacent)
            magnitude=max(0,abs(numerator)//16-decay)
            after.append(magnitude if numerator>=0 else -magnitude)
        field=after
        history.append(field[:])
    cost=35*completed
    active=[i for i,v in enumerate(field) if v and abs(v)>=threshold]
    if completed<rounds:
        valid,reason=False,'round_budget'
    elif cost+len(active)>budget:
        valid,reason=False,'expression_budget'
    else:
        cost+=len(active)
        valid,reason=bool(active),'developed' if active else 'empty_structure'
    return dict(weights=[v if i in active else 0 for i,v in enumerate(field)] if valid else zero,
                active_sites=active if valid else [],rounds_completed=completed,
                updates=35*completed,cost=cost,valid=valid,reason=reason,history=history)


def verify_attempt(attempt,padding=0):
    expected=reconstruct(attempt['genome'],attempt['encoding'],attempt['allocation'],padding)
    require(attempt['construction']==expected,'construction history or result mismatch')
    require(attempt['construction_cost']==expected['cost'],'construction charge mismatch')
    remaining=attempt['allocation']-expected['cost']
    valid=expected['valid'] and remaining>0
    require(type(attempt['valid']) is bool and attempt['valid']==valid,'attempt validity')
    reason=expected['reason'] if not expected['valid'] or remaining>0 else 'no_living_energy'
    require(attempt['reason']==reason,'attempt reason')
    require(attempt['failure_loss']==(0 if valid else remaining),'failure loss')
    require(attempt['living_energy']==(remaining if valid else 0),'postconstruction energy')
    return expected


def audit_run(directory):
    from hashlib import sha256
    import json
    from pathlib import Path
    root=Path(directory)
    metadata=json.loads((root/'metadata.json').read_text(encoding='utf-8'))
    require(metadata['status']=='complete' and metadata['schema']=='v2-run-1'
            and metadata['rules']=='v2-world-1','incomplete or unsupported run')
    final_bytes=(root/'final.json').read_bytes()
    require(sha256(final_bytes).hexdigest()==metadata['output_sha256']['final.json'],'final hash mismatch')
    final=json.loads(final_bytes)
    require([a['id'] for a in final['attempts']]==list(range(len(final['attempts']))),'attempt ID coverage')
    for attempt in final['attempts']:
        require(attempt['encoding']==metadata['encoding'],'attempt encoding mismatch')
        verify_attempt(attempt,metadata['config']['direct_padding_cost'])
    return {'scope':'independent construction histories/costs/validity only; not world life-history or spatial replay',
            'attempts':len(final['attempts']), 'successful':sum(a['valid'] for a in final['attempts']),
            'failed':sum(not a['valid'] for a in final['attempts']),
            'construction_cost':sum(a['construction_cost'] for a in final['attempts']),
            'failure_loss':sum(a['failure_loss'] for a in final['attempts']),
            'final_sha256':sha256(final_bytes).hexdigest(),
            'metadata_sha256':sha256((root/'metadata.json').read_bytes()).hexdigest(),
            'audit_sha256':sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__=='__main__':
    import argparse
    import json
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=audit_run(args.directory)
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(result,indent=2))
