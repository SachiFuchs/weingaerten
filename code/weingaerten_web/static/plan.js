// /grundriss plan editor: walls of the shown storey with snapping, open ends, rotate/split, outline check and WALLS_SAVE.
const PD=JSON.parse(document.getElementById('plandata').textContent);
const ASM=PD.assemblies;let H=PD.house;let ST=StoreyPick.of(H);
const area=document.getElementById('planarea'),view=document.getElementById('planview'),svg=document.getElementById('planedsvg'),panel=document.getElementById('planpanel');
const btn=document.getElementById('planedit');
const clone=o=>JSON.parse(JSON.stringify(o));
const EPS=0.0005,SNAP=0.15;
let saved=null,walls=[],rooms=[],height=0,deleted=new Set(),roomDel=new Set(),changes=new Map(),takes={};
let pick=null,mode=null,dragSt=null,pull=true;
// save errors of the server; a click highlights the walls / openings / rooms named in the message
let srvErr=[],errAt=-1,errHi=new Set();
function errIds(t){const ids=new Set(),tok=String(t).match(/[\w-]+/g)||[];const known=new Set(walls.map(w=>w.id).concat(rooms.map(r=>r.id),...walls.map(w=>w.ops.map(o=>o.id))));tok.forEach(x=>{if(known.has(x))ids.add(x)});return ids}
function showErr(i){errAt=errAt===i?-1:i;errHi=errAt<0?new Set():errIds(srvErr[i]);const w=walls.find(x=>errHi.has(x.id));if(w)pick={type:'wall',id:w.id};render();
 if(w){const p=svg.querySelector('[data-wall="'+CSS.escape(w.id)+'"]');if(p)p.scrollIntoView({block:'center',inline:'center',behavior:'smooth'})}}
function load(){srvErr=[];errAt=-1;errHi=new Set();ST=StoreyPick.of(H);
 walls=ST.walls.map(w=>({id:w.id,name:w.name,assembly:w.assembly,start:w.start.slice(),end:w.end.slice(),reference:w.reference,outside:w.outside,shape:clone(w.shape||{kind:'rect'}),wh:(w.shape||{}).kind!=='roof'&&w.height<ST.height-1e-6?w.height:undefined,free:(w.free_ends||[]).slice(),  ops:(w.openings||[]).map(o=>({id:o.id,offset:o.offset,width:o.rough.width}))}));
 rooms=ST.rooms.map(r=>({id:r.id,name:r.name,polygon:r.polygon.map(p=>p.slice())}));height=ST.height;
 saved={walls:clone(walls),rooms:clone(rooms),height};deleted=new Set();roomDel=new Set();changes=new Map();takes={}}
load();
// geometry helpers
const len=w=>Math.hypot(w.end[0]-w.start[0],w.end[1]-w.start[1]);
const dir=w=>{const L=len(w)||1;return [(w.end[0]-w.start[0])/L,(w.end[1]-w.start[1])/L]};
const horiz=w=>Math.abs(w.end[1]-w.start[1])<EPS;
const thick=w=>(ASM[w.assembly]||{}).thickness||0.3;
function nIn(w){const d=dir(w);if((ASM[w.assembly]||{}).category==='interior_wall')return [-d[1],d[0]];return w.outside==='right'?[d[1],-d[0]]:[-d[1],d[0]]}
function shiftOf(w){const T=thick(w);return {outside_face:0,left_face:0,center:T/2}[w.reference]??T}
function band(w){const n=nIn(w),T=thick(w),s=shiftOf(w);const P=(p,t)=>[p[0]+n[0]*(t-s),p[1]+n[1]*(t-s)];return [P(w.start,0),P(w.end,0),P(w.end,T),P(w.start,T)]}
const same=(a,b)=>Math.abs(a[0]-b[0])<0.001&&Math.abs(a[1]-b[1])<0.001;
function bbox(w){const b=band(w);return [Math.min(...b.map(p=>p[0])),Math.min(...b.map(p=>p[1])),Math.max(...b.map(p=>p[0])),Math.max(...b.map(p=>p[1]))]}
// T-joint (like the core): the end point lies inside the band of a crossing wall, or inside the corner block of
// that wall with its corner neighbour (walls are axis-parallel: depth of o = across axis, depth of the neighbour = along axis of o)
function teeOf(w,p){const inB=(B,i)=>p[i]>=B[i]-0.001&&p[i]<=B[i+2]+0.001;return walls.find(o=>{if(o===w||horiz(o)===horiz(w))return false;const B=bbox(o),a=horiz(o)?0:1;if(!inB(B,1-a))return false;if(inB(B,a))return true;
  return walls.some(n=>n!==o&&horiz(n)!==horiz(o)&&(same(n.start,o.start)||same(n.end,o.start)||same(n.start,o.end)||same(n.end,o.end))&&inB(bbox(n),a))})||null}
function savedOf(id){return saved.walls.find(w=>w.id===id)}
function opsAbs(w){// openings with absolute offset kept (like the core)
 const sv=savedOf(w.id);const d=dir(w);return w.ops.map(o=>{let off=o.offset;
  if(sv&&!o.taken){const ds=dir(sv);if(ds[0]*d[0]+ds[1]*d[1]>0.9999)off=o.offset+((sv.start[0]-w.start[0])*d[0]+(sv.start[1]-w.start[1])*d[1])}
  return {id:o.id,u0:off,u1:off+o.width}})}
