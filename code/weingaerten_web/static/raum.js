
// Page /raeume: rooms of the storeys (list), room data, floor / wall coverings and shafts.
// View mode shows the computed values; edit mode buffers a copy of the room JSON (`work`) and the shafts (`shafts`)
// until Speichern (ROOM_SAVE, then SHAFT_SAVE / SHAFT_DELETE per changed shaft) or Abbrechen.
let D=JSON.parse(document.getElementById('raumdata').textContent);const EN=D.enums;const el=r=>D.elements[r]||{};
let H=D.house;const ID_OK=/^[a-z0-9]+(-[a-z0-9]+)*$/;
const storeys=()=>(H.storeys||[]).slice().sort((a,b)=>(a.elevation||0)-(b.elevation||0));
const storeyOf=id=>{const q=StoreyPick.of(H);return q&&q.rooms.some(r=>r.id===id)?q:storeys().find(s=>s.rooms.some(r=>r.id===id))};
const hashId=decodeURIComponent(location.hash.slice(1));
let ST=storeyOf(hashId)||StoreyPick.of(H)||{rooms:[],walls:[]};
let roomId=ST.rooms.some(r=>r.id===hashId)?hashId:(ST.rooms[0]||{}).id,tab='floor',editing=false,work=null,shafts=null,curSel=null,drawMode=null,drag=null;
const svg=document.getElementById('roomsvg'),panel=document.getElementById('rpanel'),table=document.getElementById('rtable'),bar=document.getElementById('rbar'),list=document.getElementById('roomlist');
const saveErr=document.getElementById('rsaveerr'),dataBox=document.getElementById('rdata');
const room=()=>ST.rooms.find(r=>r.id===roomId)||ST.rooms[0];
const covAsm=()=>Object.keys(D.elements).filter(r=>r.startsWith('assembly:')&&el(r).category==='covering');
const asmName=r=>el(r).name||r||'–';
const clone=o=>JSON.parse(JSON.stringify(o));const m2=a=>num(a.toFixed(2))+' m²';
const usageName=u=>((EN.room_usage||[]).find(x=>x[0]===u)||[u,u||'–'])[1];
const rectOf=pl=>{const xs=pl.map(p=>p[0]),ys=pl.map(p=>p[1]);return [Math.min(...xs),Math.min(...ys),Math.max(...xs)-Math.min(...xs),Math.max(...ys)-Math.min(...ys)]};
const quad=([x,y,w,h])=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]].map(p=>[Math.round(p[0]*10000)/10000,Math.round(p[1]*10000)/10000]);
const overlap=(a,b)=>Math.max(0,Math.min(a[0]+a[2],b[0]+b[2])-Math.max(a[0],b[0]))*Math.max(0,Math.min(a[1]+a[3],b[1]+b[3])-Math.max(a[1],b[1]));
// shafts of the house that touch this room in plan and open this storey
function roomShafts(r){const ref='storey:'+ST.id;const src=editing?shafts:(H.shafts||[]).map(s=>s.source);
 return src.filter(s=>{const c=(H.shafts||[]).find(x=>x.id===s.id);const rect=rectOf(s.polygon);
  return (!c||c.floor_storeys.concat(c.ceiling_storeys).includes(ref)||s._new)&&r.rects.some(q=>overlap(q,rect)>1e-6)})}
