"""Standalone inspection of organism records, parent chains, and direct children."""

from dataclasses import asdict
import json


def write_lineage_viewer(path, world):
    payload = json.dumps({"tick": world.tick,
                          "records": [asdict(o) for o in world.lineage.values()]},
                         separators=(",", ":"), allow_nan=False)
    page = '''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>BitGenesis · Lineage inspector</title>
<style>body{margin:0;background:#0c131a;color:#e4ede8;font:16px system-ui,sans-serif}main{max-width:1100px;margin:40px auto;padding:0 24px}a{color:#9be4c1}h1{font-size:34px}p{color:#a8bab5;line-height:1.6}input,button{font:inherit;background:#20363d;color:#e4ede8;border:1px solid #53796d;border-radius:6px;padding:9px}button{cursor:pointer}table{border-collapse:collapse;width:100%;margin:20px 0;font-size:14px}td,th{text-align:left;border-bottom:1px solid #30454c;padding:9px;white-space:nowrap}.scroll{overflow-x:auto}.cards{display:flex;gap:28px;flex-wrap:wrap}.cards strong{font-size:28px;display:block}.cards span{font-size:12px;color:#a8bab5}#message{color:#ecc583}section{background:#131f28;padding:20px;border-radius:12px;margin:24px 0}.chain{display:flex;gap:8px;flex-wrap:wrap}</style>
<main><a href="index.html">← World replay</a><h1>Trace an individual's history</h1>
<p>Each individual has a recorded parent, inherited movement trait, birth and death time. Founder colors identify ancestry; they do not identify species.</p>
<div class="cards"><div><strong id="total"></strong><span>EVER BORN</span></div><div><strong id="alive"></strong><span>ALIVE AT FINAL TICK</span></div><div><strong id="founders"></strong><span>FOUNDERS</span></div></div>
<section><label for="identity">Organism ID</label> <input id="identity" type="number" min="0" step="1" value="0"> <button id="inspect">Inspect</button><p id="message" role="status"></p><h2 id="selected">Individual</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Parent</th><th>Founder</th><th>Generation</th><th>Trait</th><th>Born</th><th>Died</th><th>Offspring</th><th>Last energy</th></tr></thead><tbody id="detail"></tbody></table></div>
<h2>Ancestry, oldest first</h2><div id="ancestry" class="chain"></div><h2>Direct children</h2><div id="children" class="chain"></div></section>
<section><h2>Founder outcomes</h2><p>Living descendants include the founder when still alive. Direct offspring are not the same as all descendants.</p><div class="scroll"><table><thead><tr><th>Founder</th><th>Trait</th><th>Direct offspring</th><th>Total lineage born</th><th>Living descendants</th></tr></thead><tbody id="founderRows"></tbody></table></div></section>
<p id="note"></p></main><script>
const data=__PAYLOAD__,$=id=>document.getElementById(id),records=new Map(data.records.map(o=>[o.id,o])),children=new Map(),counts=new Map();
for(const o of data.records){if(o.parent_id!==null){if(!children.has(o.parent_id))children.set(o.parent_id,[]);children.get(o.parent_id).push(o.id);}if(!counts.has(o.founder_id))counts.set(o.founder_id,{total:0,alive:0});counts.get(o.founder_id).total++;if(o.death_tick===null)counts.get(o.founder_id).alive++;}
function button(id){const b=document.createElement('button');b.textContent='#'+id;b.onclick=()=>{$('identity').value=id;inspect();};return b;}
function cell(row,value){const td=document.createElement('td');td.textContent=value;row.append(td);}
function inspect(){const raw=$('identity').value,id=Number(raw),o=records.get(id);if(raw===''||!Number.isInteger(id)||!o){$('message').textContent='No recorded organism with that ID.';return;}$('message').textContent='';$('selected').textContent='Individual #'+id;$('detail').replaceChildren();const row=document.createElement('tr');[o.id,o.parent_id??'Founder',o.founder_id,o.generation,o.genome,o.birth_tick,o.death_tick??'Alive',o.offspring,o.energy].forEach(v=>cell(row,v));$('detail').append(row);const chain=[];let current=o;while(current){chain.push(current.id);current=current.parent_id===null?null:records.get(current.parent_id);}$('ancestry').replaceChildren(...chain.reverse().map(button));const ids=children.get(id)||[];$('children').replaceChildren(...ids.map(button));if(!ids.length)$('children').textContent='No direct offspring recorded.';}
const founders=data.records.filter(o=>o.parent_id===null);$('total').textContent=data.records.length;$('alive').textContent=data.records.filter(o=>o.death_tick===null).length;$('founders').textContent=founders.length;
for(const o of founders){const row=document.createElement('tr'),td=document.createElement('td');td.append(button(o.id));row.append(td);[o.genome,o.offspring,counts.get(o.id).total,counts.get(o.id).alive].forEach(v=>cell(row,v));$('founderRows').append(row);}
$('inspect').onclick=inspect;$('identity').onkeydown=e=>{if(e.key==='Enter')inspect();};$('note').textContent=`Recorded through tick ${data.tick}. Living individuals' offspring counts are censored at that tick; energy and position are last-observed values. Movement, sensing, memory, and intelligence cannot be inferred from ancestry alone.`;if(data.records.length)inspect();else $('message').textContent='This experiment contains no organisms.';
</script></html>'''
    path.write_text(page.replace("__PAYLOAD__", payload), encoding="utf-8")