// view transform
let bx0,by0,bx1,by1,S=60,MG=40;
function frame(){const xs=[],ys=[];walls.forEach(w=>{xs.push(w.start[0],w.end[0]);ys.push(w.start[1],w.end[1])});
 if(!xs.length){xs.push(0,10);ys.push(0,8)}bx0=Math.min(...xs)-2;by0=Math.min(...ys)-2;bx1=Math.max(...xs)+2;by1=Math.max(...ys)+2;
 const W=(bx1-bx0)*S+2*MG,Hh=(by1-by0)*S+2*MG;PlanZoom.base(svg,W,Hh)}
const X=x=>MG+(x-bx0)*S,Y=y=>MG+(y-by0)*S;
function toWorld(ev){const pt=svg.createSVGPoint();pt.x=ev.clientX;pt.y=ev.clientY;const p=pt.matrixTransform(svg.getScreenCTM().inverse());return [(p.x-MG)/S+bx0,(p.y-MG)/S+by0]}
const grid=(v,ev)=>{const g=ev&&ev.shiftKey?0.1:0.01;return Math.round(v/g)*g};
const r4=v=>Math.round(v*10000)/10000;
// rooms are rectangular polygons (like the core): area, label point, cleaning of duplicate / collinear points
const parea=pl=>Math.abs(pl.reduce((s,p,i)=>{const q=pl[(i+1)%pl.length];return s+p[0]*q[1]-q[0]*p[1]},0))/2;
function pcenter(pl){let a=0,cx=0,cy=0;pl.forEach((p,i)=>{const q=pl[(i+1)%pl.length],c=p[0]*q[1]-q[0]*p[1];a+=c;cx+=(p[0]+q[0])*c;cy+=(p[1]+q[1])*c});return a?[cx/(3*a),cy/(3*a)]:pl[0]}
function pclean(pl){const a=pl.map(p=>[r4(p[0]),r4(p[1])]);let again=true;
 while(again&&a.length>4){again=false;for(let i=0;i<a.length;i++){const p=a[(i+a.length-1)%a.length],c=a[i],n=a[(i+1)%a.length];
  if(same(p,c)||(Math.abs(p[0]-c[0])<EPS&&Math.abs(n[0]-c[0])<EPS)||(Math.abs(p[1]-c[1])<EPS&&Math.abs(n[1]-c[1])<EPS)){a.splice(i,1);again=true;break}}}return a}
const hEdge=(a,b)=>Math.abs(a[1]-b[1])<EPS;
function mark(id,txt){changes.set(id,txt)}
// checks
function problems(){const out=[];const ends=[];walls.forEach(w=>{ends.push(w.start,w.end)});
 walls.forEach(w=>{if(Math.abs(w.end[0]-w.start[0])>=EPS&&Math.abs(w.end[1]-w.start[1])>=EPS)out.push({w:w.id,t:'Wand '+w.id+' nicht im 90°-Raster'});
  if(len(w)<0.01)out.push({w:w.id,t:'Wand '+w.id+' hat keine Länge'});
  opsAbs(w).forEach(o=>{if(o.u0<-0.001||o.u1>len(w)+0.001)out.push({w:w.id,o:o.id,soft:true,t:'Öffnung '+o.id+' liegt außerhalb – auf der Seite Wände korrigieren'})})});
 rooms.forEach(r=>{const pl=r.polygon;if(pl.length<4||pl.some((p,i)=>same(p,pl[(i+1)%pl.length])))out.push({w:r.id,t:'Raum '+r.id+': Kante ohne Länge – geteilte Kante ziehen'})});
 const bb=bbox;const tees=(a,b)=>teeOf(a,a.start)===b||teeOf(a,a.end)===b;
 for(let i=0;i<walls.length;i++)for(let k=i+1;k<walls.length;k++){const a=walls[i],b=walls[k];
  if(same(a.start,b.start)||same(a.start,b.end)||same(a.end,b.start)||same(a.end,b.end)||tees(a,b)||tees(b,a))continue;
  const A=bb(a),B=bb(b);const ov=Math.max(0,Math.min(A[2],B[2])-Math.max(A[0],B[0]))*Math.max(0,Math.min(A[3],B[3])-Math.max(A[1],B[1]));
  if(ov>1e-4)out.push({w:a.id,t:'Wände '+a.id+' und '+b.id+' überlappen'})}
 return out}
const isInt=w=>(ASM[w.assembly]||{}).category==='interior_wall';
// end points: c = connections; free = interior wall end released without a connection (free_ends)
function openEnds(){const res=[];walls.forEach(w=>[['start',w.start],['end',w.end]].forEach(([k,p])=>{const c=walls.filter(o=>o!==w&&(same(o.start,p)||same(o.end,p))).length+(teeOf(w,p)?1:0);res.push({w,k,p,c,free:!c&&isInt(w)&&(w.free||[]).includes(k)})}));return res}
function setFree(w,k,on){w.free=(w.free||[]).filter(x=>x!==k);if(on)w.free.push(k);mark(w.id,w.id+(on?' Ende ohne Anschluss erlaubt':' Freigabe aufgehoben'))}
// outline (reference points) for automatic outside side
function ring(){const ext=walls.filter(w=>(ASM[w.assembly]||{}).category!=='interior_wall');if(!ext.length)return null;
 const used=new Set([ext[0].id]);const pts=[ext[0].start];let cur=ext[0].end;const first=ext[0].start;
 for(let n=0;n<ext.length;n++){if(same(cur,first))return pts;pts.push(cur);const nx=ext.find(o=>!used.has(o.id)&&(same(o.start,cur)||same(o.end,cur)));if(!nx)return null;
  used.add(nx.id);cur=same(nx.start,cur)?nx.end:nx.start}return same(cur,first)?pts:null}