const coverings=()=>editing?work.coverings||(work.coverings=[]):(room().source.coverings||[]);
const computed=id=>(room().coverings||[]).find(c=>c.id===id);
// --- plan of the room (SVG)
let S=80,PAD=30,ox=0,oy=0;const X=x=>PAD+(x-ox)*S,Y=y=>PAD+(y-oy)*S;
const pts=pl=>pl.map(p=>X(p[0]).toFixed(1)+','+Y(p[1]).toFixed(1)).join(' ');
function toWorld(ev){const pt=svg.createSVGPoint();pt.x=ev.clientX;pt.y=ev.clientY;const p=pt.matrixTransform(svg.getScreenCTM().inverse());return [Math.round(((p.x-PAD)/S+ox)*100)/100,Math.round(((p.y-PAD)/S+oy)*100)/100]}
function draw(){const r=room();svg.textContent='';if(!r){drawList();return}
 const [bx,by,bw,bh]=rectOf(r.polygon);ox=bx-0.6;oy=by-0.6;const width=svg.clientWidth||800;S=Math.min(110,(width-2*PAD)/(bw+1.2));
 const W=(bw+1.2)*S+2*PAD,Hh=(bh+1.2)*S+2*PAD;svg.setAttribute('viewBox','0 0 '+W+' '+Hh);svg.setAttribute('height',Math.min(520,Hh*(width/W)));
 const defs=sv('defs',{}),pat=sv('pattern',{id:'rshaft',width:6,height:6,patternUnits:'userSpaceOnUse'});pat.appendChild(sv('rect',{width:6,height:6,fill:'#F3E5F5'}));
 pat.appendChild(sv('path',{d:'M0,6 L6,0',stroke:'#AB47BC'}));defs.appendChild(pat);svg.appendChild(defs);
 (ST.walls||[]).forEach(w=>svg.appendChild(sv('polygon',{points:pts(w.footprint),fill:'#D9CBB8',stroke:'#999','stroke-width':.5})));
 svg.appendChild(sv('polygon',{points:pts(r.polygon),fill:'#F7F3EA',stroke:'#1C69D4','stroke-width':2}));
 const isOn=c=>curSel===c.id;
 coverings().forEach(c=>{const cc=computed(c.id);const color=asmColor(c.assembly);
  if(c.surface==='floor'&&Array.isArray(c.area))svg.appendChild(sv('polygon',{points:pts(c.area),fill:color,'fill-opacity':.55,stroke:isOn(c)?'#1C69D4':'#555','stroke-width':isOn(c)?3:1,'data-cov':c.id,style:'cursor:pointer'}));
  if(c.surface==='floor'&&!Array.isArray(c.area))svg.appendChild(sv('polygon',{points:pts(r.polygon),fill:color,'fill-opacity':.25,stroke:'none','pointer-events':'none'}));
  if(c.surface==='wall'&&cc)cc.segments.forEach(g=>svg.appendChild(sv('line',{x1:X(g.line[0][0]),y1:Y(g.line[0][1]),x2:X(g.line[1][0]),y2:Y(g.line[1][1]),stroke:color,'stroke-width':isOn(c)?9:6,'stroke-opacity':.85,'data-cov':c.id,style:'cursor:pointer'})))});
 roomShafts(r).forEach(s=>svg.appendChild(sv('polygon',{points:pts(s.polygon),fill:'url(#rshaft)',stroke:curSel===s.id?'#1C69D4':'#6A1B9A','stroke-width':curSel===s.id?3:1.5,'data-shaft':s.id,style:'cursor:pointer'})));
 if(drag&&drag.cur){const a=drag.a,b=drag.cur;svg.appendChild(sv('rect',{x:X(Math.min(a[0],b[0])),y:Y(Math.min(a[1],b[1])),width:Math.abs(b[0]-a[0])*S,height:Math.abs(b[1]-a[1])*S,fill:'rgba(28,105,212,.15)',stroke:'#1C69D4'}))}
 const t=sv('text',{x:PAD,y:Hh-8,'font-size':11,fill:'#777'});t.textContent=drawMode?'Rechteck im Plan ziehen ('+(drawMode==='zone'?'Belagsfläche':'Schacht')+')':'Klick auf eine Fläche, Linie oder einen Schacht wählt sie aus';svg.appendChild(t);
 drawHead();drawData();drawList();drawTabs()}
function asmColor(ref){const a=el(ref);const top=(a.layers||[])[a.layers?a.layers.length-1:0];return (el((top||{}).material).appearance||{}).color||'#B0A090'}
svg.addEventListener('pointerdown',ev=>{const t=ev.target;
 if(drawMode&&editing){drag={a:toWorld(ev),cur:null};try{svg.setPointerCapture(ev.pointerId)}catch(e){}return}
 if(t.dataset.cov){tab=coverings().find(c=>c.id===t.dataset.cov).surface;curSel=t.dataset.cov;draw();buildPanel();return}
 if(t.dataset.shaft){tab='shaft';curSel=t.dataset.shaft;draw();buildPanel()}});
svg.addEventListener('pointermove',ev=>{if(!drag)return;drag.cur=toWorld(ev);draw()});
svg.addEventListener('pointerup',()=>{if(!drag)return;const d=drag;drag=null;if(!d.cur||Math.abs(d.cur[0]-d.a[0])<0.05||Math.abs(d.cur[1]-d.a[1])<0.05){draw();return}
 const rect=[Math.min(d.a[0],d.cur[0]),Math.min(d.a[1],d.cur[1]),Math.abs(d.cur[0]-d.a[0]),Math.abs(d.cur[1]-d.a[1])];
 if(drawMode==='zone')addCovering('floor',quad(rect));else addShaft(quad(rect));drawMode=null;draw();buildPanel()});
