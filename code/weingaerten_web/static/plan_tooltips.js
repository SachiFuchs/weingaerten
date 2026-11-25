// /grundriss: hover tooltips of layers, openings, structure (beams/posts) and stairs in the plan SVG.
// Wall tooltips carry a link to the wall on /waende; they freeze when the pointer rests 300 ms so the link can be clicked.
const PlanTip=(function(){let frozen=false,timer=0,el=null;const T=()=>{if(!el){el=document.getElementById('tip');el.addEventListener('mouseleave',()=>idle())}return el};
 function unfreeze(){clearTimeout(timer);frozen=false;T().classList.remove('live')}
 function idle(){unfreeze();hideTip()}
 function link(label,url){const d=document.createElement('div');d.className='tiplinks';const a=document.createElement('a');a.textContent=label;a.href=url;d.appendChild(a);T().appendChild(d);
  timer=setTimeout(()=>{if(T().style.display==='block'){frozen=true;T().classList.add('live')}},300)}
 // true while frozen and the pointer is near the box (the plan must not update the tooltip then)
 function held(e){if(!frozen)return false;const r=T().getBoundingClientRect();
  const dx=Math.max(r.left-e.clientX,0,e.clientX-r.right),dy=Math.max(r.top-e.clientY,0,e.clientY-r.bottom);
  if(Math.hypot(dx,dy)<=40)return true;unfreeze();return false}
 const inTip=n=>!!(n&&T().contains(n));
 addEventListener('keydown',e=>{if(e.key==='Escape')idle()});
 return {unfreeze,idle,link,held,inTip}})();
document.querySelectorAll('polygon.layer,polygon.layer-d').forEach(p=>{p.addEventListener('mousemove',e=>{if(PlanTip.held(e))return;const d=p.dataset;PlanTip.unfreeze();p.setAttribute('stroke','#1C69D4');p.setAttribute('stroke-width','1.5');showTip(e,[d.wall,d.asm,'Schicht '+d.layer+': '+d.material,'Dicke '+d.thickness],d.color);
 if(d.wid)PlanTip.link('Wand anzeigen / bearbeiten','/waende?storey='+encodeURIComponent(d.storey)+'#'+encodeURIComponent(d.wid))});p.addEventListener('mouseleave',e=>{p.setAttribute('stroke','#555');p.setAttribute('stroke-width','0.4');if(!PlanTip.inTip(e.relatedTarget)&&!PlanTip.held(e))PlanTip.idle()})});document.querySelectorAll('g.opening').forEach(g=>{g.addEventListener('mousemove',e=>{if(PlanTip.held(e))return;PlanTip.unfreeze();const d=g.dataset;showTip(e,[d.name,'Öffnung '+d.id+' in '+d.wall,'Rohbau '+d.size,'Brüstung '+d.sill])});g.addEventListener('mouseleave',e=>{if(!PlanTip.held(e))PlanTip.idle()})});document.querySelectorAll('polygon.structure').forEach(p=>{p.addEventListener('mousemove',e=>{if(PlanTip.held(e))return;PlanTip.unfreeze();const d=p.dataset;showTip(e,[d.kind+': '+d.name,d.material,d.size,'Länge '+d.length])});p.addEventListener('mouseleave',e=>{if(!PlanTip.held(e))PlanTip.idle()})});document.querySelectorAll('g.stair').forEach(g=>{g.addEventListener('mousemove',e=>{if(PlanTip.held(e))return;PlanTip.unfreeze();const d=g.dataset;showTip(e,[d.name,d.steps+' Steigungen','Steigung '+d.rise.replace('.',',')+' cm, Auftritt '+d.going.replace('.',',')+' cm'])});g.addEventListener('mouseleave',e=>{if(!PlanTip.held(e))PlanTip.idle()})});