function inside(p,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c}
function autoOutside(w,poly){poly=poly||ring();if(!poly)return w.outside||'left';const d=dir(w),m=[(w.start[0]+w.end[0])/2,(w.start[1]+w.end[1])/2];
 const left=[m[0]+d[1]*0.05,m[1]-d[0]*0.05];return inside(left,poly)?'right':'left'}
function newId(prefix,list){const ids=new Set(list.map(x=>x.id).concat([...deleted]));let n=1;while(ids.has(prefix+n))n++;return prefix+n}
// drawing
function el(tag,a,parent){const e=sv(tag,a);(parent||svg).appendChild(e);return e}
function render(){frame();svg.textContent='';const pr=problems();const bad=new Set(pr.filter(p=>!p.soft).map(p=>p.w));const badOp=new Set(pr.filter(p=>p.o).map(p=>p.o));
 rooms.forEach(r=>{const pl=r.polygon;const g=el('g',{});const isSel=pick&&pick.type==='room'&&pick.id===r.id;
  el('polygon',{points:pl.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:isSel?'#E3EEFB':'#F7F3EA',stroke:errHi.has(r.id)?'#D81B60':isSel?'#1C69D4':'#C9C2B0','stroke-width':errHi.has(r.id)?4:isSel?2:1,'data-room':r.id,style:'cursor:pointer'},g);
  const c=pcenter(pl);const t=el('text',{class:'roomlabel',x:X(c[0]),y:Y(c[1]),'text-anchor':'middle','font-size':20,fill:'#555','pointer-events':'none'},g);t.textContent=r.name+' ('+num(parea(pl).toFixed(2))+' m²)';
  if(isSel){pl.forEach((a,i)=>{const b=pl[(i+1)%pl.length];const hz=hEdge(a,b);
    el('rect',{x:X((a[0]+b[0])/2)-5,y:Y((a[1]+b[1])/2)-5,width:10,height:10,fill:'#1C69D4','data-redge':i,style:'cursor:'+(hz?'ns-resize':'ew-resize')},g).appendChild(sv('title',{})).textContent='Kante ziehen – Doppelklick teilt die Kante';
    el('circle',{cx:X(a[0]),cy:Y(a[1]),r:6,fill:'#fff',stroke:'#1C69D4','stroke-width':2,'data-rvert':i,style:'cursor:move'},g)})}});
 walls.forEach(w=>{const isSel=pick&&pick.type==='wall'&&pick.id===w.id;const b=band(w);
  el('polygon',{points:b.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:(ASM[w.assembly]||{}).color||'#C9A88A',stroke:errHi.has(w.id)?'#D81B60':bad.has(w.id)?'#C62828':(isSel?'#1C69D4':'#000'),'stroke-width':errHi.has(w.id)?5:isSel||bad.has(w.id)?2.5:1,'data-wall':w.id,style:'cursor:'+(horiz(w)?'ns-resize':'ew-resize')});
  const d=dir(w);opsAbs(w).forEach(o=>{const n=nIn(w),T=thick(w),s=shiftOf(w);const P=(u,t)=>[w.start[0]+d[0]*u+n[0]*(t-s),w.start[1]+d[1]*u+n[1]*(t-s)];
   const q=[P(o.u0,0),P(o.u1,0),P(o.u1,T),P(o.u0,T)];el('polygon',{points:q.map(p=>X(p[0])+','+Y(p[1])).join(' '),fill:errHi.has(o.id)||badOp.has(o.id)?'#FFCDD2':'#fff',stroke:errHi.has(o.id)?'#D81B60':badOp.has(o.id)?'#C62828':'#1C69D4','stroke-width':errHi.has(o.id)?4:1,'pointer-events':'none'});
   const c=P((o.u0+o.u1)/2,T+0.25);const t=el('text',{x:X(c[0]),y:Y(c[1]),'text-anchor':'middle','font-size':14,fill:'#1C69D4','pointer-events':'none'});t.textContent=o.id});
  el('line',{x1:X(w.start[0]),y1:Y(w.start[1]),x2:X(w.end[0]),y2:Y(w.end[1]),stroke:'#333','stroke-dasharray':'4 3','stroke-width':0.8,'pointer-events':'none'});
  const n=nIn(w),m=[(w.start[0]+w.end[0])/2,(w.start[1]+w.end[1])/2];el('line',{x1:X(m[0]),y1:Y(m[1]),x2:X(m[0]-n[0]*0.4),y2:Y(m[1]-n[1]*0.4),stroke:'#2E7D32','stroke-width':2,'pointer-events':'none','marker-end':''});
  const lt=el('text',{class:'walllabel',x:X(m[0]-n[0]*0.6),y:Y(m[1]-n[1]*0.6)+4,'text-anchor':'middle','font-size':16,fill:isSel?'#1C69D4':'#333','pointer-events':'none'});lt.textContent=(w.name?w.name+' · ':'')+w.id+' · '+num(Math.round(len(w)*100))+' cm';
  if(isSel){[['start',w.start],['end',w.end]].forEach(([k,p])=>el('circle',{cx:X(p[0]),cy:Y(p[1]),r:7,fill:'#1C69D4',stroke:'#fff','stroke-width':2,'data-end':k,style:'cursor:'+(horiz(w)?'ew-resize':'ns-resize')}))}});
 openEnds().forEach(({w,k,p,c,free})=>{const hit=!c&&isInt(w)&&!(pick&&pick.type==='wall'&&pick.id===w.id);
  el('circle',{cx:X(p[0]),cy:Y(p[1]),r:hit?5:3.5,fill:c?'#2E7D32':free?'#42A5F5':'#F57C00','pointer-events':hit?'all':'none','data-fend':hit?w.id+'|'+k:'',style:hit?'cursor:pointer':''})});
 if(dragSt&&dragSt.guide){const g=dragSt.guide;el('line',{x1:X(g[0][0]),y1:Y(g[0][1]),x2:X(g[1][0]),y2:Y(g[1][1]),stroke:'#1C69D4','stroke-width':1,'stroke-dasharray':'2 2','pointer-events':'none'})}
 if(dragSt&&dragSt.kind==='draw'&&dragSt.cur){const a=dragSt.a,b=dragSt.cur;
  if(mode==='wall')el('line',{x1:X(a[0]),y1:Y(a[1]),x2:X(b[0]),y2:Y(b[1]),stroke:'#1C69D4','stroke-width':4});
  else el('rect',{x:X(Math.min(a[0],b[0])),y:Y(Math.min(a[1],b[1])),width:Math.abs(b[0]-a[0])*S,height:Math.abs(b[1]-a[1])*S,fill:'rgba(28,105,212,.15)',stroke:'#1C69D4'})}
 drawPanel(pr)}