// --- header, room data, list
function drawHead(){const r=room();document.getElementById('katname').textContent=r?((r.number?r.number+' ':'')+r.name+' – '+(ST.name||ST.id)):'';
 document.getElementById('rtitle').textContent=r?m2(r.area)+' · Umfang '+num(r.perimeter.toFixed(2))+' m · Höhe '+num(r.height.toFixed(2))+' m · '+num(r.volume.toFixed(1))+' m³':'';
 document.getElementById('redit').href='/grundriss?storey='+encodeURIComponent(ST.id)+'#edit';
 const show=(id,on)=>{document.getElementById(id).style.display=on?'':'none'};show('redmode',!editing&&!!r);show('rsave',editing);show('rcancel',editing);
 const sb=document.getElementById('rsave');sb.disabled=saving||!dirty();sb.textContent=saving?'Speichert …':'Speichern und zurück'}
function drawData(){const r=room();dataBox.textContent='';if(!r)return;
 if(!editing){dataBox.append(h('div',{style:'display:flex;gap:1.5rem;flex-wrap:wrap'},
  ...[['Nummer',r.number||'–'],['Nutzung (DIN 277)',r.usage?usageName(r.usage):'–'],['Lichte Höhe',num(r.height.toFixed(2))+' m'+(r.source.height==null?' (aus Geschoss und Boden)':'')],['Id',r.id]]
   .map(([k,v])=>h('div',{},h('div',{class:'note',text:k}),h('b',{text:v})))),r.note?h('p',{class:'note',text:r.note}):null);return}
 const nr=inp(work.number||''),nm=inp(work.name),us=sel([['','– keine –']].concat(EN.room_usage||[]),work.usage||''),hi=inp(work.height==null?'':cmv(work.height),{type:'number',step:'1',placeholder:'automatisch'});
 const nt=inp(work.note||'');const est=h('input',{type:'checkbox'});est.checked=!!work.estimated;
 nr.oninput=()=>{work.number=nr.value.trim()||undefined;drawHead()};nm.oninput=()=>{work.name=nm.value;drawHead()};us.onchange=()=>{work.usage=us.value||undefined;drawHead()};
 hi.oninput=()=>{work.height=hi.value===''?undefined:tom(+hi.value);drawHead()};nt.oninput=()=>{work.note=nt.value||undefined;drawHead()};est.onchange=()=>{work.estimated=est.checked||undefined;drawHead()};
 dataBox.append(field('Nummer',nr,'eindeutig im Haus'),field('Name',nm),field('Nutzung (DIN 277)',us),
  field('Lichte Höhe cm',hi,'leer = Geschosshöhe minus Bodenaufbau'),field('Notiz',nt),field('geschätzt',est))}
const FK='weingaerten.raeume.storey',floorSel=document.getElementById('rfloor'),search=document.getElementById('rsearch');
function fillFloors(){const keep=floorSel.value||localStorage.getItem(FK)||'';floorSel.textContent='';floorSel.appendChild(h('option',{value:'',text:'Alle Geschosse'}));
 storeys().forEach(s=>floorSel.appendChild(h('option',{value:s.id,text:s.name||s.id})));floorSel.value=storeys().some(s=>s.id===keep)?keep:''}
function drawList(){list.textContent='';const f=floorSel.value,q=search.value.trim().toLowerCase();let n=0,tot=0;
 storeys().slice().reverse().forEach(s=>s.rooms.forEach(r=>{tot++;if(f&&s.id!==f)return;if(q&&!((r.number||'')+' '+r.name+' '+r.id+' '+(s.name||'')).toLowerCase().includes(q))return;n++;
  const c=h('div',{class:'wcard'+(r.id===roomId&&s===ST?' on':'')},h('b',{text:(r.number?r.number+' ':'')+r.name}),
   h('div',{class:'note',text:(s.name||s.id)+' · '+m2(r.area)+(r.usage?' · '+r.usage:'')+((r.coverings||[]).length?' · '+r.coverings.length+' Beläge':'')}));
  c.onclick=()=>pickRoom(r.id,s);list.appendChild(c)}));
 document.getElementById('katcount').textContent=(n===tot?tot:n+' von '+tot)+' Räume';const on=list.querySelector('.wcard.on');if(on)on.scrollIntoView({block:'nearest'})}
