"""Self-contained local experiment viewer; no network or simulation mutations."""

from dataclasses import asdict
import json


def write_viewer(path, config, snapshots, frames):
    payload = json.dumps({"config": asdict(config), "metrics": snapshots, "frames": frames},
                         separators=(",", ":"), allow_nan=False)
    template = '''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>BitGenesis · V0 experiment</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0c131a;color:#e4ede8;font:16px system-ui,sans-serif}
main{max-width:1200px;margin:auto;padding:38px 24px}h1{font-size:38px;margin:4px 0 12px;letter-spacing:-1px}
.eyebrow{color:#8edabb;font-size:13px;letter-spacing:3px}p{color:#a8bab5;line-height:1.6;max-width:850px}
.grid{display:grid;grid-template-columns:1.1fr 1fr;gap:24px;margin-top:26px}.panel{background:#131f28;border:1px solid #2a3d46;border-radius:14px;padding:20px}
h2{font-size:18px;margin:0 0 16px}.stats{display:flex;gap:22px;flex-wrap:wrap;margin-bottom:16px}.stats b{display:block;font-size:27px;color:#b4f0d2}.stats span{font-size:12px;color:#a8bab5}
canvas{width:100%;display:block;border-radius:6px}#world{aspect-ratio:1;image-rendering:pixelated;background:#090f15}.controls{display:flex;gap:12px;align-items:center;margin-top:16px}
input{flex:1;min-width:40px;accent-color:#9be4c1}button,select{background:#233e43;color:#e4ede8;border:1px solid #52776e;border-radius:6px;padding:8px 12px}button{cursor:pointer}.legend{font-size:12px;color:#9cb3aa;margin-top:12px}.chart{height:160px}.note{font-size:13px;border-top:1px solid #2a3d46;padding-top:20px;margin-top:24px}@media(max-width:760px){.grid{grid-template-columns:1fr}h1{font-size:30px}}
</style><main>
<div class="eyebrow">BITGENESIS / EXPERIMENT OBSERVATORY</div>
<h1>Life from simple rules?</h1>
<a href="lineage.html" style="color:#9be4c1">Inspect individuals and ancestry →</a>
<p>A minimal Darwinian world. Individuals inherit a probability of moving; energy, local food and space constrain survival and reproduction. No food-seeking controller is built in.</p>
<div class="grid"><section class="panel"><h2>World replay</h2><div class="stats"><div><b id="tick"></b><span>TICK</span></div><div><b id="population"></b><span>POPULATION</span></div><div><b id="generation"></b><span>MAX GENERATION</span></div></div>
<canvas id="world" width="640" height="640" aria-label="World replay: resources and organisms"></canvas>
<div class="controls"><button id="play">Play</button><input id="scrub" type="range" min="0" value="0" aria-label="Replay frame"><select id="color" aria-label="Organism color"><option value="genome">Movement trait</option><option value="founder">Founder lineage</option></select></div>
<div class="legend">Green background: food · Filled cells: organisms · Trait colors: blue (rest) → orange (move). Lineage colors are labels, not species.</div></section>
<section class="panel"><h2>Population through time</h2><canvas id="populationChart" class="chart" width="560" height="160" aria-label="Population time series"></canvas>
<h2>Mean inherited movement probability</h2><canvas id="traitChart" class="chart" width="560" height="160" aria-label="Mean movement probability time series"></canvas>
<h2>Surviving founder lineages</h2><canvas id="lineageChart" class="chart" width="560" height="160" aria-label="Founder lineage count time series"></canvas>
<p id="description"></p></section></div>
<p class="note">V0 / v0-darwin-1. Designed organisms and reproduction; this run is not evidence of intelligence or open-ended evolution. Compare multiple seeds and controls. Replay and long-run charts are sampled and may omit brief changes; metrics.csv covers every tick. Inspect metadata.json for sampling intervals and events.jsonl / lineage.json for raw lifecycle observations.</p>
</main><script>
const data=__PAYLOAD__;const $=id=>document.getElementById(id);const slider=$('scrub');slider.max=data.frames.length-1;
function chart(id,key,color,fixedMax){const el=$(id),ctx=el.getContext('2d'),w=el.width,h=el.height,p=28;const max=fixedMax||data.metrics.reduce((highest,m)=>Math.max(highest,m[key]||0),1);ctx.clearRect(0,0,w,h);ctx.strokeStyle='#30454c';ctx.beginPath();ctx.moveTo(p,10);ctx.lineTo(p,h-p);ctx.lineTo(w-10,h-p);ctx.stroke();ctx.fillStyle='#a8bab5';ctx.font='11px system-ui';ctx.fillText(String(Math.round(max)),0,15);ctx.fillText('0',8,h-p);ctx.fillText(String(data.metrics.at(-1).tick),w-45,h-8);ctx.strokeStyle=color;ctx.lineWidth=2;ctx.beginPath();let pen=false;data.metrics.forEach(m=>{if(m[key]===null){pen=false;return;}const x=p+m.tick/Math.max(1,data.metrics.at(-1).tick)*(w-p-10),y=h-p-m[key]/max*(h-p-10);if(pen)ctx.lineTo(x,y);else ctx.moveTo(x,y);pen=true;});ctx.stroke();}
function draw(){const f=data.frames[Number(slider.value)],m=f.metrics,c=data.config,ctx=$('world').getContext('2d'),w=640/c.width,h=640/c.height;ctx.fillStyle='#090f15';ctx.fillRect(0,0,640,640);f.food.forEach((food,p)=>{ctx.fillStyle=`rgba(55,175,112,${food/Math.max(1,c.food_capacity)*0.65})`;ctx.fillRect((p%c.width)*w,Math.floor(p/c.width)*h,w,h);});f.organisms.forEach(([p,g,founder])=>{const hue=$('color').value==='founder'?(founder*137.508)%360:220-g/1000*195;ctx.fillStyle=`hsl(${hue} 75% 65%)`;ctx.fillRect((p%c.width)*w+w*.15,Math.floor(p/c.width)*h+h*.15,w*.7,h*.7);});$('tick').textContent=f.tick;$('population').textContent=m.population;$('generation').textContent=m.max_generation??'—';}
slider.oninput=draw;$('color').onchange=draw;let timer=null;$('play').onclick=()=>{if(timer){clearInterval(timer);timer=null;$('play').textContent='Play';return;}if(Number(slider.value)===data.frames.length-1)slider.value=0;$('play').textContent='Pause';timer=setInterval(()=>{slider.value=Math.min(Number(slider.value)+1,data.frames.length-1);draw();if(Number(slider.value)===data.frames.length-1){clearInterval(timer);timer=null;$('play').textContent='Play';}},100);};
$('description').textContent=`Seed ${data.config.seed} · ${data.config.width} × ${data.config.height} cells · mutation probability ${data.config.mutation_probability/10}% per birth. Trait scale: 0–1000. Empty populations have no mean trait.`;
chart('populationChart','population','#9be4c1');chart('traitChart','mean_genome','#e9b36f',1000);chart('lineageChart','founder_lineages','#8fb7ef');draw();
</script></html>'''
    path.write_text(template.replace("__PAYLOAD__", payload), encoding="utf-8")