// snapping
function snapEnd(p,self){let best=null,bd=SNAP;walls.forEach(w=>{if(w===self)return;[w.start,w.end].forEach(q=>{const d=Math.hypot(q[0]-p[0],q[1]-p[1]);if(d<bd){bd=d;best=q}})});return best}
function snapLine(val,isY,self){let best=null,bd=SNAP;walls.forEach(w=>{if(w===self)return;if(isY?horiz(w):!horiz(w)){const v=isY?w.start[1]:w.start[0];const d=Math.abs(v-val);if(d<bd){bd=d;best=v}}});return best}
// end point of a wall: reference line and both faces of crossing walls
function endLineSnap(val,isY,self){let best=null,bd=SNAP;walls.forEach(w=>{if(w===self||(isY?!horiz(w):horiz(w)))return;const b=band(w);const c=isY?[w.start[1],b[0][1],b[2][1]]:[w.start[0],b[0][0],b[2][0]];c.forEach(v=>{const d=Math.abs(v-val);if(d<bd){bd=d;best=v}})});return best}
function roomSnap(val,isY){let best=null,bd=SNAP;walls.forEach(w=>{const b=band(w);const c=isY?(horiz(w)?[b[0][1],b[2][1]]:[]):(!horiz(w)?[b[0][0],b[2][0]]:[]);c.forEach(v=>{const d=Math.abs(v-val);if(d<bd){bd=d;best=v}})});return best}
// interaction
function cap(ev){try{svg.setPointerCapture(ev.pointerId)}catch(e){}}
svg.addEventListener('pointerdown',ev=>{const t=ev.target;const p=toWorld(ev);
 if(mode==='wall'||mode==='room'){const s=snapEnd(p,null)||[grid(p[0],ev),grid(p[1],ev)];dragSt={kind:'draw',a:s,cur:s};cap(ev);return}
 if(t.dataset.fend){const [id,k]=t.dataset.fend.split('|');const w=walls.find(x=>x.id===id);const on=(w.free||[]).includes(k);
  if(confirm(on?'Freigabe für Ende von '+id+' aufheben?':'Innenwand '+id+': Ende ohne Anschluss erlauben?')){setFree(w,k,!on);render()}return}
 if(t.dataset.end&&pick&&pick.type==='wall'){const w=walls.find(x=>x.id===pick.id);dragSt={kind:'end',w,which:t.dataset.end,orig:clone(w)};cap(ev);return}
 if(t.dataset.redge&&pick&&pick.type==='room'){const r=rooms.find(x=>x.id===pick.id);dragSt={kind:'redge',r,i:+t.dataset.redge,orig:clone(r.polygon)};cap(ev);return}
 if(t.dataset.rvert&&pick&&pick.type==='room'){const r=rooms.find(x=>x.id===pick.id);dragSt={kind:'rvert',r,i:+t.dataset.rvert,orig:clone(r.polygon)};cap(ev);return}
 if(t.dataset.wall){const w=walls.find(x=>x.id===t.dataset.wall);pick={type:'wall',id:w.id};
  const att=[];if(pull)walls.forEach(o=>{if(o===w||horiz(o)===horiz(w))return;['start','end'].forEach(k=>{if(same(o[k],w.start)||same(o[k],w.end))att.push({o,k,orig:o[k].slice()})})});
  dragSt={kind:'move',w,p0:p,orig:clone(w),att,moved:false};cap(ev);render();return}
 if(t.dataset.room){pick={type:'room',id:t.dataset.room};render();return}
 pick=null;render()});