function pickRoom(id,s){s=s||storeyOf(id);if(!s||(id===roomId&&s===ST)||!confirmDiscard())return;ST=s;roomId=id;stopEdit();
 history.replaceState(null,'','?storey='+encodeURIComponent(s.id)+(new URLSearchParams(location.search).get('embed')?'&embed=1':'')+'#'+encodeURIComponent(id));draw()}
// --- tabs: tables and forms
function drawTabs(){document.querySelectorAll('.rtab').forEach(b=>{b.className=(b.dataset.tab===tab?'btn':'btn2')+' rtab';b.onclick=()=>{tab=b.dataset.tab;curSel=null;drawMode=null;draw();buildPanel()}});
 bar.textContent='';table.textContent='';const r=room();if(!r)return;
 if(editing&&tab==='floor')bar.append(h('button',{class:'btn2',text:'+ Belag ganzer Raum',onclick:()=>{addCovering('floor','room');draw();buildPanel()}}),' ',
  h('button',{class:drawMode==='zone'?'btn':'btn2',text:'+ Teilfläche (im Plan ziehen)',onclick:()=>{drawMode=drawMode==='zone'?null:'zone';draw()}}));
 if(editing&&tab==='wall')bar.append(h('button',{class:'btn2',text:'+ Wandbelag',onclick:()=>{addCovering('wall');draw();buildPanel()}}));
 if(editing&&tab==='shaft')bar.append(h('button',{class:drawMode==='shaft'?'btn':'btn2',text:'+ Schacht (im Plan ziehen)',onclick:()=>{drawMode=drawMode==='shaft'?null:'shaft';draw()}}));
 if(tab==='shaft')return shaftTable(r);
 const rows=coverings().filter(c=>c.surface===tab);
 table.appendChild(h('tr',{},(tab==='floor'?['Id','Aufbau','Bereich','Dicke','Fläche netto','']:['Id','Aufbau','Wände','Höhe von–bis','Länge','Fläche','']).map(x=>h('th',{text:x}))));
 rows.forEach(c=>{const cc=computed(c.id);const a=cc?m2(cc.area):'–';const tr=h('tr',{style:'cursor:pointer'+(curSel===c.id?';background:#F2F7FD':'')});
  const cells=tab==='floor'?[c.id,asmName(c.assembly),Array.isArray(c.area)?'Teilfläche '+m2(cc?cc.gross_area:0):'ganzer Raum',cc?cmf(cc.thickness):'–',a]
   :[c.id,asmName(c.assembly),c.walls==null||c.walls==='all'?'alle':c.walls.map(x=>x.wall).join(', '),c.z?num(cmv(c.z[0]))+'–'+num(cmv(c.z[1]))+' cm':'ganze Höhe',cc?num(cc.length.toFixed(2))+' m':'–',a];
  cells.forEach(v=>tr.appendChild(h('td',{text:v})));tr.appendChild(h('td',{},editing&&!cc?h('span',{class:'note',text:'nach Speichern berechnet'}):null));
  tr.onclick=()=>{curSel=c.id;draw();buildPanel()};table.appendChild(tr)});
 if(!rows.length)table.appendChild(h('tr',{},h('td',{class:'note',text:editing?'Noch kein Belag – oben hinzufügen.':'Keine Beläge – Bearbeiten, um welche anzulegen.'})))}
function shaftTable(r){table.appendChild(h('tr',{},['Id','Name','Zweck','von – bis','Querschnitt','Leitungen'].map(x=>h('th',{text:x}))));
 const P=Object.fromEntries((EN.shaft_purpose||[]).map(x=>[x[0],x[1]]));
 roomShafts(r).forEach(s=>{const tr=h('tr',{style:'cursor:pointer'+(curSel===s.id?';background:#F2F7FD':'')});const [,,w,hh]=rectOf(s.polygon);
  [s.id,s.name,P[s.purpose]||'–',(s.from_storey||'').replace('storey:','')+' – '+(s.to_storey||'').replace('storey:',''),num(cmv(w))+' × '+num(cmv(hh))+' cm',(s.penetrations||[]).map(p=>p.replace('tga-run:','')).join(', ')||'–']
   .forEach(v=>tr.appendChild(h('td',{text:v})));tr.onclick=()=>{curSel=s.id;draw();buildPanel()};table.appendChild(tr)});
 const sh=(H.shafts||[]).filter(s=>roomShafts(r).some(x=>x.id===s.id));
 if(sh.length&&!editing)table.appendChild(h('tr',{},h('td',{colspan:6,class:'note',text:sh.map(s=>s.id+': '+s.cuts.map(c=>c.storey+' '+(c.kind==='floor'?'Boden':'Decke')+' '+m2(c.area)).join(', ')).join(' · ')})))}
