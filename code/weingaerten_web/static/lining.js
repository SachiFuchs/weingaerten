// Innendämmung on the page /waende: lined areas of the shown wall face (drawn under the openings), table and form.
// Uses the state of wand.js (D, H, ST, view, wall(), faceRange, mirrorOf, sx, sz, topAt, S, draw, reload).
// window property, not const: wand.js runs (and draws) before this part of the script is reached
window.LiningUI=(()=>{
 const bar=document.getElementById('linbar'),panel=document.getElementById('linpanel'),tab=document.getElementById('lintable');
 let work=null;const errBox=h('div',{style:'color:#C62828;margin:.4rem 0'});
 const asms=()=>Object.keys(D.elements).filter(r=>r.startsWith('assembly:')&&el(r).category==='interior_lining');
 // the face seen in the current view: exterior walls only from inside, interior walls left (Außenansicht) / right
 const faceOf=w=>w.category==='exterior_wall'?(view==='inside'?'inside':null):(view==='outside'?'left':'right');
 const range=(w,f)=>{const r=w.u_range[f]||w.u_range.left;return [Math.min(...r),Math.max(...r)]};
 const top=w=>Math.max(...(w.profile||[[0,w.height]]).map(p=>p[1]));
 const listOf=w=>(ST.linings||[]).filter(l=>l.wall===w.id);
 const errorsOf=w=>(H.errors||[]).filter(e=>e.kind==='lining'&&e.wall===w.id&&e.where.startsWith(ST.ref+'.'));
 const z1Of=(w,l)=>l.z1==null?top(w):l.z1;
 function plain(w,l){const o={id:l.id,assembly:l.assembly,face:l.face,u0:l.u0,u1:l.u1};if(l.z0>1e-6)o.z0=l.z0;
  if(l.z1!=null&&Math.abs(l.z1-top(w))>1e-6)o.z1=l.z1;if(l.note)o.note=l.note;return o}
 function problems(w,l){const out=[],[a,b]=range(w,l.face),z1=z1Of(w,l);
  if(!(l.u1-l.u0>1e-4))out.push('Breite muss > 0 sein');if(!(z1-l.z0>1e-4))out.push('Höhe muss > 0 sein');if(l.z0<0)out.push('Unterkante < 0');
  if(l.u0<a-1e-3||l.u1>b+1e-3)out.push('Bereich ragt über die Wand');if(z1>top(w)+1e-3)out.push('Oberkante höher als die Wand');
  if(!l.assembly)out.push('Aufbau fehlt');
  listOf(w).forEach(x=>{if(x.id===l.id||x.face!==l.face)return;if(Math.min(l.u1,x.u1)-Math.max(l.u0,x.u0)>1e-3&&Math.min(z1,x.z1)-Math.max(l.z0,x.z0)>1e-3)out.push('Überlappt mit '+x.id)});
  return out}
 // outline of the area: bottom z0, top min(z1, wall top), sampled so that the roof line and z1 meet correctly
 function outline(w,l){const z1=z1Of(w,l),us=[l.u0,l.u1];for(let i=1;i<24;i++)us.push(l.u0+(l.u1-l.u0)*i/24);
  (w.profile||[]).forEach(p=>{if(p[0]>l.u0&&p[0]<l.u1)us.push(p[0])});us.sort((x,y)=>x-y);
  return [[l.u0,l.z0],...us.map(u=>[u,Math.min(z1,topAt(w,u))]),[l.u1,l.z0]]}
 function defs(){const d=sv('defs',{}),p=sv('pattern',{id:'wlin',width:10,height:10,patternUnits:'userSpaceOnUse',patternTransform:'rotate(-45)'});
  p.appendChild(sv('rect',{width:10,height:10,fill:'#E8D3AE'}));p.appendChild(sv('line',{x1:0,y1:0,x2:0,y2:10,stroke:'#A9804A','stroke-width':2}));d.appendChild(p);return d}
 function drawArea(w,l,pts){const isWork=work&&work.id===l.id;const pr=isWork?problems(w,l):[];
  const poly=sv('polygon',{points:outline(w,l).map(p=>sx(w,p[0]).toFixed(1)+','+sz(w,p[1]).toFixed(1)).join(' '),fill:'url(#wlin)','fill-opacity':.75,
   stroke:pr.length?'#C62828':(isWork?'#1C69D4':'#8A6534'),'stroke-width':isWork?2.5:1.2,'stroke-dasharray':isWork?'6 4':'none',style:'cursor:pointer'});
  const info=['Innendämmung '+l.id,el(l.assembly).name||l.assembly,'Breite '+num(cmv(l.u1-l.u0))+' cm, Höhe '+num(cmv(z1Of(w,l)-l.z0))+' cm'+(l.area!=null?', netto '+num(l.area.toFixed(2))+' m²':''),'Öffnungen werden ausgespart'];
  poly.addEventListener('pointermove',ev=>showTip(ev,info));poly.addEventListener('pointerleave',hideTip);
  poly.addEventListener('pointerdown',ev=>{ev.stopPropagation();edit(l.id)});svg.appendChild(poly);pts.add(l.u0);pts.add(l.u1)}
 function drawAreas(w,pts){const f=faceOf(w);if(!f)return;svg.appendChild(defs());
  listOf(w).filter(l=>l.face===f&&!(work&&work.id===l.id)).forEach(l=>drawArea(w,l,pts));
  if(work&&work.face===f)drawArea(w,work,pts)}
 function table(w){tab.textContent='';bar.textContent='';const f=faceOf(w);const [fa,fb]=f?range(w,f):[0,0];const m=mirrorOf(w,view);
  if(!f)bar.appendChild(h('p',{class:'note',text:'Innendämmung liegt auf der Innenseite – Innenansicht wählen.'}));
  else if(!asms().length)bar.appendChild(h('p',{class:'note',text:'Kein Aufbau der Kategorie Innendämmung im Katalog.'}));
  else bar.appendChild(h('button',{class:'btn2',text:'+ Dämmbereich',onclick:()=>create(w,f)}));
  const rows=listOf(w);const errs=errorsOf(w);if(!rows.length&&!errs.length)return;
  tab.appendChild(h('tr',{},['Id','Seite','Aufbau','Abstand links','Breite','Unterkante','Oberkante','netto m²','ausgespart'].map(x=>h('th',{text:x}))));
  rows.forEach(l=>{const [a,b]=range(w,l.face);const tr=h('tr',{style:'cursor:pointer'+(work&&work.id===l.id?';background:#F2F7FD':'')},h('td',{text:l.id}),
   h('td',{text:{inside:'innen',left:'links',right:'rechts'}[l.face]}),h('td',{text:el(l.assembly).name||l.assembly}),
   h('td',{class:'n',text:num(cmv(m?b-l.u1:l.u0-a))}),h('td',{class:'n',text:num(cmv(l.u1-l.u0))}),h('td',{class:'n',text:num(cmv(l.z0))}),
   h('td',{class:'n',text:num(cmv(l.z1))}),h('td',{class:'n',text:num(l.area.toFixed(2))}),h('td',{text:(l.openings||[]).join(', ')||'–'}));
   tr.onclick=()=>edit(l.id);tab.appendChild(tr)});
  errs.forEach(e=>{const tr=h('tr',{style:'color:#C62828'},h('td',{text:e.lining}),h('td',{colspan:'7',text:'Fehler: '+e.message+' (nicht berechnet)'}),
   h('td',{},h('button',{class:'btn2',text:'Löschen',onclick:()=>remove(w,e.lining)})));tab.appendChild(tr)})}
 function create(w,f){const ids=new Set((ST.linings||[]).map(l=>l.id).concat((H.errors||[]).filter(e=>e.kind==='lining').map(e=>e.lining)));
  let n=1;while(ids.has('id-'+n))n++;const [a,b]=range(w,f);
  work={id:'id-'+n,assembly:asms()[0],face:f,u0:a,u1:b,z0:0,z1:null,note:'',_new:true};buildPanel();draw()}
 function edit(id){const w=wall();const l=listOf(w).find(x=>x.id===id);if(!l)return;
  work={id:l.id,assembly:l.assembly,face:l.face,u0:l.u0,u1:l.u1,z0:l.z0,z1:Math.abs(l.z1-top(w))<1e-6?null:l.z1,note:l.note||''};buildPanel();draw()}
 function close(){work=null;buildPanel();draw()}
 let pf={};
 function buildPanel(){panel.style.display=work?'block':'none';panel.textContent='';errBox.textContent='';if(!work)return;const w=wall();
  const A=sel(asms().map(r=>[r,el(r).name||r]),work.assembly);const id=inp(work.id);id.disabled=!work._new;
  const L=inp('',{type:'number',step:'1'}),B=inp('',{type:'number',step:'1',min:'0'}),Z0=inp('',{type:'number',step:'1',min:'0'}),
   Z1=inp('',{type:'number',step:'1',min:'0',placeholder:'bis Wandoberkante'}),N=inp(work.note||'');pf={L,B,Z0,Z1};
  const probs=h('div',{id:'linprobs',style:'color:#C62828;margin:.4rem 0'});
  const [fa,fb]=range(w,work.face);const m=mirrorOf(w,view);
  A.onchange=()=>{work.assembly=A.value;draw()};id.oninput=()=>{work.id=id.value.trim();draw()};N.oninput=()=>{work.note=N.value};
  L.oninput=()=>{if(L.value==='')return;const v=tom(+L.value),wd=work.u1-work.u0;work.u0=Math.round((m?fb-v-wd:fa+v)*10000)/10000;work.u1=work.u0+wd;fill('L');draw()};
  B.oninput=()=>{if(B.value==='')return;const v=tom(+B.value);if(m)work.u0=Math.round((work.u1-v)*10000)/10000;else work.u1=Math.round((work.u0+v)*10000)/10000;fill('B');draw()};
  Z0.oninput=()=>{if(Z0.value!==''){work.z0=tom(+Z0.value);fill('Z0');draw()}};Z1.oninput=()=>{work.z1=Z1.value===''?null:tom(+Z1.value);fill('Z1');draw()};
  const full=h('button',{class:'btn2',text:'ganze Wandseite',onclick:()=>{[work.u0,work.u1]=[fa,fb];work.z0=0;work.z1=null;fill();draw()}});
  const save=h('button',{class:'btn',id:'linsave',text:'Speichern',onclick:()=>store(w)});
  const del=work._new?null:h('button',{class:'btn2',text:'Löschen',onclick:()=>remove(w,work.id)});
  panel.append(h('h3',{text:work._new?'Neuer Dämmbereich':'Dämmbereich '+work.id,style:'margin-top:0'}),field('Aufbau',A),field('id',id),
   field('Abstand links cm',L,'wie in der aktuellen Ansicht'),field('Breite cm',B),field('Unterkante cm',Z0,'über Geschossboden'),
   field('Oberkante cm',Z1,'leer = bis zur Wandoberkante (Dachschräge)'),field('Notiz',N),probs,errBox,
   h('div',{style:'display:flex;gap:.5rem;flex-wrap:wrap'},save,full,del,h('button',{class:'btn2',text:'Abbrechen',onclick:close})),
   h('p',{class:'note',text:'Schichten von der Wand zum Raum; Fenster und Türen werden ausgespart (keine Laibung).'}));
  fill()}
 function fill(skip){if(!work||!pf.L)return;const w=wall();const [fa,fb]=range(w,work.face);const m=mirrorOf(w,view);
  if(skip!=='L')pf.L.value=cmv(m?fb-work.u1:work.u0-fa);if(skip!=='B')pf.B.value=cmv(work.u1-work.u0);
  if(skip!=='Z0')pf.Z0.value=cmv(work.z0);if(skip!=='Z1')pf.Z1.value=work.z1==null?'':cmv(work.z1);
  const pr=problems(w,work);const box=document.getElementById('linprobs');if(box){box.textContent='';pr.forEach(t=>box.appendChild(h('div',{text:t})))}
  const b=document.getElementById('linsave');if(b)b.disabled=pr.length>0||!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(work.id)}
 function store(w){errBox.textContent='';const body=plain(w,work);
  post('/api/lining/save',{storey:ST.id,wall:w.id,lining:body,create:!!work._new}).then(({ok,j})=>{
   if(!ok||j.error){(j.errors||[j.error]).forEach(t=>errBox.appendChild(h('div',{text:t})));return}
   work=null;buildPanel();reload(false,'Dämmbereich gespeichert')})}
 function remove(w,id){if(!confirm('Dämmbereich '+id+' löschen?'))return;
  post('/api/lining/delete',{storey:ST.id,wall:w.id,id}).then(({ok,j})=>{if(!ok||j.error){alert((j.errors||[j.error]).join('\n'));return}
   work=null;buildPanel();reload(false,'Dämmbereich gelöscht')})}
 function reset(){work=null;buildPanel()}
 return {drawAreas,table,reset,dirty:()=>!!work}})();
draw();