svg.addEventListener('pointermove',ev=>{if(!dragSt)return;const p=toWorld(ev);dragSt.guide=null;
 if(dragSt.kind==='draw'){let b=snapEnd(p,null)||[grid(p[0],ev),grid(p[1],ev)];if(mode==='wall'){const a=dragSt.a;if(Math.abs(b[0]-a[0])>=Math.abs(b[1]-a[1]))b=[b[0],a[1]];else b=[a[0],b[1]]}dragSt.cur=b;render();return}
 if(dragSt.kind==='move'){const w=dragSt.w,o=dragSt.orig;const hz=horiz(o);let v=(hz?o.start[1]:o.start[0])+(hz?p[1]-dragSt.p0[1]:p[0]-dragSt.p0[0]);v=grid(v,ev);
  const sn=snapLine(v,hz,w);if(sn!==null){v=sn;dragSt.guide=hz?[[bx0,v],[bx1,v]]:[[v,by0],[v,by1]]}
  if(hz){w.start=[o.start[0],r4(v)];w.end=[o.end[0],r4(v)]}else{w.start=[r4(v),o.start[1]];w.end=[r4(v),o.end[1]]}
  dragSt.att.forEach(a=>{a.o[a.k]=hz?[a.orig[0],r4(v)]:[r4(v),a.orig[1]]});dragSt.moved=true;render();return}
 if(dragSt.kind==='end'){const w=dragSt.w,o=dragSt.orig,k=dragSt.which;const hz=horiz(o);let q=o[k].slice();
  if(hz)q[0]=grid(p[0],ev);else q[1]=grid(p[1],ev);const se=snapEnd(q,w);if(se&&(hz?Math.abs(se[1]-q[1])<0.001:Math.abs(se[0]-q[0])<0.001))q=se.slice();
  else{const sl=endLineSnap(hz?q[0]:q[1],!hz,w);if(sl!==null){if(hz)q[0]=sl;else q[1]=sl;dragSt.guide=hz?[[sl,by0],[sl,by1]]:[[bx0,sl],[bx1,sl]]}}
  w[k]=[r4(q[0]),r4(q[1])];dragSt.moved=true;render();return}
 if(dragSt.kind==='redge'){const r=dragSt.r,o=dragSt.orig,i=dragSt.i,j=(i+1)%o.length;const hz=hEdge(o[i],o[j]);let v=grid(hz?p[1]:p[0],ev);const sn=roomSnap(v,hz);if(sn!==null)v=sn;
  const pl=clone(o);pl[i][hz?1:0]=r4(v);pl[j][hz?1:0]=r4(v);r.polygon=pl;dragSt.moved=true;render();return}
 if(dragSt.kind==='rvert'){const r=dragSt.r,o=dragSt.orig,i=dragSt.i,n=o.length,pv=(i+n-1)%n,nx=(i+1)%n;
  let x=grid(p[0],ev),y=grid(p[1],ev);const sx=roomSnap(x,false),sy=roomSnap(y,true);if(sx!==null)x=sx;if(sy!==null)y=sy;
  // the neighbours follow so every edge stays axis-parallel
  const pl=clone(o);pl[i]=[r4(x),r4(y)];[pv,nx].forEach(k=>{if(hEdge(o[k],o[i]))pl[k][1]=r4(y);else pl[k][0]=r4(x)});r.polygon=pl;dragSt.moved=true;render()}});
svg.addEventListener('dblclick',ev=>{const t=ev.target;if(!(t.dataset.redge&&pick&&pick.type==='room'))return;const r=rooms.find(x=>x.id===pick.id);const i=+t.dataset.redge,pl=r.polygon,a=pl[i],b=pl[(i+1)%pl.length];
 const m=[r4((a[0]+b[0])/2),r4((a[1]+b[1])/2)];pl.splice(i+1,0,m.slice(),m.slice());mark('room:'+r.id,'Raum '+r.id+' Kante geteilt');render()});
svg.addEventListener('pointerup',()=>{if(!dragSt)return;const d=dragSt;dragSt=null;
 if(d.kind==='draw'){const a=d.a,b=d.cur;if(mode==='wall'&&Math.hypot(b[0]-a[0],b[1]-a[1])>=0.05){const tpl=walls.find(w=>pick&&w.id===pick.id)||walls[0];
   const w={id:newId('w-',walls),name:'Wand',assembly:tpl?tpl.assembly:Object.keys(ASM)[0],start:a.slice(),end:b.slice(),reference:'outside_face',outside:'left',shape:{kind:'rect'},ops:[]};
   w.outside=autoOutside(w);walls.push(w);pick={type:'wall',id:w.id};mark(w.id,w.id+' neu')}
  if(mode==='room'&&Math.abs(b[0]-a[0])>=0.1&&Math.abs(b[1]-a[1])>=0.1){const x0=Math.min(a[0],b[0]),y0=Math.min(a[1],b[1]),x1=Math.max(a[0],b[0]),y1=Math.max(a[1],b[1]);
   const r={id:newId('room-',rooms),name:'Raum',polygon:[[x0,y0],[x1,y0],[x1,y1],[x0,y1]].map(p=>[r4(p[0]),r4(p[1])])};
   rooms.push(r);pick={type:'room',id:r.id};mark('room:'+r.id,'Raum '+r.id+' neu')}
  mode=null;render();return}
 if(d.moved){if(d.kind==='redge'||d.kind==='rvert'){const pl=pclean(d.r.polygon);if(pl.length>=4)d.r.polygon=pl;mark('room:'+d.r.id,'Raum '+d.r.id+' geändert')}else{mark(d.w.id,d.w.id+(d.kind==='move'?' verschoben':' Länge geändert'));(d.att||[]).forEach(a=>mark(a.o.id,a.o.id+' Ecke mitgezogen'))}}
 render()});