function newId(prefix,taken){let n=1;while(taken.has(prefix+n))n++;return prefix+n}
function addCovering(surface,area){const A=covAsm();if(!A.length){alert('Kein Aufbau der Kategorie „Belag“ (covering) im Katalog.');return}
 const taken=new Set(ST.rooms.flatMap(x=>(x.source.coverings||[]).map(c=>c.id)).concat(coverings().map(c=>c.id)));
 const pick=k=>A.find(r=>(el(r).ifc||{}).predefined_type===k)||A[0];
 const c=surface==='floor'?{id:newId('bel-',taken),surface,assembly:pick('FLOORING'),area}:{id:newId('wb-',taken),surface,assembly:pick('SKIRTINGBOARD'),walls:'all',z:[0,0.06]};
 coverings().push(c);curSel=c.id;tab=surface}
function addShaft(polygon){const taken=new Set(shafts.map(s=>s.id));const all=storeys();
 const s={id:newId('schacht-',taken),name:'Schacht',purpose:'supply',polygon,from_storey:'storey:'+ST.id,to_storey:'storey:'+(all[0]||ST).id,estimated:true,_new:true};
 if(s.from_storey===s.to_storey&&all.length>1)s.from_storey='storey:'+all[all.length-1].id;shafts.push(s);curSel=s.id;tab='shaft'}
function buildPanel(){panel.textContent='';panel.style.display='none';if(!editing||!curSel)return;
 const c=coverings().find(x=>x.id===curSel);const s=!c&&shafts.find(x=>x.id===curSel);if(!c&&!s)return;panel.style.display='block';
 if(s)return shaftPanel(s);
 const id=inp(c.id);id.disabled=!!computed(c.id);id.oninput=()=>{c.id=id.value.trim();curSel=c.id;draw()};
 const as=sel(covAsm().map(r=>[r,asmName(r)]),c.assembly);as.onchange=()=>{c.assembly=as.value;draw()};
 const nm=inp(c.name||'');nm.oninput=()=>{c.name=nm.value||undefined};
 const del=h('button',{class:'btn2',text:'Entfernen',onclick:()=>{work.coverings=coverings().filter(x=>x!==c);curSel=null;draw();buildPanel()}});
 panel.append(h('h3',{text:(c.surface==='floor'?'Bodenbelag ':'Wandbelag ')+c.id,style:'margin-top:0'}),field('id',id),field('Aufbau',as,'Kategorie Belag – im Katalog unter Aufbauten'),field('Name',nm));
 if(c.surface==='floor'){if(Array.isArray(c.area)){const [x,y,w,hh]=rectOf(c.area);const f=(v,cb)=>{const i=inp(cmv(v),{type:'number',step:'1',style:'width:80px'});i.onchange=()=>{cb(tom(+i.value));draw()};return i};
   const rect=[x,y,w,hh];const set=k=>v=>{rect[k]=v;c.area=quad(rect)};
   panel.append(c.area.length===4?field('Teilfläche x / y / Breite / Tiefe cm',h('span',{style:'display:flex;gap:4px'},f(x,set(0)),f(y,set(1)),f(w,set(2)),f(hh,set(3)))):h('p',{class:'note',text:'Teilfläche mit '+c.area.length+' Ecken'}))}
  else panel.append(h('p',{class:'note',text:'Gilt für den ganzen Raum außer den Teilflächen und Schächten.'}))}
 else wallForm(c);
 panel.append(h('div',{style:'margin-top:.5rem'},del),h('p',{class:'note',text:'Übernehmen mit Speichern oben.'}))}
function wallForm(c){const r=room();const ws=[...new Set(r.faces.map(f=>f.wall))];const all=h('input',{type:'checkbox'});all.checked=c.walls==null||c.walls==='all';
 const box=h('div',{style:'display:flex;flex-direction:column;gap:2px'});
 const draw2=()=>{box.textContent='';box.style.display=all.checked?'none':'flex';const cur=Array.isArray(c.walls)?c.walls:[];
  ws.forEach(wid=>{const w=ST.walls.find(x=>x.id===wid)||{};const it=cur.find(x=>x.wall===wid);const cb=h('input',{type:'checkbox'});cb.checked=!!it;
   const u0=inp(it&&it.u?cmv(it.u[0]):'',{type:'number',step:'1',placeholder:'von',style:'width:70px'}),u1=inp(it&&it.u?cmv(it.u[1]):'',{type:'number',step:'1',placeholder:'bis',style:'width:70px'});
   const upd=()=>{let list=(Array.isArray(c.walls)?c.walls:[]).filter(x=>x.wall!==wid);if(cb.checked){const x={wall:wid};if(u0.value!==''&&u1.value!=='')x.u=[tom(+u0.value),tom(+u1.value)];list.push(x)}c.walls=list;draw()};
   cb.onchange=upd;u0.onchange=upd;u1.onchange=upd;box.appendChild(h('label',{style:'display:flex;gap:6px;align-items:center'},cb,h('span',{text:(w.name||wid)+' ('+wid+')',style:'min-width:200px'}),u0,u1))})};
 all.onchange=()=>{c.walls=all.checked?'all':[];draw2();draw()};draw2();
 const z0=inp(c.z?cmv(c.z[0]):'',{type:'number',step:'1',placeholder:'0'}),z1=inp(c.z?cmv(c.z[1]):'',{type:'number',step:'1',placeholder:'Wandhöhe'});
 const zs=()=>{c.z=z0.value===''&&z1.value===''?undefined:[tom(+(z0.value||0)),tom(+(z1.value||250))];draw()};z0.onchange=zs;z1.onchange=zs;
 panel.append(field('alle Wände des Raums',all),field('Wände (Bereich u von–bis cm entlang der Wand, leer = ganze Wand)',box),field('Höhe von cm',z0,'über Geschossboden'),field('Höhe bis cm',z1))}
function shaftPanel(s){const runs=['waste_water','water_supply','electrical'].flatMap(k=>((H[k]||{}).runs||[]));const all=storeys();
 const id=inp(s.id);id.disabled=!s._new;id.oninput=()=>{s.id=id.value.trim();curSel=s.id;draw()};const nm=inp(s.name);nm.oninput=()=>{s.name=nm.value;draw()};
 const pu=sel(EN.shaft_purpose||[],s.purpose||'other');pu.onchange=()=>{s.purpose=pu.value};
 const so=all.slice().reverse().map(x=>['storey:'+x.id,x.name||x.id]);const fr=sel(so,s.from_storey),to=sel(so,s.to_storey);fr.onchange=()=>{s.from_storey=fr.value};to.onchange=()=>{s.to_storey=to.value};
 const rect=rectOf(s.polygon);const f=k=>{const i=inp(cmv(rect[k]),{type:'number',step:'1',style:'width:80px'});i.onchange=()=>{rect[k]=tom(+i.value);s.polygon=quad(rect);draw()};return i};
 const pens=h('div',{style:'display:flex;flex-direction:column;gap:2px'});runs.forEach(run=>{const cb=h('input',{type:'checkbox'});cb.checked=(s.penetrations||[]).includes(run.ref);
  cb.onchange=()=>{const p=(s.penetrations||[]).filter(x=>x!==run.ref);if(cb.checked)p.push(run.ref);s.penetrations=p.length?p:undefined};pens.appendChild(h('label',{},cb,' '+(run.name||run.id)))});
 const est=h('input',{type:'checkbox'});est.checked=!!s.estimated;est.onchange=()=>{s.estimated=est.checked||undefined};
 panel.append(h('h3',{text:'Schacht '+s.id,style:'margin-top:0'}),field('id',id),field('Name',nm),field('Zweck',pu),field('oberstes Geschoss (Boden offen)',fr),field('unterstes Geschoss (Decke offen, Boden zu)',to),
  s.polygon.length===4?field('x / y / Breite / Tiefe cm',h('span',{style:'display:flex;gap:4px'},f(0),f(1),f(2),f(3))):h('p',{class:'note',text:'Schacht mit '+s.polygon.length+' Ecken'}),
  field('Leitungen im Schacht',pens),field('geschätzt',est),h('div',{style:'margin-top:.5rem'},h('button',{class:'btn2',text:'Schacht löschen',onclick:()=>{s._deleted=true;shafts=shafts.filter(x=>x!==s);deletedShafts.push(s.id);curSel=null;draw();buildPanel()}})),
  h('p',{class:'note',text:'Der Schacht gilt für das ganze Haus: er öffnet die Böden aller Geschosse von oben bis über dem untersten und deren Decken.'}))}