document.addEventListener('keydown',ev=>{if(area.style.display==='none'||!pick||pick.type!=='wall'||['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName))return;
 const w=walls.find(x=>x.id===pick.id);if(!w)return;const st=ev.shiftKey?0.1:0.01;const hz=horiz(w);let dv=0;
 if(hz&&ev.key==='ArrowUp')dv=-st;else if(hz&&ev.key==='ArrowDown')dv=st;else if(!hz&&ev.key==='ArrowLeft')dv=-st;else if(!hz&&ev.key==='ArrowRight')dv=st;else return;ev.preventDefault();
 const att=[];if(pull)walls.forEach(o=>{if(o===w||horiz(o)===hz)return;['start','end'].forEach(k=>{if(same(o[k],w.start)||same(o[k],w.end))att.push({o,k})})});
 const i=hz?1:0;w.start[i]=r4(w.start[i]+dv);w.end[i]=r4(w.end[i]+dv);att.forEach(a=>{a.o[a.k][i]=r4(a.o[a.k][i]+dv);mark(a.o.id,a.o.id+' Ecke mitgezogen')});mark(w.id,w.id+' verschoben');render()});
// operations
function rotate(w,sign){const L=len(w),d=dir(w);const nd=sign>0?[-d[1],d[0]]:[d[1],-d[0]];w.end=[r4(w.start[0]+nd[0]*L),r4(w.start[1]+nd[1]*L)];mark(w.id,w.id+' gedreht')}
function split(w,a){const L=len(w);if(!(a>0.01&&a<L-0.01)){alert('Teilungspunkt muss innerhalb der Wand liegen');return null}const d=dir(w);const P=[r4(w.start[0]+d[0]*a),r4(w.start[1]+d[1]*a)];
 const w2=Object.assign(clone(w),{id:newId('w-',walls),name:(w.name||'Wand')+' 2',start:P,end:w.end.slice(),ops:[]});
 const keep=[],move=[];opsAbs(w).forEach((o,i)=>{(o.u0>=a-1e-6?move:keep).push(w.ops[i])});w.ops=keep;w.end=P;
 move.forEach(o=>{w2.ops.push(Object.assign({},o,{taken:true,offset:o.offset-a}));(takes[w2.id]=takes[w2.id]||[]).push(o.id)});
 walls.splice(walls.indexOf(w)+1,0,w2);mark(w.id,w.id+' geteilt');mark(w2.id,w2.id+' neu (Teil von '+w.id+')');return w2}
function bay(w,a,b,t,outward){const L=len(w);if(!(a>0.01&&a+b<L-0.01&&b>0.05&&t>0.01)){alert('Versprung passt nicht in die Wand');return}
 const n=nIn(w);const off=outward?[-n[0]*t,-n[1]*t]:[n[0]*t,n[1]*t];const poly0=ring();
 const mid=split(w,a);if(!mid)return;const right=split(mid,b);if(!right)return;
 const p1=mid.start.slice(),p2=mid.end.slice();mid.start=[r4(p1[0]+off[0]),r4(p1[1]+off[1])];mid.end=[r4(p2[0]+off[0]),r4(p2[1]+off[1])];
 const c1={id:newId('w-',walls),name:'Versprung 1',assembly:w.assembly,start:p1,end:mid.start.slice(),reference:w.reference,outside:'left',shape:clone(w.shape||{kind:'rect'}),ops:[]};walls.push(c1);
 const c2={id:newId('w-',walls),name:'Versprung 2',assembly:w.assembly,start:mid.end.slice(),end:p2,reference:w.reference,outside:'left',shape:clone(w.shape||{kind:'rect'}),ops:[]};walls.push(c2);
 const poly=ring();[c1,c2].forEach(c=>{c.outside=autoOutside(c,poly);mark(c.id,c.id+' neu (Versprung)')});mark(mid.id,mid.id+' versetzt (Versprung)')}
// panel
function numIn(v,cb){const i=inp(v,{type:'number',step:'1',style:'width:80px'});i.onchange=()=>{if(i.value!=='')cb(+i.value)};return i}
function drawPanel(pr){panel.textContent='';
 const ht=numIn(Math.round(height*100),v=>{height=v/100;mark('height','Geschosshöhe '+v+' cm');render()});
 const pc=h('input',{type:'checkbox'});pc.checked=pull;pc.onchange=()=>pull=pc.checked;
 panel.append(h('div',{class:'wpanel',style:'margin-top:0'},field('Geschosshöhe cm',ht),field('Ecken mitziehen',pc),
  h('div',{style:'display:flex;gap:.4rem;flex-wrap:wrap'},h('button',{class:mode==='wall'?'btn':'btn2',text:'+ Wand',onclick:()=>{mode=mode==='wall'?null:'wall';render()}}),
   h('button',{class:mode==='room'?'btn':'btn2',text:'+ Raum',onclick:()=>{mode=mode==='room'?null:'room';render()}})),
  mode?h('p',{class:'note',text:mode==='wall'?'Auf dem Plan ziehen: neue Wand (achsparallel).':'Auf dem Plan ein Rechteck ziehen: neuer Raum (danach Ecken und Kanten ziehen).'}):null));
 if(pick&&pick.type==='wall'){const w=walls.find(x=>x.id===pick.id);if(w){const box=h('div',{class:'wpanel'});const hd=h('h3',{text:'Wand '+(w.name||w.id),style:'margin-top:0'});box.append(hd,h('p',{class:'note',text:w.id,style:'margin-top:-.6rem'}));
   const nm=inp(w.name||'');nm.oninput=()=>{w.name=nm.value;hd.textContent='Wand '+(w.name||w.id);mark(w.id,w.id+' geändert')};
   const as=sel(Object.keys(ASM).map(r=>[r,ASM[r].name]),w.assembly);as.onchange=()=>{w.assembly=as.value;mark(w.id,w.id+' Aufbau');render()};
   const sx=numIn(Math.round(w.start[0]*100),v=>{w.start[0]=v/100;mark(w.id,w.id+' geändert');render()}),sy=numIn(Math.round(w.start[1]*100),v=>{w.start[1]=v/100;mark(w.id,w.id+' geändert');render()});
   const ex=numIn(Math.round(w.end[0]*100),v=>{w.end[0]=v/100;mark(w.id,w.id+' geändert');render()}),ey=numIn(Math.round(w.end[1]*100),v=>{w.end[1]=v/100;mark(w.id,w.id+' geändert');render()});
   const ln=numIn(Math.round(len(w)*100),v=>{const d=dir(w);w.end=[r4(w.start[0]+d[0]*v/100),r4(w.start[1]+d[1]*v/100)];mark(w.id,w.id+' Länge');render()});
   const spl=numIn(Math.round(len(w)*50),()=>{});const ba=numIn(Math.round(len(w)*40),()=>{}),bw=numIn(Math.round(len(w)*20),()=>{}),bt=numIn(100,()=>{});
   const bo=sel([['out','nach außen'],['in','nach innen']],'out');
   box.append(field('Name',nm),field('Aufbau',as),field('Start x / y cm',h('span',{style:'display:flex;gap:4px'},sx,sy)),field('Ende x / y cm',h('span',{style:'display:flex;gap:4px'},ex,ey)),field('Länge cm',ln),
    field('Außenseite',h('span',{},(w.outside==='right'?'rechts':'links')+' ',h('button',{class:'btn2',text:'tauschen',onclick:()=>{w.outside=w.outside==='right'?'left':'right';mark(w.id,w.id+' Außenseite');render()}}))),
    h('div',{style:'display:flex;gap:.4rem;flex-wrap:wrap;margin:.4rem 0'},h('button',{class:'btn2',text:'Drehen 90° links',onclick:()=>{rotate(w,-1);render()}}),h('button',{class:'btn2',text:'Drehen 90° rechts',onclick:()=>{rotate(w,1);render()}})),
    h('h4',{text:'Teilen'}),field('ab Start cm',spl),h('button',{class:'btn2',text:'Teilen',onclick:()=>{if(split(w,+spl.value/100))render()}}),
    h('h4',{text:'Versprung'}),field('ab Start cm',ba),field('Breite cm',bw),field('Tiefe cm',bt),field('Richtung',bo),
    h('button',{class:'btn2',text:'Versprung erzeugen',onclick:()=>{bay(w,+ba.value/100,+bw.value/100,+bt.value/100,bo.value==='out');render()}}),
    h('div',{style:'margin-top:.8rem'},h('button',{class:'btn2',text:'Wand löschen',onclick:()=>{const ops=w.ops.map(o=>o.id);
     if(!confirm('Wand '+w.id+' löschen?'+(ops.length?' Mit ihr werden die Öffnungen '+ops.join(', ')+' gelöscht.':'')))return;walls.splice(walls.indexOf(w),1);
     if(savedOf(w.id))deleted.add(w.id);changes.delete(w.id);mark('del:'+w.id,w.id+' gelöscht');pick=null;render()}})));panel.appendChild(box)}}
 if(pick&&pick.type==='room'){const r=rooms.find(x=>x.id===pick.id);if(r){const box=h('div',{class:'wpanel'});box.appendChild(h('h3',{text:'Raum '+r.id,style:'margin-top:0'}));
   const nm=inp(r.name);nm.onchange=()=>{r.name=nm.value;mark('room:'+r.id,'Raum '+r.id+' geändert');render()};
   const xs=r.polygon.map(p=>p[0]),ys=r.polygon.map(p=>p[1]);
   box.append(field('Name',nm),field('Fläche',h('span',{text:num(parea(r.polygon).toFixed(2))+' m² · '+r.polygon.length+' Ecken'})),
    field('Umriss cm',h('span',{text:num(Math.round((Math.max(...xs)-Math.min(...xs))*100))+' × '+num(Math.round((Math.max(...ys)-Math.min(...ys))*100))})),
    h('p',{class:'note',text:'Ecken (Kreise) und Kanten (Quadrate) ziehen; sie rasten an den Wandinnenseiten ein. Doppelklick auf eine Kante teilt sie – die zweite Hälfte ziehen ergibt einen Versprung. Gerade gezogene Versprünge verschwinden wieder. Beläge, Nummer und Nutzung: Seite Räume.'}),
    h('a',{href:'/raeume?storey='+encodeURIComponent(ST.id)+'#'+encodeURIComponent(r.id),text:'Raum auf der Seite Räume öffnen'}),h('div',{style:'height:.5rem'}),
    h('button',{class:'btn2',text:'Raum löschen',onclick:()=>{if(!confirm('Raum '+r.id+' löschen?'))return;rooms.splice(rooms.indexOf(r),1);if(saved.rooms.some(x=>x.id===r.id))roomDel.add(r.id);mark('room:'+r.id,'Raum '+r.id+' gelöscht');pick=null;render()}}));
   panel.appendChild(box)}}
 const pb=h('div',{class:'wpanel'});const hard=pr.filter(p=>!p.soft),soft=pr.filter(p=>p.soft);const oe=openEnds();const ends=oe.filter(e=>!e.c&&!e.free).length,frees=oe.filter(e=>e.free).length;
 if(hard.length)pb.appendChild(h('div',{style:'color:#C62828'},hard.map(p=>h('div',{text:p.t}))));
 if(soft.length)pb.appendChild(h('div',{style:'color:#C62828'},soft.map(p=>h('div',{text:p.t}))));
 if(ends)pb.appendChild(h('div',{style:'color:#F57C00',text:ends+' offene Wandenden (orange)'}));
 if(frees)pb.appendChild(h('div',{style:'color:#1E88E5',text:frees+' freie Innenwandenden (blau)'}));
 pb.appendChild(h('h4',{text:'Änderungen ('+changes.size+')'}));pb.appendChild(h('ul',{},[...changes.values()].map(t=>h('li',{text:t}))));
 const err=h('div',{id:'planerr',style:'color:#C62828'});srvErr.forEach((t,i)=>{const ids=errIds(t);err.appendChild(h('div',ids.size?{text:t,title:'Klicken: betroffene Elemente im Plan markieren',onclick:()=>showErr(i),
  style:'cursor:pointer;text-decoration:underline dotted;padding:2px 4px'+(errAt===i?';background:#FCE4EC;outline:1px solid #D81B60':'')}:{text:t}))});
 const sbtn=h('button',{class:'btn',text:'Speichern',onclick:save});sbtn.disabled=!changes.size||!!hard.length;
 pb.append(err,h('div',{style:'display:flex;gap:.5rem'},sbtn,h('button',{class:'btn2',text:'Verwerfen',onclick:()=>{if(changes.size&&!confirm('Änderungen verwerfen?'))return;load();pick=null;render()}}),
  h('button',{class:'btn2',text:'Bearbeiten beenden',onclick:()=>{if(changes.size&&!confirm('Änderungen verwerfen?'))return;location.hash='';location.reload()}})));
 panel.appendChild(pb)}
function save(){const oe=openEnds();oe.forEach(e=>{if(e.c&&(e.w.free||[]).includes(e.k))e.w.free=e.w.free.filter(x=>x!==e.k)});
 oe.filter(e=>!e.c&&isInt(e.w)&&!e.free).forEach(e=>{if(confirm('Innenwand '+e.w.id+': Ende ohne Anschluss erlauben?'))setFree(e.w,e.k,true)});
 const fe=w=>isInt(w)?(w.free||[]).slice().sort():[];const up=[];walls.forEach(w=>{const sv=savedOf(w.id);const plain={id:w.id,name:w.name,assembly:w.assembly,start:w.start,end:w.end,reference:w.reference,shape:clone(w.shape||{kind:'rect'})};
  if((ASM[w.assembly]||{}).category!=='interior_wall')plain.outside=w.outside;if(takes[w.id])plain.take_openings=takes[w.id];if(w.wh)plain.height=w.wh;if(fe(w).length)plain.free_ends=fe(w);
  const svPlain=sv?JSON.stringify({id:sv.id,name:sv.name,assembly:sv.assembly,start:sv.start,end:sv.end,reference:sv.reference,outside:sv.outside,free:fe(sv)}):null;
  if(!sv||takes[w.id]||svPlain!==JSON.stringify({id:w.id,name:w.name,assembly:w.assembly,start:w.start,end:w.end,reference:w.reference,outside:w.outside,free:fe(w)}))up.push(plain)});
 const rup=rooms.filter(r=>{const s=saved.rooms.find(x=>x.id===r.id);return !s||JSON.stringify(s)!==JSON.stringify(r)}).map(r=>({id:r.id,name:r.name,polygon:pclean(r.polygon)}));
 const body={storey:ST.id,upsert:up,delete:[...deleted],rooms:{upsert:rup,delete:[...roomDel]}};if(height!==saved.height)body.height=height;
 post('/api/walls/save',body).then(({ok,j})=>{if(!ok){srvErr=(j.errors||[j.error]).filter(Boolean);errAt=-1;errHi=new Set();render();return}
  const c=(j.opening_conflicts||[]).map(x=>x.opening).join(', ');sessionStorage.setItem('weingaerten.toast','Gespeichert'+(c?' – Öffnungen außerhalb: '+c:''));
  location.hash=pick&&pick.type==='wall'?pick.id:'edit';location.reload()})}
function startEdit(){view.style.display='none';area.style.display='block';btn.style.display='none';PlanZoom.showPanel();
 const hsh=decodeURIComponent(location.hash.slice(1));if(hsh&&walls.some(w=>w.id===hsh))pick={type:'wall',id:hsh};render()}
btn.onclick=()=>{location.hash='edit';startEdit()};
[['planroomnames','noroomnames','weingaerten.grundriss.raumnamen'],['planwallnames','nowallnames','weingaerten.grundriss.wandnamen']].forEach(([id,cls,key])=>{
 const cb=document.getElementById(id);if(!cb)return;const box=document.getElementById('planbox');
 const apply=()=>{box.classList.toggle(cls,!cb.checked);localStorage.setItem(key,cb.checked?'1':'0')};
 cb.checked=localStorage.getItem(key)!=='0';cb.onchange=apply;apply()});
if(location.hash&&location.hash!=='#')startEdit();
const tm=sessionStorage.getItem('weingaerten.toast');if(tm){sessionStorage.removeItem('weingaerten.toast');toast(tm)}
window.addEventListener('beforeunload',ev=>{if(changes.size&&area.style.display!=='none'){ev.preventDefault();ev.returnValue=''}});