// --- edit mode
let deletedShafts=[],origShafts=[],saving=false;
const plainShaft=s=>{const o={};Object.keys(s).filter(k=>k[0]!=='_').forEach(k=>{if(s[k]!==undefined)o[k]=s[k]});return o};
// the room JSON as it would be written: an empty covering list is left out
const plainRoom=r=>{const o=clone(r);if(o.coverings&&!o.coverings.length)delete o.coverings;return o};
function dirty(){if(!editing)return false;return JSON.stringify(plainRoom(work))!==JSON.stringify(room().source)||deletedShafts.length>0||shafts.some(s=>s._new||JSON.stringify(plainShaft(s))!==JSON.stringify(origShafts.find(o=>o.id===s.id)))}
function confirmDiscard(){return !dirty()||confirm('Änderungen verwerfen?')}
function startEdit(){const r=room();if(!r)return;editing=true;work=clone(r.source);origShafts=(H.shafts||[]).map(s=>clone(s.source));shafts=clone(origShafts);deletedShafts=[];saveErr.textContent='';draw();buildPanel()}
function stopEdit(){editing=false;work=null;shafts=null;curSel=null;drawMode=null;saveErr.textContent='';panel.style.display='none'}
function saveEdit(){saveErr.textContent='';const err=t=>saveErr.appendChild(h('div',{text:t}));
 const bad=coverings().filter((c,i,a)=>!ID_OK.test(c.id)||a.findIndex(x=>x.id===c.id)!==i).concat(shafts.filter(s=>!ID_OK.test(s.id)));
 if(bad.length){bad.forEach(x=>err('id ungültig oder doppelt: '+x.id+' (nur a–z, 0–9 und -)'));return}
 const steps=[];if(JSON.stringify(plainRoom(work))!==JSON.stringify(room().source))steps.push(()=>post('/api/room/save',{storey:ST.id,room:plainRoom(work),create:false}).then(r=>[r,'Raum '+work.id]));
 deletedShafts.forEach(id=>steps.push(()=>post('/api/shaft/delete',{id}).then(r=>[r,'Schacht '+id])));
 shafts.filter(s=>s._new||JSON.stringify(plainShaft(s))!==JSON.stringify(origShafts.find(o=>o.id===s.id))).forEach(s=>steps.push(()=>post('/api/shaft/save',{shaft:plainShaft(s),create:!!s._new}).then(r=>{if(r.ok)delete s._new;return [r,'Schacht '+s.id]})));
 const run=i=>i>=steps.length?Promise.resolve(true):steps[i]().then(([{ok,j},what])=>{if(!ok){err(what+':');(j.errors||[j.error]).forEach(t=>err(t));return false}return run(i+1)});
 saving=true;drawHead();
 run(0).catch(e=>{err(String(e));return false}).then(done=>reload(done,done?'Gespeichert':null))}
function reload(done,text){fetch('/api/house',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json()).finally(()=>{saving=false}).then(j=>{H=j;ST=(H.storeys||[]).find(s=>s.id===ST.id)||StoreyPick.of(H);
 if(done)stopEdit();else{origShafts=(H.shafts||[]).map(s=>clone(s.source));deletedShafts=deletedShafts.filter(id=>origShafts.some(o=>o.id===id))}draw();buildPanel();if(text)toast(text)})}
document.getElementById('redmode').onclick=startEdit;document.getElementById('rsave').onclick=saveEdit;document.getElementById('rcancel').onclick=()=>{if(confirmDiscard()){stopEdit();draw()}};
document.getElementById('katdetail').addEventListener('input',()=>drawHead());
fillFloors();floorSel.onchange=()=>{localStorage.setItem(FK,floorSel.value);drawList()};search.oninput=drawList;
window.addEventListener('beforeunload',ev=>{if(dirty()){ev.preventDefault();ev.returnValue=''}});
window.addEventListener('hashchange',()=>pickRoom(decodeURIComponent(location.hash.slice(1))));
KatLayout.init('raeume');KatLayout.photos(null);new ResizeObserver(()=>draw()).observe(document.getElementById('katdetail'));
draw();
