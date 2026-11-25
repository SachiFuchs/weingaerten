// Installation (Einbauteile) on the page /waende: pipes, fittings, boxes and valves on the shown wall face.
// Uses the state of wand.js (D, H, ST, view, wall(), faceRange, mirrorOf, sx, sz, S, PADL, PADT, svg, draw, reload).
// Geometry = PartFrame of the core (same formulas): x, y in the wall plane, w out of the face; depth > 0 = in front.
window.InstallUI=(()=>{
 const bar=document.getElementById('instbar'),pal=document.getElementById('instpal'),panel=document.getElementById('instpanel'),
  sec=document.getElementById('instsec'),tab=document.getElementById('insttable'),menu=h('div',{class:'instmenu',style:'display:none'});
 document.body.appendChild(menu);
 const PORT={open:'#E53935',connected:'#2E7D32',open_ok:'#1C69D4',transfer:'#1C69D4',inactive:'#B0B0B0'};
 const STATUS_DE={open:'offen',connected:'verbunden',open_ok:'bewusst offen',transfer:'Übergabe',inactive:'inaktiv (Klemmen voll)'};
 const TRANSFER_DE={beside:'→ Nachbarraum',above:'↑ Geschoss oben',below:'↓ Geschoss unten'};
 // snap radius ("Magnet"): 0 = off .. 30 cm, stored per browser
 const MKEY='weingaerten.waende.magnet';let SNAP=+(localStorage.getItem(MKEY)??0.05);const SEAT=0.002,OPP=-Math.cos(Math.PI/180);
 const inst=()=>H.installation||{catalog:[],parts:[]};
 const cat=r=>(inst().catalog||[]).find(c=>c.ref===r);
 let on=false,buf=null,dels=new Set(),cur=null,carry=null,drag=null,place='in';
 const urlPart=new URLSearchParams(location.search).get('part');
 // --- geometry (PartFrame) -------------------------------------------------------------------------------
 const faceOf=w=>w.category==='exterior_wall'?(view==='outside'?'outside':'inside'):(view==='outside'?'left':'right');
 const other=(w,f)=>({outside:'inside',inside:'outside',left:'right',right:'left'})[f];
 const unit2=w=>{const dx=w.end[0]-w.start[0],dy=w.end[1]-w.start[1],l=Math.hypot(dx,dy);return [dx/l,dy/l]};
 function faceT(w,f){const s=w.start,n=w.normal_in,ts=w.footprint.map(p=>(p[0]-s[0])*n[0]+(p[1]-s[1])*n[1]);
  return ['outside','left'].includes(f)?[Math.min(...ts),-1]:[Math.max(...ts),1]}
 function rotated(v,r){let [x,y,w]=v;if(r.flip)x=-x;const R=Math.PI/180,p=(r.plane||0)*R,t=(r.tilt||0)*R,q=(r.turn||0)*R;
  [x,y]=[x*Math.cos(p)-y*Math.sin(p),x*Math.sin(p)+y*Math.cos(p)];[y,w]=[y*Math.cos(t)-w*Math.sin(t),y*Math.sin(t)+w*Math.cos(t)];
  [x,w]=[x*Math.cos(q)+w*Math.sin(q),-x*Math.sin(q)+w*Math.cos(q)];return [x,y,w]}
 function frame(w,p){const d=unit2(w),n=w.normal_in,[t,s]=faceT(w,p.host.face),eu=[d[0],d[1],0],ez=[0,0,1],eo=[s*n[0],s*n[1],0];
  const o=[w.start[0]+d[0]*p.u+n[0]*t+eo[0]*p.depth,w.start[1]+d[1]*p.u+n[1]*t+eo[1]*p.depth,w.z0+p.z];
  const ax=[[1,0,0],[0,1,0],[0,0,1]].map(l=>{const r=rotated(l,p.rot||{});return [0,1,2].map(i=>r[0]*eu[i]+r[1]*ez[i]+r[2]*eo[i])});
  return {o,x:ax[0],y:ax[1],w:ax[2],eu,eo,pt:l=>[0,1,2].map(i=>o[i]+l[0]*ax[0][i]+l[1]*ax[1][i]+l[2]*ax[2][i]),
   vec:l=>[0,1,2].map(i=>l[0]*ax[0][i]+l[1]*ax[1][i]+l[2]*ax[2][i])}}
 // computed part like the server output (origin, axes, ports, legs) from the source fields
 // a bent cable: `path` = local points after the origin (port a), the last one = port b; length = sum of the pieces
const unit3=v=>{const n=Math.hypot(...v);return n>1e-9?v.map(x=>x/n):[1,0,0]};
const cablePath=(c,p)=>c.shape==='cable'&&p.path&&p.path.length?p.path:null;
function geo(w,p){const c=cat(p.component);if(!c)return null;const f=frame(w,p);const path=cablePath(c,p);const pts=path?[[0,0,0]].concat(path):null;
  const len=path?pts.slice(1).reduce((s,q,i)=>s+dist(q,pts[i]),0):c.stretch?(p.length||c.stretch.default_length):null;
  const ports=c.ports.map(q=>{let pos=q.pos.slice(),dir=q.dir;if(q.at_length&&path){pos=path[path.length-1].slice();dir=unit3(pos.map((v,i)=>v-pts[pts.length-2][i]))}
   else if(q.at_length)pos[0]+=len;if(path&&q.id==='a')dir=unit3(path[0]).map(v=>-v);
   const cores=c.shape==='pipe'&&p.cable&&q.line==='conduit'&&cableCores(p.cable)?[cableCores(p.cable)]:q.cores||null;
   const cb=c.shape==='pipe'&&p.cable?cableOf(p.cable):null;
   return {id:q.id,position:f.pt(pos),direction:f.vec(dir),line:q.line,dn:q.dn,gender:q.gender,cores,
    cable_type:cb?cb.cable_type:q.cable_type,section:cb?cb.section:q.section,cable_types:q.cable_types,cross_section:q.cross_section,label:q.label,angle:q.angle,
    status:'open',connected_to:null,transfer:null}});
  const legs=path?pts.slice(1).map((q,i)=>[f.pt(pts[i]),f.pt(q)]):['pipe','cable'].includes(c.shape)?[[ports[0].position,ports[1].position]]:['fitting','valve','cap'].includes(c.shape)?ports.map(q=>[f.o,q.position]):[];
  return Object.assign({},p,{component_name:c.name,trade:c.trade,shape:c.shape,outer_diameter:c.outer_diameter,size:c.size,layout:c.layout,color:c.color,length:len,
   origin:f.o,axes:{x:f.x,y:f.y,w:f.w},ports,legs,_src:p})}
 // world point -> wall view coordinates of the shown face: u along the wall, z above the storey floor, depth out of the face
 function proj(w,f,P){const s=w.start,d=unit2(w),n=w.normal_in,[t,sg]=faceT(w,f);
  return {u:(P[0]-s[0])*d[0]+(P[1]-s[1])*d[1],z:P[2]-w.z0,dep:((P[0]-s[0])*n[0]+(P[1]-s[1])*n[1]-t)*sg}}
 const dist=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1],a[2]-b[2]);const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
 // cables: an end (line power, dn = cores) fits only an entry whose `cores` lists its core count, never another cable;
// a conduit carrying a cable (`cores` on its ends) fits an entry only when the core counts overlap
// an entry may restrict the cable type (`cable_types`) and cross-section (`cross_section`), like PartPorts.cable_fits
function cableFits(c,e){const t=e.cable_types,s=e.cross_section;if(t&&c.cable_type!=null&&!t.includes(c.cable_type))return false;
  if(t&&c.line==='power'&&c.cable_type==null)return false;return !(s&&c.section!=null&&Math.abs(c.section-s)>1e-6)}
function compatible(a,b){if(a.active===false||b.active===false)return false;if(a.line==='power'||b.line==='power'){if(a.line===b.line)return false;const [c,e]=a.line==='power'?[a,b]:[b,a];return (e.cores||[]).includes(+c.dn)&&cableFits(c,e)}
  if(a.line!==b.line||Math.abs(a.dn-b.dn)>1e-6)return false;if(a.cores&&b.cores&&!a.cores.some(x=>b.cores.includes(x)))return false;
  if(!(cableFits(a,b)&&cableFits(b,a)))return false;
  const g=new Set([a.gender,b.gender]);return g.has('any')||(g.has('spigot')&&g.has('socket'))}
const cableCores=r=>((inst().cables||[]).find(x=>x.ref===r)||{}).cores;
const cableOf=r=>(inst().cables||[]).find(x=>x.ref===r);
// box clamps per conductor: the smallest pole count = active cable entries (connected ones first, like the core)
const ROLES=['L','N','PE','L1','L2','L3'];const THREE=new Set();
const clampOf=r=>(inst().clamps||[]).find(x=>x.ref===r);
function capacity(p){const ps=(p.clamps||[]).map(c=>(clampOf(c.clamp)||{}).poles).filter(Boolean);return ps.length?Math.min(...ps):null}
function activate(p){const n=p.shape==='box'?capacity(p):null;p.ports.forEach(q=>q.active=true);if(n==null)return;
  const es=p.ports.filter(q=>q.cores);es.filter(q=>q.connected_to).concat(es.filter(q=>!q.connected_to)).forEach((q,i)=>{q.active=i<n;if(!q.active&&q.status==='open')q.status='inactive'})}
const portText=q=>(q.label?q.label+': ':'')+(q.line==='power'?'Kabel '+q.dn+'-adrig':q.line.toUpperCase()+' DN '+q.dn+(q.cores?' (Kabel '+(q.cable_types?q.cable_types.join('/')+' ':'')+q.cores.join('/')+'-adrig'+(q.cross_section?' '+String(q.cross_section).replace('.',',')+' mm²':'')+')':''));
 // angle rule of a port (same as core PartPorts.angle_of): own angle, else cable ends / cable entries any, else right
 const angleOf=q=>q.angle==='right'||q.angle==='any'?q.angle:(q.line==='power'||(q.cores&&q.cores.length)?'any':'right');
 const anyAngle=(a,b)=>angleOf(a)==='any'||angleOf(b)==='any';
 const seated=(a,b)=>dist(a.position,b.position)<=SEAT&&(anyAngle(a,b)||dot(a.direction,b.direction)<=OPP);
 // --- parts of the shown wall: server parts, replaced by the edit buffer ---------------------------------
 const SRC=['id','component','storey','host','u','z','depth','rot','length','path','connections','open_ok','system','medium','cable','circuit','clamps','estimated','note'];
 function source(p){const o={};SRC.forEach(k=>{if(p[k]!=null&&!(k==='rot'&&!Object.keys(p[k]).length)&&!(k==='open_ok'&&!p[k].length)&&!(k==='clamps'&&!p[k].length)&&!(k==='connections'&&!Object.keys(p[k]).length))o[k]=JSON.parse(JSON.stringify(p[k]))});return o}
 const mine=(w,p)=>p.host&&p.host.wall===w.id&&p.storey===ST.id;
 function sources(w){const out=new Map();(inst().parts||[]).filter(p=>mine(w,p)&&!dels.has(p.id)).forEach(p=>out.set(p.id,source(p)));
  if(buf)buf.forEach((p,id)=>out.set(id,p));return [...out.values()]}
 function scene(w){const f=faceOf(w);const parts=sources(w).map(p=>geo(w,p)).filter(Boolean);
  const own=parts.filter(p=>p.host.face===f),ghosts=parts.filter(p=>p.host.face!==f);
  const ids=new Set(parts.map(p=>p.id));const [t]=[w.thickness];const [fa,fb]=faceRange(w,view);
  const anchors=[];(inst().parts||[]).forEach(p=>{if(ids.has(p.id)||dels.has(p.id))return;p.ports.forEach(q=>{if(q.status==='connected'&&!ids.has((q.connected_to||'').split('.')[0]))return;
   const v=proj(w,f,q.position);if(v.dep<=0.25&&v.dep>=-t-0.25&&v.u>=fa-0.25&&v.u<=fb+0.25&&v.z>=-0.25&&v.z<=w.height+0.25)anchors.push({part:p,q})})});
  match(w,parts,anchors);return {f,own,ghosts,anchors}}
 function match(w,parts,anchors){const pool=[];parts.forEach(p=>p.ports.forEach(q=>pool.push([p,q])));anchors.forEach(a=>pool.push([a.part,a.q,true]));
  pool.forEach(([p,q,ext])=>{if(!ext){q.status='open';q.connected_to=null}});
  for(let i=0;i<pool.length;i++)for(let j=i+1;j<pool.length;j++){const [pa,a,ea]=pool[i],[pb,b,eb]=pool[j];
   if(pa.id===pb.id||(ea&&eb)||(!ea&&a.connected_to)||(!eb&&b.connected_to)||!seated(a,b)||!compatible(a,b))continue;
   if(!ea){a.connected_to=pb.id+'.'+b.id;a.status='connected'}if(!eb){b.connected_to=pa.id+'.'+a.id;b.status='connected'}}
  parts.forEach(p=>p.ports.forEach(q=>{if(q.connected_to)return;q.transfer=transfer(w,p,q);q.status=(p.open_ok||[]).includes(q.id)?'open_ok':q.transfer?'transfer':'open'}));parts.forEach(activate)}
 function transfer(w,p,q){const z=q.position[2]-ST.elevation;if(z<=SEAT)return 'below';if(z>=ST.height-SEAT)return 'above';
  return proj(w,p.host.face,q.position).dep<=-w.thickness+SEAT?'beside':null}
 // --- snapping: nearest compatible free port within 5 cm, rotating the part if its port does not face it --
 function rotations(){const out=[];for(let p=0;p<360;p+=15)for(const t of [0,90,-90,180])for(const q of [0,90,-90])for(const fl of [false,true])out.push({plane:p,tilt:t,turn:q,flip:fl});return out}
 const ROTS=rotations();
 function snap(w,p,pool){const c=cat(p.component);if(!c)return null;let best=null;
  const try1=rot=>{const g=geo(w,Object.assign({},p,{rot}));g.ports.forEach(a=>pool.forEach(([op,b])=>{if(!compatible(a,b)||(!anyAngle(a,b)&&dot(a.direction,b.direction)>OPP))return;
   const dd=dist(a.position,b.position);if(SNAP>0&&dd<=SNAP&&(!best||dd<best.dd))best={dd,rot,a,b,op}}))};
  try1(p.rot||{});if(!best)ROTS.forEach(r=>try1(r));if(!best)return null;
  const f=frame(w,Object.assign({},p,{rot:best.rot}));const dl=[0,1,2].map(i=>best.b.position[i]-best.a.position[i]);
  return {rot:best.rot,du:dot(dl,f.eu),dz:dl[2],ddep:dot(dl,f.eo),port:best.a.id,to:best.op.id+'.'+best.b.id}}
 // --- drawing --------------------------------------------------------------------------------------------
 const P2=(w,f,P)=>{const v=proj(w,f,P);return [sx(w,v.u),sz(w,v.z),v.dep]};
 // drawing of the catalog (layout.shapes, local x/y in the wall plane) instead of the default rectangle
 function drawShapes(g,w,f,p,shapes,isCur){const W=(x,y)=>P2(w,f,[0,1,2].map(i=>p.origin[i]+x*p.axes.x[i]+y*p.axes.y[i]));
  const ln=(a,b)=>Math.hypot(a[0]-b[0],a[1]-b[1]),dash=P2(w,f,p.origin)[2]<0?'4 2':'none',edge=isCur?'#1C69D4':null;
  shapes.forEach(s=>{const stroke=edge||s.stroke||'#455A64',fill=s.fill&&s.fill!=='none'?s.fill:(s.kind==='rect'||s.kind==='circle')&&!s.fill?p.color:'none';
   if(s.kind==='rect'){const cs=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>W(s.x+a*s.w/2,s.y+b*s.h/2));
    g.appendChild(sv('polygon',{points:cs.map(c=>c[0].toFixed(1)+','+c[1].toFixed(1)).join(' '),fill,stroke,'stroke-width':isCur?2.5:1,'stroke-dasharray':dash}))}
   else if(s.kind==='circle'){const c=W(s.x,s.y),r=ln(c,W(s.x+s.r,s.y));g.appendChild(sv('circle',{cx:c[0],cy:c[1],r,fill,stroke,'stroke-width':isCur?2.5:1,'stroke-dasharray':dash}))}
   else if(s.kind==='line'){const a=W(s.x,s.y),b=W(s.x2,s.y2);g.appendChild(sv('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],stroke,'stroke-width':isCur?2.5:1.5}))}
   else if(s.kind==='cable'){if(!s.ends)return;const P=[s.ends[0],...(s.points||[]),s.ends[1]],q=[];
    // Catmull-Rom sampled in local coordinates, then projected (same curve as the catalog editor)
    for(let i=0;i<P.length-1;i++){const p0=P[i-1]||P[i],p1=P[i],p2=P[i+1],p3=P[i+2]||p2;
     for(let k=0;k<12;k++){const t=k/12,t2=t*t,t3=t2*t,c=j=>0.5*(2*p1[j]+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3);q.push(W(c(0),c(1)))}}
    q.push(W(P[P.length-1][0],P[P.length-1][1]));
    g.appendChild(sv('polyline',{points:q.map(c=>c[0].toFixed(1)+','+c[1].toFixed(1)).join(' '),fill:'none',stroke,'stroke-width':isCur?2.5:1.5,'stroke-linecap':'round'}))}
   else{const c=W(s.x,s.y),t=sv('text',{x:c[0],y:c[1],'font-size':Math.max(6,ln(c,W(s.x,s.y+(s.size||0.01)))),fill:stroke,'text-anchor':'middle','dominant-baseline':'middle','pointer-events':'none'});t.textContent=s.text||'';g.appendChild(t)}})}
 function drawPart(w,f,p,ghost){const g=sv('g',{'data-part':p.id,style:ghost?'pointer-events:none;opacity:.45':(on?'cursor:move':'cursor:pointer')});
  const isCur=cur===p.id,r=Math.max(2,(p.outer_diameter||0.02)*S);const deep=pt=>P2(w,f,pt)[2]<0;
  p.legs.forEach(([a,b])=>{const A=P2(w,f,a),B=P2(w,f,b);const inside=deep(a)||deep(b);
   if(Math.hypot(A[0]-B[0],A[1]-B[1])<1)g.appendChild(sv('circle',{cx:A[0],cy:A[1],r:r/2,fill:p.color,stroke:isCur?'#1C69D4':'#555','stroke-dasharray':inside?'3 2':'none'}));
   else{g.appendChild(sv('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],stroke:isCur?'#1C69D4':'#555','stroke-width':r+2,'stroke-linecap':'round','stroke-dasharray':inside?'6 3':'none'}));
    g.appendChild(sv('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],stroke:p.color,'stroke-width':r,'stroke-linecap':'round','stroke-opacity':inside?.55:1}))}});
  sockets(g,w,f,p,r);if(p.shape==='cable'&&!ghost)bends(g,w,f,p,isCur);
  const shapes=(p.layout||{}).shapes;
  if(shapes&&shapes.length)drawShapes(g,w,f,p,shapes,isCur);
  else if(p.shape==='box'||p.shape==='insert'){const [bw,bh]=p.size||[0.07,0.07];const cs=[[-1,-1],[1,-1],[1,1],[-1,1]].map(([a,b])=>P2(w,f,[0,1,2].map(i=>p.origin[i]+a*bw/2*p.axes.x[i]+b*bh/2*p.axes.y[i])));
   g.appendChild(sv('polygon',{points:cs.map(c=>c[0].toFixed(1)+','+c[1].toFixed(1)).join(' '),fill:p.color,stroke:isCur?'#1C69D4':'#555','stroke-width':isCur?2.5:1,'stroke-dasharray':P2(w,f,p.origin)[2]<0?'4 2':'none'}));
   if(p.shape==='insert'){const c=P2(w,f,p.origin);g.appendChild(sv('circle',{cx:c[0],cy:c[1],r:bw*S*0.3,fill:'none',stroke:'#555'}))}}
  if(p.shape==='valve'){const c=P2(w,f,p.origin);g.appendChild(sv('rect',{x:c[0]-r,y:c[1]-r*1.6,width:2*r,height:3.2*r,fill:'#C62828'}))}
  if(!ghost)p.ports.forEach(q=>{const c=P2(w,f,q.position);const endDrag=on&&['pipe','cable'].includes(p.shape);const dotc=sv('circle',{cx:c[0],cy:c[1],r:isCur?5:4,fill:PORT[q.status],stroke:'#fff','stroke-width':1.2,style:endDrag?'cursor:ew-resize':'cursor:context-menu'});
   if(endDrag)dotc.addEventListener('pointerdown',ev=>{if(ev.button===0)startEnd(ev,w,p,q)});
   dotc.addEventListener('pointermove',ev=>showTip(ev,['Anschluss '+q.id+' – '+STATUS_DE[q.status]+(q.transfer?' '+TRANSFER_DE[q.transfer]:''),portText(q)+' ('+({spigot:'Spitzende',socket:'Muffe',any:'beliebig'})[q.gender]+')',q.connected_to?'an '+q.connected_to:'Rechtsklick: bewusst offen / weiterbauen',['pipe','cable'].includes(p.shape)?'Länge '+num(cmv(p.length))+' cm – Ende ziehen zum Kürzen':'']));
   dotc.addEventListener('pointerleave',hideTip);dotc.addEventListener('contextmenu',ev=>{ev.preventDefault();portMenu(ev,w,p,q)});g.appendChild(dotc)});
  g.addEventListener('pointermove',ev=>{if(!drag)showTip(ev,[(p.component_name||p.component)+(ghost?' (andere Wandseite)':''),'Teil '+p.id+(p.length?' – Länge '+num(cmv(p.length))+' cm':''),layerText(w,f,p)])});
  g.addEventListener('pointerleave',hideTip);if(!ghost)g.addEventListener('pointerdown',ev=>startDrag(ev,w,p));svg.appendChild(g)}
 // cable: bend points as squares (drag = move, double click / right click = remove); a press on a piece of the
// selected cable inserts a bend point there and drags it
function bends(g,w,f,p,isCur){if(!on||!isCur)return;
  p.legs.forEach(([a,b],i)=>{const A=P2(w,f,a),B=P2(w,f,b);const hit=sv('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],stroke:'transparent','stroke-width':12,style:'cursor:copy'});
   hit.addEventListener('pointermove',ev=>{if(!drag)showTip(ev,['Klick: Knickpunkt einfügen','Ziehen am Rand: ganze Leitung verschieben'])});hit.addEventListener('pointerleave',hideTip);
   hit.addEventListener('pointerdown',ev=>{if(ev.button!==0||carry)return;ev.preventDefault();ev.stopPropagation();insertBend(ev,w,f,p,i,A,B)});g.appendChild(hit)});
  (p.path||[]).slice(0,-1).forEach((q,k)=>{const c=P2(w,f,frame(w,p).pt(q));const sq=sv('rect',{x:c[0]-4,y:c[1]-4,width:8,height:8,fill:'#fff',stroke:'#1C69D4','stroke-width':2,style:'cursor:move'});
   sq.addEventListener('pointermove',ev=>{if(!drag)showTip(ev,['Knickpunkt '+(k+1),'ziehen = verschieben (1 cm, Shift 1 mm)','Doppelklick / Rechtsklick = entfernen'])});sq.addEventListener('pointerleave',hideTip);
   sq.addEventListener('pointerdown',ev=>{if(ev.button!==0)return;ev.preventDefault();ev.stopPropagation();startBend(ev,w,p,k)});
   const rm=ev=>{ev.preventDefault();ev.stopPropagation();removeBend(w,p,k)};sq.addEventListener('dblclick',rm);sq.addEventListener('contextmenu',rm);g.appendChild(sq)})}
// local point of the part for a world point (orthonormal axes)
function toLocal(w,s,P){const f=frame(w,s);const d=P.map((v,i)=>v-f.o[i]);return [dot(d,f.x),dot(d,f.y),dot(d,f.w)].map(r4)}
// world point on the face f at view (u, z) and depth dep
function wallPt(w,f,u,z,dep){const d=unit2(w),n=w.normal_in,[t,sg]=faceT(w,f);return [w.start[0]+d[0]*u+n[0]*t+sg*n[0]*dep,w.start[1]+d[1]*u+n[1]*t+sg*n[1]*dep,w.z0+z]}
// a straight cable gets an explicit path (its end b) before the first bend
function pathOf(w,s){const c=cat(s.component);if(!s.path||!s.path.length)s.path=[[r4(s.length||c.stretch.default_length),0,0]];delete s.length;return s.path}
function insertBend(ev,w,f,p,i,A,B){const s=edit(p);const path=pathOf(w,s);cur=p.id;
  const m=svg.getScreenCTM().inverse(),q=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(m);const dx=B[0]-A[0],dy=B[1]-A[1];
  const t=Math.max(0.05,Math.min(0.95,((q.x-A[0])*dx+(q.y-A[1])*dy)/Math.max(1e-9,dx*dx+dy*dy)));const [a,b]=p.legs[i];
  path.splice(i,0,toLocal(w,s,a.map((v,j)=>v+(b[j]-v)*t)));startBend(ev,w,p,i)}
function startBend(ev,w,p,k){const s=edit(p);cur=p.id;const P=frame(w,s).pt(s.path[k]);drag={bend:k,w,id:p.id,dep:proj(w,faceOf(w),P).dep};svg.setPointerCapture(ev.pointerId);buildPanel();draw()}
function bendMove(ev,w){const s=buf.get(drag.id),v=ptView(ev,w),st=ev.shiftKey?1000:100;
  s.path[drag.bend]=toLocal(w,s,wallPt(w,faceOf(w),Math.round(v.u*st)/st,Math.round(v.z*st)/st,drag.dep));fill();draw()}
function removeBend(w,p,k){const s=edit(p);if(!s.path||s.path.length<2)return;s.path.splice(k,1);hideTip();fill();draw()}
// cable end drag with a path: b moves the last point, a moves the origin (the other points stay where they are)
function cableEndMove(ev,w){const s=buf.get(drag.id),v=ptView(ev,w),st=ev.shiftKey?1000:100,f=faceOf(w);
  let P=wallPt(w,f,Math.round(v.u*st)/st,Math.round(v.z*st)/st,drag.dep);
  pool([drag.id]).forEach(([op,q])=>{const me=geo(w,s).ports.find(x=>x.id===drag.end);if(me&&compatible(me,q)&&dist(q.position,P)<=SNAP)P=q.position.slice()});
  if(drag.end==='b')s.path[s.path.length-1]=toLocal(w,s,P);
  else{const keep=s.path.map(q=>frame(w,s).pt(q));const pv=proj(w,f,P);s.u=r4(pv.u);s.z=r4(pv.z);s.depth=r4(pv.dep);s.path=keep.map(q=>toLocal(w,s,q))}
  fill();draw()}
// socket ends (Muffe) as a thicker band; waste water pipes get a flow arrow from the socket to the spigot end
 function sockets(g,w,f,p,r){const od=p.outer_diameter||0.02;
  p.ports.forEach(q=>{if(q.gender!=='socket')return;const leg=p.legs.find(l=>dist(l[1],q.position)<1e-6||dist(l[0],q.position)<1e-6);if(!leg)return;
   const other=dist(leg[1],q.position)<1e-6?leg[0]:leg[1],len=dist(other,q.position);if(len<1e-6)return;const k=Math.min(1.5*od,len/2)/len;
   const A=P2(w,f,q.position),B=P2(w,f,q.position.map((v,i)=>v+(other[i]-v)*k));if(Math.hypot(A[0]-B[0],A[1]-B[1])<0.5)return;
   g.appendChild(sv('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],stroke:'#444','stroke-width':r*1.45+2}));
   g.appendChild(sv('line',{x1:A[0],y1:A[1],x2:B[0],y2:B[1],stroke:p.color,'stroke-width':r*1.45}))});
  if(p.trade!=='waste_water'||p.shape!=='pipe')return;const s=p.ports.find(q=>q.gender==='socket'),e=p.ports.find(q=>q!==s);if(!s||!e)return;
  const A=P2(w,f,s.position),B=P2(w,f,e.position),dx=B[0]-A[0],dy=B[1]-A[1],l=Math.hypot(dx,dy);if(l<14)return;
  const ux=dx/l,uy=dy/l,m=[(A[0]+B[0])/2,(A[1]+B[1])/2],a=Math.max(5,r*0.9);
  const tri=[[m[0]+ux*a,m[1]+uy*a],[m[0]-ux*a-uy*a*0.7,m[1]-uy*a+ux*a*0.7],[m[0]-ux*a+uy*a*0.7,m[1]-uy*a-ux*a*0.7]];
  const t=sv('polygon',{points:tri.map(c=>c[0].toFixed(1)+','+c[1].toFixed(1)).join(' '),fill:'#333'});
  t.addEventListener('pointermove',ev=>showTip(ev,['Fließrichtung: Muffe → Spitzende']));t.addEventListener('pointerleave',hideTip);g.appendChild(t)}
 function drawAnchor(w,f,a){const c=P2(w,f,a.q.position);const g=sv('g',{});
  g.appendChild(sv('circle',{cx:c[0],cy:c[1],r:7,fill:'none',stroke:PORT[a.q.status]||'#1C69D4','stroke-width':2,'stroke-dasharray':'3 2'}));
  g.addEventListener('pointermove',ev=>showTip(ev,['Anschluss von '+a.part.id+' ('+(a.part.component_name||'')+')',(a.part.wall_name||'freies Teil')+' · '+a.part.storey,'zum Weiterbauen hier ein Teil ansetzen']));
  g.addEventListener('pointerleave',hideTip);svg.appendChild(g)}
 function layerText(w,f,p){const d=proj(w,f,p.origin).dep;if(d>=0)return 'vor der Wand ('+num(cmv(d))+' cm)';
  const t=['outside','left'].includes(f)?-d:w.thickness+d;const l=(w.layers||[]).find(x=>t>=x.offset-1e-6&&t<=x.offset+x.thickness+1e-6);
  return 'in der Wand '+num(cmv(-d))+' cm tief'+(l?' – Schicht '+((H.materials[l.material]||{}).name||l.material):'')}
 let last=null;
 function drawParts(w,pts){const s=scene(w);last={w,...s};s.ghosts.forEach(p=>drawPart(w,s.f,p,true));s.anchors.forEach(a=>drawAnchor(w,s.f,a));
  s.own.forEach(p=>drawPart(w,s.f,p,false));let carried=null;if(carry){carried=geo(w,carry);if(carried){match(w,[carried].concat(s.own),s.anchors);drawPart(w,s.f,carried,false)}}
  s.own.forEach(p=>pts.add(proj(w,s.f,p.origin).u));
  clashes().forEach(c=>{const P=P2(w,s.f,c.at);const ring=sv('circle',{cx:P[0],cy:P[1],r:10,fill:'none',stroke:'#C62828','stroke-width':3});
   ring.addEventListener('pointermove',ev=>showTip(ev,['Nicht verbunden: '+c.part+'.'+c.port+' ↔ '+c.other,c.why,'Teil an einen freien passenden Anschluss setzen (rastet ein) oder wegrücken']));
   ring.addEventListener('pointerleave',hideTip);svg.appendChild(ring)});
  if(window.Install3d)Install3d.update(w,s.f,s.own.concat(s.ghosts,carried?[carried]:[]),cur,H.materials)}
 // --- interaction ----------------------------------------------------------------------------------------
 function ptView(ev,w){const m=svg.getScreenCTM().inverse(),q=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(m);const [fa,fb]=faceRange(w,view);
  return {u:mirrorOf(w,view)?fb-(q.x-PADL)/S:fa+(q.x-PADL)/S,z:w.height-(q.y-PADT)/S}}
 const r4=v=>Math.round(v*10000)/10000;
 function edit(p){if(!buf)buf=new Map();if(!buf.has(p.id))buf.set(p.id,source(p._src||p));return buf.get(p.id)}
 function group(id){const ids=new Set([id]),todo=[id];const own=last?last.own:[];
  while(todo.length){const id0=todo.pop(),p=own.find(x=>x.id===id0);if(!p)continue;p.ports.forEach(q=>{const o=(q.connected_to||'').split('.')[0];if(o&&!ids.has(o)&&own.some(x=>x.id===o)){ids.add(o);todo.push(o)}})}return [...ids]}
 // free ports to snap to: a port already joined to a part outside the moving set takes no second part
 const free=(q,excl)=>!q.connected_to||excl.includes(q.connected_to.split('.')[0]);
 function pool(excl){const out=[];if(!last)return out;last.own.concat(last.ghosts).forEach(p=>{if(!excl.includes(p.id))p.ports.forEach(q=>{if(free(q,excl))out.push([p,q])})});
  last.anchors.forEach(a=>{if(free(a.q,excl))out.push([a.part,a.q])});return out}
 // a free port of a shown part lying on another port (closer than 3 cm) without a connection: wrong angle, port
 // already taken or misfit - not allowed. Only the nearest port counts; joined ports are fine.
 const CLASH=0.03;
 function clashes(){const out=[];if(!last)return out;const all=[];last.own.concat(last.ghosts).forEach(p=>p.ports.forEach(q=>all.push([p,q])));
  last.anchors.forEach(a=>all.push([a.part,a.q]));
  last.own.forEach(pa=>pa.ports.forEach(a=>{if(a.connected_to)return;let near=null;
   all.forEach(([pb,b])=>{if(pb.id===pa.id||(b.connected_to||'').split('.')[0]===pa.id)return;const d=dist(a.position,b.position);if(d<=CLASH&&(!near||d<near.d))near={pb,b,d}});
   if(!near)return;const b=near.b;if(out.some(o=>o.part===near.pb.id&&o.port===b.id&&o.other===pa.id+'.'+a.id))return;
   const why=!compatible(a,b)?'passt nicht ('+portText(a)+' / '+portText(b)+(a.gender===b.gender&&a.gender!=='any'&&a.line!=='power'?', '+({spigot:'2× Spitzende',socket:'2× Muffe'})[a.gender]:'')+')'
    :b.connected_to?'Anschluss schon belegt':'Winkel/Lage passt nicht ('+Math.round(Math.acos(Math.max(-1,Math.min(1,-dot(a.direction,b.direction))))*180/Math.PI)+'°, '+Math.round(near.d*1000)+' mm)';
   out.push({part:pa.id,port:a.id,other:near.pb.id+'.'+b.id,why,at:a.position})}));
  return out}
 function startDrag(ev,w,p){if(carry&&on)return;ev.preventDefault();ev.stopPropagation();cur=p.id;if(!on){buildPanel();draw();return}
  const ids=ev.altKey?[p.id]:group(p.id);const at=ptView(ev,w);
  drag={w,id:p.id,ids,at,start:ids.map(id=>{const s=edit((last.own.find(x=>x.id===id)||{})._src||sources(w).find(x=>x.id===id));return [id,s.u,s.z,s.depth]}),clash0:clashOf(ids)};
  svg.setPointerCapture(ev.pointerId);buildPanel();draw()}
 // straight pipe: change the length so that `end` (a or b) lands at length L; the other end stays where it is
 function setLength(w,s,end,L){const c=cat(s.component);const max=c.stretch.max_length;L=Math.min(max,Math.max(0.01,r4(L)));
  const old=s.length||c.stretch.default_length;if(end==='a'){const f=frame(w,s);const dl=f.x.map(v=>v*(old-L));
   s.u=r4(s.u+dot(dl,f.eu));s.z=r4(s.z+dl[2]);s.depth=r4(s.depth+dot(dl,f.eo))}s.length=L}
 function startEnd(ev,w,p,q){if(!on||carry||!['pipe','cable'].includes(p.shape))return false;ev.preventDefault();ev.stopPropagation();cur=p.id;const s=edit(p);
  if(p.shape==='cable'&&s.path&&s.path.length){drag={end:q.id,cable:true,w,id:p.id,dep:proj(w,faceOf(w),q.position).dep};svg.setPointerCapture(ev.pointerId);buildPanel();draw();return true}
  const fixed=p.ports.find(x=>x.id!==q.id).position;const ax=q.direction;drag={end:q.id,w,id:p.id,fixed,ax};svg.setPointerCapture(ev.pointerId);buildPanel();draw();return true}
 function endMove(ev,w){const s=buf.get(drag.id),f=frame(w,s),v=ptView(ev,w),F=proj(w,faceOf(w),drag.fixed);
  // the axis seen in the wall view; a pipe pointing into the wall cannot be dragged (use +/−)
  const au=dot(drag.ax,f.eu),az=drag.ax[2],n2=au*au+az*az;if(n2<0.01)return;
  const st=ev.shiftKey?1000:100;let L=Math.round(((v.u-F.u)*au+(v.z-F.z)*az)/n2*st)/st;
  pool([drag.id]).forEach(([op,q])=>{const g=geo(w,s),me=g.ports.find(x=>x.id===drag.end);if(!compatible(me,q)||(!anyAngle(me,q)&&dot(q.direction,drag.ax)>OPP))return;
   const d=[0,1,2].map(i=>q.position[i]-drag.fixed[i]),al=dot(d,drag.ax),perp=Math.hypot(...[0,1,2].map(i=>d[i]-al*drag.ax[i]));
   if(perp<=SEAT&&Math.abs(al-L)<=SNAP)L=al});
  setLength(w,s,drag.end,L);fill();draw()}
 svg.addEventListener('pointermove',ev=>{const w=wall();if(carry&&on){const v=ptView(ev,w);carry.u=r4(Math.round(v.u*100)/100);carry.z=r4(Math.max(0,Math.round(v.z*100)/100));
   const s=snap(w,carry,pool([carry.id]));if(s)apply(carry,s);draw();return}
  if(drag&&drag.bend!=null){bendMove(ev,w);return}
  if(drag&&drag.cable){cableEndMove(ev,w);return}
  if(drag&&drag.end){endMove(ev,w);return}
  if(!drag)return;const v=ptView(ev,w),st=ev.shiftKey?1000:100;const du=Math.round((v.u-drag.at.u)*st)/st,dz=Math.round((v.z-drag.at.z)*st)/st;
  drag.start.forEach(([id,u,z])=>{const s=buf.get(id);s.u=r4(u+du);s.z=r4(z+dz)});
  const s=buf.get(drag.id);const sn=snap(w,s,pool(drag.ids));
  if(sn&&(drag.ids.length===1||JSON.stringify(sn.rot)===JSON.stringify(s.rot||{})))drag.ids.forEach(id=>{const x=buf.get(id);if(id===drag.id&&drag.ids.length===1)x.rot=sn.rot;x.u=r4(x.u+sn.du);x.z=r4(x.z+sn.dz);x.depth=r4(x.depth+sn.ddep)});
  fill();draw()});
 // a part may only be set down / dropped where it does not lie on an occupied or unfitting port
 const clashOf=ids=>clashes().filter(c=>ids.includes(c.part)||ids.includes(c.other.split('.')[0])).length;
 const refuse=ev=>showTip(ev,['Hier nicht möglich: Anschluss belegt oder passt nicht','an einen freien passenden Anschluss setzen']);
 svg.addEventListener('pointerup',ev=>{if(!drag)return;const d=drag;drag=null;draw();
  if(d.start&&clashOf(d.ids)>d.clash0){d.start.forEach(([id,u,z,dep])=>{const s=buf.get(id);s.u=u;s.z=z;s.depth=dep});fill();draw();refuse(ev,clashOf(d.ids)||'')}});
 svg.addEventListener('click',ev=>{if(!carry||!on)return;ev.stopPropagation();if(!buf)buf=new Map();const c=carry;buf.set(c.id,c);carry=null;draw();
  if(clashOf([c.id])){buf.delete(c.id);carry=c;draw();refuse(ev,'');return}cur=c.id;buildPanel();draw()});
 function apply(p,s){p.rot=s.rot;p.u=r4(p.u+s.du);p.z=r4(p.z+s.dz);p.depth=r4(p.depth+s.ddep)}
 function newId(){const ids=new Set((inst().parts||[]).map(p=>p.id).concat(buf?[...buf.keys()]:[]));let n=1;while(ids.has('p-'+n))n++;return 'p-'+n}
 // grouped palette entry: dialog for the type (variant) and, for boxes, the number of connections (clamp poles)
 function pick(c){if(!c.variants){startCarry(c);draw();return}
  const box=c.shape==='box'&&c.trade==='electrical';const poles=[...new Map((inst().clamps||[]).map(x=>[x.poles,x])).values()].sort((a,b)=>a.poles-b.poles);
  const vs=sel(c.variants.map(x=>[x.ref,x.label]),c.ref);
  const ns=box?sel([['','– ohne Klemmen (alle Einführungen) –']].concat(poles.map(x=>[x.ref,x.poles+' Anschlüsse (WAGO '+x.poles+'-polig)'])),(poles.find(x=>x.poles===3)||{}).ref||''):null;
  const close=()=>ov.remove();
  const ok=()=>{const v=cat(vs.value);close();if(!v)return;startCarry(v);
   if(ns&&ns.value){carry.clamps=['L','N','PE'].map(r=>({role:r,clamp:ns.value}));buildPanel()}draw()};
  const ov=h('div',{style:'position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1000;display:flex;align-items:center;justify-content:center'},
   h('div',{style:'background:#fff;padding:1rem 1.2rem;border-radius:6px;min-width:320px;box-shadow:0 4px 18px rgba(0,0,0,.3)'},
    h('h3',{style:'margin-top:0',text:c.group_name+' einfügen'}),field(c.shape==='cable'?'Ausführung (Adern × Querschnitt)':'Typ',vs),
    ns?field('Anzahl Anschlüsse',ns,'Klemmen je Leiter L, N, PE'):null,
    h('div',{style:'display:flex;gap:.5rem;margin-top:.8rem;justify-content:flex-end'},h('button',{class:'btn2',text:'Abbrechen',onclick:close}),h('button',{class:'btn',text:'Einfügen',onclick:ok}))));
  ov.addEventListener('keydown',ev=>{if(ev.key==='Escape')close();if(ev.key==='Enter')ok();ev.stopPropagation()});
  ov.addEventListener('click',ev=>{if(ev.target===ov)close()});document.body.appendChild(ov);vs.focus()}
 function startCarry(c){const w=wall();const r=(c.outer_diameter||0.02)/2;const depth=c.shape==='box'?(place==='in'?0:c.size[2]):c.shape==='insert'?0:(place==='in'?-(r+0.005):r+0.01);
  carry={id:newId(),component:c.ref,storey:ST.id,host:{wall:w.id,face:faceOf(w)},u:0,z:1,depth:r4(depth),rot:{}};
  if(c.stretch)carry.length=c.stretch.default_length;if(c.medium&&c.trade==='water_supply')carry.medium=c.medium;cur=carry.id;buildPanel()}
 document.addEventListener('keydown',ev=>{if(on&&ev.key==='Escape'&&!document.querySelector('.ovl,dialog[open]')){newGroup();return}
  if(!on||['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName))return;
  const w=wall();const own=last?last.own.find(x=>x.id===cur):null;const target=carry&&carry.id===cur?carry:own?edit(own):null;
  if(!target||!target.component)return;const m=mirrorOf(w,view)?-1:1;const st=ev.shiftKey?0.001:0.01;
  const k=ev.key.toLowerCase();let done=true;if((ev.ctrlKey||ev.metaKey)&&k!=='d')return;
  // rotations, flip and moves act on the selected part and everything connected to it (Alt = only this part),
  // as one rigid body about the origin of the selected part, in wall axes (u, z, depth)
  const members=target===carry||ev.altKey?[target]:group(target.id).map(id=>id===target.id?target:edit(last.own.find(x=>x.id===id)));
  const A=15*Math.PI/180,rz=a=>[[Math.cos(a),-Math.sin(a),0],[Math.sin(a),Math.cos(a),0],[0,0,1]],
   rx=a=>[[1,0,0],[0,Math.cos(a),-Math.sin(a)],[0,Math.sin(a),Math.cos(a)]],ry=a=>[[Math.cos(a),0,Math.sin(a)],[0,1,0],[-Math.sin(a),0,Math.cos(a)]];
  if(k==='d'&&ev.ctrlKey){if(target!==carry)duplicate(target)}else if(k==='r')turnGroup(members,target,rz((ev.shiftKey?-A:A)*m));
  else if(k==='q'||k==='e')turnGroup(members,target,ry(k==='q'?-A:A));
  else if(k==='a'||k==='d')turnGroup(members,target,rx(k==='a'?-A:A));else if(k==='t')turnGroup(members,target,[[-1,0,0],[0,1,0],[0,0,1]]);
  else if(k==='w')spin(w,target,members,ev.shiftKey?-A:A);
  else if(ev.key==='ArrowLeft')shiftGroup(members,-st*m,0,0);else if(ev.key==='ArrowRight')shiftGroup(members,st*m,0,0);
  else if(ev.key==='ArrowUp')shiftGroup(members,0,st,0);else if(ev.key==='ArrowDown')shiftGroup(members,0,-st,0);
  else if(ev.key==='PageUp')shiftGroup(members,0,0,0.005);else if(ev.key==='PageDown')shiftGroup(members,0,0,-0.005);
  else if(['+','*','Add','-','_','Subtract'].includes(ev.key)&&cat(target.component).stretch&&!(target.path&&target.path.length)){const c=cat(target.component);
   setLength(w,target,'b',(target.length||c.stretch.default_length)+(['+','*','Add'].includes(ev.key)?1:-1)*st)}
  else if(ev.key==='Delete'&&target!==carry)remove(target.id);else done=false;
  if(!done)return;ev.preventDefault();if(target.component&&(buf&&buf.has(target.id)||target===carry))autoAlign(w,target,members);fill();draw()});
 const mul=(a,b)=>a.map(r=>[0,1,2].map(j=>r[0]*b[0][j]+r[1]*b[1][j]+r[2]*b[2][j]));
 const mv=(a,v)=>a.map(r=>r[0]*v[0]+r[1]*v[1]+r[2]*v[2]);
 // orientation matrix of a part in wall axes: columns = its local x, y, w (rotated() of the unit vectors)
 function matrixOf(rot){const c=[[1,0,0],[0,1,0],[0,0,1]].map(l=>rotated(l,rot||{}));return [0,1,2].map(i=>c.map(col=>col[i]))}
 // back to {plane, tilt, turn, flip}: M = Ry(turn) Rx(tilt) Rz(plane) F (YXZ Euler angles, flip when mirrored)
 function rotOf(M){const det=M[0][0]*(M[1][1]*M[2][2]-M[1][2]*M[2][1])-M[0][1]*(M[1][0]*M[2][2]-M[1][2]*M[2][0])+M[0][2]*(M[1][0]*M[2][1]-M[1][1]*M[2][0]);
  const flip=det<0,R=flip?M.map(r=>[-r[0],r[1],r[2]]):M,D=180/Math.PI,c=v=>Math.max(-1,Math.min(1,v));
  const tilt=Math.asin(-c(R[1][2]));let turn,plane;
  if(Math.abs(R[1][2])<1-1e-12){turn=Math.atan2(R[0][2],R[2][2]);plane=Math.atan2(R[1][0],R[1][1])}else{turn=Math.atan2(-R[2][0],R[0][0]);plane=0}
  const deg=v=>{let d=Math.round(v*D*1e6)/1e6;if(Math.abs(d)<1e-9)d=0;return d};
  const out={};if(deg(plane))out.plane=(deg(plane)+360)%360;if(deg(tilt))out.tilt=deg(tilt);if(deg(turn))out.turn=deg(turn);if(flip)out.flip=true;return out}
 function turnGroup(members,pivot,G){const P=[pivot.u,pivot.z,pivot.depth];
  members.forEach(s=>{const d=mv(G,[s.u-P[0],s.z-P[1],s.depth-P[2]]);s.u=r4(P[0]+d[0]);s.z=r4(P[1]+d[1]);s.depth=r4(P[2]+d[2]);s.rot=rotOf(mul(G,matrixOf(s.rot)))})}
 function shiftGroup(members,du,dz,dd){members.forEach(s=>{s.u=r4(s.u+du);s.z=r4(s.z+dz);s.depth=r4(s.depth+dd)})}
 // W: turn a pipe, bend or branch in itself about the axis of a port (the joint when joined at exactly one port,
 // else port a), together with everything joined to it (Alt = only this part)
 function axisTurn(n,a){const c=Math.cos(a),s=Math.sin(a),t=1-c;return [[t*n[0]*n[0]+c,t*n[0]*n[1]-s*n[2],t*n[0]*n[2]+s*n[1]],
  [t*n[0]*n[1]+s*n[2],t*n[1]*n[1]+c,t*n[1]*n[2]-s*n[0]],[t*n[0]*n[2]-s*n[1],t*n[1]*n[2]+s*n[0],t*n[2]*n[2]+c]]}
 function spin(w,target,members,a){const g=geo(w,target);if(!g||!g.ports.length)return;const own=last&&last.own.find(x=>x.id===target.id);
  const joined=own?own.ports.filter(q=>q.connected_to):[];const port=joined.length===1?joined[0]:g.ports[0];
  const q0=g.ports.find(q=>q.id===port.id),f0=frame(w,target),ax=[dot(q0.direction,f0.eu),q0.direction[2],dot(q0.direction,f0.eo)];
  turnGroup(members,target,axisTurn(ax.map(v=>v/Math.hypot(...ax)),a));
  const q1=geo(w,target).ports.find(q=>q.id===port.id),dl=[0,1,2].map(i=>q0.position[i]-q1.position[i]),f=frame(w,target);
  shiftGroup(members,dot(dl,f.eu),dl[2],dot(dl,f.eo))}
 // two fitting ports lying on each other (within 1 cm) but not in line: the selected part (with everything joined to
 // it) is turned by the smallest rotation that points its port against the other one and moved onto it
 const ALIGN=0.01;
 function rotationOnto(va,vb){const k=[va[1]*vb[2]-va[2]*vb[1],va[2]*vb[0]-va[0]*vb[2],va[0]*vb[1]-va[1]*vb[0]],s=Math.hypot(...k),c=dot(va,vb);
  if(s<1e-9){if(c>0)return [[1,0,0],[0,1,0],[0,0,1]];const p=Math.abs(va[0])<0.9?[1,0,0]:[0,1,0];const q=[va[1]*p[2]-va[2]*p[1],va[2]*p[0]-va[0]*p[2],va[0]*p[1]-va[1]*p[0]],l=Math.hypot(...q);
   const n=q.map(v=>v/l);return [0,1,2].map(i=>[0,1,2].map(j=>2*n[i]*n[j]-(i===j?1:0)))}
  const K=[[0,-k[2],k[1]],[k[2],0,-k[0]],[-k[1],k[0],0]],K2=mul(K,K),f=(1-c)/(s*s);
  return [0,1,2].map(i=>[0,1,2].map(j=>(i===j?1:0)+K[i][j]+K2[i][j]*f))}
 function autoAlign(w,target,members){if(!last||!target||!target.host)return false;const excl=members.map(m=>m.id),pl=pool(excl),f0=frame(w,target);
  const g=geo(w,target);if(!g)return false;const toWall=v=>[dot(v,f0.eu),v[2],dot(v,f0.eo)];let hit=null;
  g.ports.forEach(a=>{if(a.connected_to)return;pl.forEach(([op,b])=>{const d=dist(a.position,b.position);if(d<=ALIGN&&compatible(a,b)&&!seated(a,b)&&(!hit||d<hit.d))hit={a,b,d}})});
  if(!hit)return false;turnGroup(members,target,rotationOnto(toWall(hit.a.direction),toWall(hit.b.direction).map(v=>-v)));
  const a=geo(w,target).ports.find(q=>q.id===hit.a.id),dl=[0,1,2].map(i=>hit.b.position[i]-a.position[i]),f=frame(w,target);
  shiftGroup(members,dot(dl,f.eu),dl[2],dot(dl,f.eo));return true}
 // keep everything placed, drop the selection (and a carried part): the palette offers all parts again, so a new,
 // unconnected group (any trade) can be started
 function newGroup(){carry=null;cur=null;menu.style.display='none';if(document.activeElement&&panel.contains(document.activeElement))document.activeElement.blur();buildPanel();draw()}
 function newGroupBtn(){return h('button',{class:'btn2',style:'margin:.3rem 0',text:'Neue Gruppe beginnen',title:'Auswahl aufheben – das Bestehende bleibt, alle Teile der Palette (auch Elektro) sind wieder wählbar (Esc)',onclick:newGroup})}
 function remove(id){if(buf)buf.delete(id);if((inst().parts||[]).some(p=>p.id===id))dels.add(id);if(cur===id)cur=null;buildPanel();draw()}
 function duplicate(p){const c=JSON.parse(JSON.stringify(p));c.id=newId();delete c.connections;c.u=r4(c.u+0.1);if(!buf)buf=new Map();buf.set(c.id,c);cur=c.id;buildPanel();draw()}
 function portMenu(ev,w,p,q){menu.textContent='';menu.style.cssText='display:block;position:fixed;left:'+ev.clientX+'px;top:'+ev.clientY+'px';
  const item=(t,fn)=>menu.appendChild(h('div',{class:'institem',text:t,onclick:()=>{menu.style.display='none';fn();fill();draw()}}));
  if(on){const s=edit(p);const ok=(s.open_ok||[]).includes(q.id);
   item(ok?'nicht mehr bewusst offen':'bewusst offen (blau)',()=>{s.open_ok=ok?s.open_ok.filter(x=>x!==q.id):(s.open_ok||[]).concat([q.id])});
   if(q.connected_to)item('trennen (2 cm abrücken)',()=>{const f=frame(w,s);const dl=q.direction.map(c=>-c*0.02);s.u=r4(s.u+dot(dl,f.eu));s.z=r4(s.z+dl[2]);s.depth=r4(s.depth+dot(dl,f.eo))})}
  if(q.transfer==='beside')item('auf der anderen Wandseite weiterbauen',()=>{const r=document.querySelector('input[name=wview][value='+(view==='outside'?'inside':'outside')+']');r.checked=true;r.onchange()});
  if(q.transfer==='above'||q.transfer==='below')item('im Geschoss '+(q.transfer==='above'?'oben':'unten')+' weiterbauen',()=>goStorey(q));
  item('schließen',()=>{})}
 function goStorey(q){const all=(H.storeys||[]).slice().sort((a,b)=>a.elevation-b.elevation);const i=all.findIndex(s=>s.id===ST.id);
  const s=all[i+(q.transfer==='above'?1:-1)];if(!s){toast('Kein Geschoss '+(q.transfer==='above'?'darüber':'darunter'));return}
  const P=q.position;const near=s.walls.map(w=>{const d=unit2(w),n=w.normal_in,a=w.start;const t=(P[0]-a[0])*n[0]+(P[1]-a[1])*n[1],u=(P[0]-a[0])*d[0]+(P[1]-a[1])*d[1];
   return [Math.abs(t)+Math.max(0,-u,u-w.length),w]}).sort((a,b)=>a[0]-b[0])[0];
  if(!near){toast('Keine Wand im Geschoss '+(s.name||s.id));return}
  if(dirty()&&!confirm('Ungespeicherte Einbauteile verwerfen?'))return;location.href='/waende?storey='+encodeURIComponent(s.id)+'#'+encodeURIComponent(near[1].id)}
 // --- bar, palette, panel, section strip, table ------------------------------------------------------------
 function dirty(){return !!((buf&&buf.size)||dels.size||carry)}
 function changes(){const orig=new Map((inst().parts||[]).map(p=>[p.id,JSON.stringify(source(p))]));const ups=[];
  if(buf)buf.forEach((p,id)=>{const g=last&&last.own.concat(last.ghosts).find(x=>x.id===id);const s=JSON.parse(JSON.stringify(p));
   if(g){const conn={};g.ports.forEach(q=>{if(q.connected_to)conn[q.id]=q.connected_to});if(Object.keys(conn).length)s.connections=conn;else delete s.connections}
   if(orig.get(id)!==JSON.stringify(s))ups.push(s)});return {upsert:ups,delete:[...dels]}}
 function save(){const c=changes();const err=document.getElementById('insterr');err.textContent='';
  post('/api/part/save',c).then(({ok,j})=>{if(!ok||j.error){(j.errors||[j.error]).forEach(t=>err.appendChild(h('div',{text:t})));return}
   buf=null;dels=new Set();carry=null;on=false;reload(false,'Einbauteile gespeichert: '+(c.upsert.length+c.delete.length))})}
 function discard(){if(dirty()&&!confirm('Änderungen an Einbauteilen verwerfen?'))return;buf=null;dels=new Set();carry=null;on=false;cur=null;buildPanel();draw()}
 function buildBar(w){palTop=pal.scrollTop;bar.textContent='';pal.textContent='';
  if(!on){bar.appendChild(h('button',{class:'btn2',text:'Installation bearbeiten',onclick:()=>{on=true;buildPanel();draw()}}));
   bar.appendChild(h('span',{class:'note',style:'margin-left:.6rem',text:'Elektro, Abwasser und Zuwasser als Einzelteile; Anschlüsse rot = offen, grün = verbunden, blau = bewusst offen / Übergabe.'}));return}
  const ps=sel([['in','in der Wand (Unterputz)'],['out','vor der Wand (Aufputz)']],place);ps.onchange=()=>{place=ps.value;buildBar(w)};
  const cl=clashes();
  const mg=h('input',{type:'range',min:'0',max:'30',step:'1',style:'vertical-align:middle;width:110px'});mg.value=Math.round(SNAP*100);
  const mgv=h('span',{class:'note',text:SNAP?Math.round(SNAP*100)+' cm':'aus'});
  mg.oninput=()=>{SNAP=+mg.value/100;localStorage.setItem(MKEY,SNAP);mgv.textContent=SNAP?mg.value+' cm':'aus'};
  bar.append(h('button',{class:'btn',text:'Speichern',onclick:save,disabled:dirty()&&!cl.length?null:'disabled',title:cl.length?'erst die rot markierten Anschlüsse lösen':null}),h('button',{class:'btn2',text:'Verwerfen',onclick:discard}),h('label',{style:'margin-left:.6rem'},'Einbau ',ps),
   h('label',{style:'margin-left:.6rem',title:'Fangradius: so nah muss ein passender freier Anschluss sein, damit das Teil einrastet'},'Magnet ',mg,' ',mgv),
   h('span',{class:'note',style:'margin-left:.6rem',text:'Klick auf ein Teil der Palette, dann in die Wand klicken. R drehen, Q/E schwenken, A/D kippen, T spiegeln, W/Shift+W in sich drehen (um den Anschluss), Rohrende ziehen oder +/− = Länge, Pfeile 1 cm (Shift 1 mm), Bild↑/↓ Tiefe, Entf löschen, Strg+D duplizieren, Alt+Ziehen = einzeln. Leitung: Klick auf die gewählte Leitung = Knickpunkt (ziehen, Doppelklick entfernt).'}),h('div',{id:'insterr',style:'color:#C62828'}),
   cl.length?h('div',{style:'color:#C62828'},cl.map(c=>h('div',{text:'Nicht verbunden: '+c.part+'.'+c.port+' ↔ '+c.other+' – '+c.why}))):null);
  // with a placed part selected only catalog parts that fit one of its free ports are offered (the rest grey)
  const chosen=!carry&&last?last.own.find(p=>p.id===cur):null,openPorts=chosen?chosen.ports.filter(q=>!q.connected_to):[];
  const fits=c=>!chosen||(c.ports||[]).some(a=>openPorts.some(b=>compatible(a,b)));
  if(chosen)pal.append(h('div',{class:'note',style:'width:100%',text:openPorts.length?'Nur Teile, die an einen freien Anschluss von '+chosen.id+' passen (grau = passt nicht). Esc = Auswahl aufheben, alle Teile.'
   :'Teil '+chosen.id+' hat keinen freien Anschluss – Esc = Auswahl aufheben, alle Teile.'}),newGroupBtn());else if(carry)pal.appendChild(newGroupBtn());
  const btn=c=>{const ok=fits(c);return h('button',{class:'instbtn'+(carry&&carry.component===c.ref?' on':''),
   disabled:ok?null:'disabled',style:ok?null:'opacity:.4;cursor:not-allowed',
   title:c.ref+(c.estimated?' (Platzhalter)':'')+(ok?'':' – passt an keinen freien Anschluss des gewählten Teils'),onclick:()=>{pick(c)}},swatch(c.color),' '+(c.group_name?c.group_name+(c.shape==='box'?'':' '+c.variant_key):c.name||c.ref))};
  // tab Baum = configurable TGA trees (only suited objects and assemblies), tab Katalog = derived palette tree
  pal.appendChild(InstallTree.tabs(()=>buildBar(w)));
  pal.appendChild(InstallTree.tab()==='tree'?InstallTree.render({trees:inst().trees,cat,btn,fits,chosen:!!chosen,place,pick})
   :tree(btn,fits,!!chosen));pal.scrollTop=palTop}
// palette tree (Gewerk > System/Größe > Gruppe): <details> nodes, open state per browser; a part may sit in several nodes
const TKEY='weingaerten.waende.paltree';let palTop=0;
const ROOT_ORDER=['Abwasser','Zuwasser','Elektro'];
// order: fixed roots, then by system name, larger DN first (HT DN 90 before HT DN 50), else alphabetical
function nodeKey(n){const m=/^(.*?)\s*DN\s*([\d.]+)$/.exec(n);const r=ROOT_ORDER.indexOf(n);return r>=0?[0,String(r),0]:m?[1,m[1],-(+m[2])]:[1,n,0]}
function byNode(a,b){const x=nodeKey(a),y=nodeKey(b);return x[0]-y[0]||x[1].localeCompare(y[1],'de')||x[2]-y[2]}
function tree(btn,fits,chosen){const root={kids:new Map(),items:[]};const node=path=>path.reduce((n,k)=>{if(!n.kids.has(k))n.kids.set(k,{kids:new Map(),items:[]});return n.kids.get(k)},root);
  (inst().palette_roots||[]).forEach(p=>node(p));(inst().catalog||[]).filter(c=>c.palette!==false).forEach(c=>(c.paths&&c.paths.length?c.paths:[[c.trade_name||c.trade||'Sonstiges',c.group||'Sonstiges']]).forEach(p=>node(p).items.push(c)));
  let open;try{open=new Set(JSON.parse(localStorage.getItem(TKEY)||'[]'))}catch(e){open=new Set()}
  const all=n=>{const s=new Set(n.items.map(c=>c.ref));n.kids.forEach(k=>all(k).forEach(r=>s.add(r)));return s};
  const fitting=n=>{let k=n.items.filter(fits).length;n.kids.forEach(x=>{k+=fitting(x)});return k};
  const render=(name,n,key)=>{const total=all(n).size,ok=chosen?fitting(n):total;
   const d=h('details',{},h('summary',{class:chosen&&!ok?'off':null},name+' ',h('span',{class:'cnt',text:'('+(chosen?ok+'/':'')+total+')'})));
   d.open=open.has(key)||(chosen&&ok>0);
   d.addEventListener('toggle',()=>{if(d.open)open.add(key);else open.delete(key);localStorage.setItem(TKEY,JSON.stringify([...open]))});
   [...n.kids.keys()].sort(byNode).forEach(k=>d.appendChild(render(k,n.kids.get(k),key+'/'+k)));
   if(n.items.length){const box=h('div',{class:'items'});n.items.slice().sort((a,b)=>(a.name||a.ref).localeCompare(b.name||b.ref,'de')).forEach(c=>box.appendChild(btn(c)));d.appendChild(box)}
   if(!total)d.appendChild(h('div',{class:'note items',text:'noch keine Teile'}));return d};
  const box=h('div',{class:'insttree'});[...root.kids.keys()].sort(byNode).forEach(k=>box.appendChild(render(k,root.kids.get(k),k)));return box}
 let pf={};
 function curGeo(){return last&&(last.own.find(p=>p.id===cur)||(carry&&carry.id===cur?geo(last.w,carry):null))}
 // one clamp per conductor (L, N, PE; L1-L3 for three-phase); the pole count decides how many cables the box takes
 function clampFields(g,s,ro){const cl=inst().clamps||[];const cur=r=>((g.clamps||[]).find(x=>x.role===r)||{}).clamp||'';
  const three=THREE.has(g.id)||(g.clamps||[]).some(x=>/^L\d$/.test(x.role));
  const set=(r,v)=>{const t=s||edit(g);const l=(t.clamps||[]).filter(x=>x.role!==r);if(v)l.push({role:r,clamp:v});l.sort((a,b)=>ROLES.indexOf(a.role)-ROLES.indexOf(b.role));
   if(l.length)t.clamps=l;else delete t.clamps;g.clamps=l;draw();buildPanel()};
  const opts=[['','– keine Klemme –']].concat(cl.map(x=>[x.ref,x.poles+'-polig: '+x.name]));
  const roles=three?['L1','L2','L3','N','PE']:['L','N','PE'];
  const out=roles.map(r=>{const e=sel(opts,cur(r));e.disabled=ro;e.onchange=()=>set(r,e.value);return field('Klemme '+r,e)});
  const all=sel([['','– alle Leiter –']].concat(opts.slice(1)),'');all.disabled=ro;
  all.onchange=()=>{if(!all.value)return;const t=s||edit(g);t.clamps=roles.map(r=>({role:r,clamp:all.value}));g.clamps=t.clamps;draw();buildPanel()};
  const tp=h('input',{type:'checkbox'});tp.checked=three;tp.disabled=ro;
  tp.onchange=()=>{const t=s||edit(g);if(tp.checked)THREE.add(g.id);else THREE.delete(g.id);delete t.clamps;g.clamps=[];draw();buildPanel()};
  const n=capacity(g),es=g.ports.filter(q=>q.cores).length;
  return [field('alle Leiter',all,'gleiche Klemme für jeden Leiter'),...out,field('Drehstrom',tp,'L1, L2, L3 statt L'),
   h('div',{class:'note',text:n==null?'Ohne Klemmen: alle '+es+' Kabeleinführungen offen.':'Aktive Kabeleinführungen: '+Math.min(n,es)+' von '+es+' (kleinste Klemme '+n+'-polig).'})]}
 function buildPanel(){const w=wall();panel.textContent='';pf={};const g=curGeo();panel.style.display=g?'block':'none';if(w)buildBar(w);if(!g){drawSection(null);return}
  const s=carry&&carry.id===cur?carry:null;const ro=!on;const num_=(v,step)=>{const i=inp(v,{type:'number',step:step||'0.1'});i.disabled=ro;return i};
  const c=cat(g.component)||{};const [fa,fb]=faceRange(w,view),m=mirrorOf(w,view);
  pf={L:num_(),Z:num_(),T:num_(),N:num_('', '1'),P:num_('', '15'),K:num_('', '15'),Q:num_('', '15'),F:h('input',{type:'checkbox'})};pf.F.disabled=ro;
  const upd=(k,fn)=>{pf[k].oninput=pf[k].onchange=()=>{const t=s||edit(g);fn(t);autoAlign(w,t,[t]);draw()}};
  upd('L',t=>{if(pf.L.value!=='')t.u=r4(m?fb-tom(+pf.L.value):fa+tom(+pf.L.value))});upd('Z',t=>{if(pf.Z.value!=='')t.z=tom(+pf.Z.value)});
  upd('T',t=>{if(pf.T.value!=='')t.depth=tom(+pf.T.value)});
  // the length is taken only when valid (1 cm .. max); while typing an invalid value it is marked red
  pf.N.oninput=pf.N.onchange=()=>{const t=s||edit(g),v=tom(+pf.N.value),max=c.stretch?c.stretch.max_length:0;
   const bad=pf.N.value===''||!(v>=0.01&&v<=max+1e-9);msg(pf.N,bad?'1 bis '+num(cmv(max))+' cm':'');if(!bad){t.length=v;draw()}};
  const bent=c.shape==='cable'&&g.path&&g.path.length;if(bent)pf.N.disabled=true;
  upd('P',t=>{t.rot=Object.assign({},t.rot,{plane:+pf.P.value||0})});upd('K',t=>{t.rot=Object.assign({},t.rot,{tilt:+pf.K.value||0})});
  upd('Q',t=>{t.rot=Object.assign({},t.rot,{turn:+pf.Q.value||0})});upd('F',t=>{t.rot=Object.assign({},t.rot,{flip:pf.F.checked})});
  const fields=[field('Abstand links cm',pf.L,'Ursprung des Teils, wie in der Ansicht'),field('Höhe cm',pf.Z,'über Geschossboden'),field('Tiefe cm',pf.T,'+ vor der Wand, − in der Wand')];
  // grouped parts (NYM-J, NYY-J, Abzweigkasten Aufputz): one palette entry, the variant is chosen here
  const rep=c.variant_group&&(inst().catalog||[]).find(x=>x.variants&&x.variant_group===c.variant_group);
  if(rep){const v=rep.variants.find(x=>x.ref===c.ref)||rep.variants.find(x=>x.key===c.variant_key);
   const vs=sel(rep.variants.map(x=>[x.ref,rep.group_name+' '+x.label]),v?v.ref:'');vs.disabled=ro;
   vs.onchange=()=>{(s||edit(g)).component=vs.value;draw();buildPanel()};fields.unshift(field('Ausführung',vs,c.shape==='cable'?'Adern × Querschnitt':'Größe'))}
  if(c.stretch)fields.push(field('Länge cm',pf.N,bent?'Summe der Stücke ('+(g.path.length-1)+' Knickpunkte) – Enden und Knickpunkte ziehen':c.shape==='cable'?'gerade, max. '+num(cmv(c.stretch.max_length))+' cm – Klick auf die gewählte Leitung = Knickpunkt':'gerade, abgeschnitten, max. '+num(cmv(c.stretch.max_length))+' cm – oder Rohrende ziehen, +/− Taste'));
  fields.push(field('Drehung °',pf.P,'in der Wandebene (R)'),field('Kippen °',pf.K,'um die Waagerechte (A/D)'),field('Schwenken °',pf.Q,'um die Senkrechte (Q/E)'),field('gespiegelt',pf.F,'T'));
  if(c.trade==='water_supply'){const md=sel([['cold_water','Kaltwasser'],['hot_water','Warmwasser'],['circulation','Zirkulation']],g.medium||c.medium||'cold_water');md.disabled=ro;
   md.onchange=()=>{(s||edit(g)).medium=md.value;draw()};fields.push(field('Medium',md))}
  if(c.trade==='electrical'&&c.shape==='cable'){const ci=inp(g.circuit||'');ci.disabled=ro;ci.oninput=()=>{(s||edit(g)).circuit=ci.value||undefined};
   fields.push(field('Stromkreis',ci))}
  if(c.trade==='electrical'&&c.shape==='pipe'){const cs=sel([['','– kein Kabel –']].concat((inst().cables||[]).map(x=>[x.ref,x.name])),g.cable||'');cs.disabled=ro;
   cs.onchange=()=>{const t=s||edit(g);if(cs.value)t.cable=cs.value;else delete t.cable};const ci=inp(g.circuit||'');ci.disabled=ro;ci.oninput=()=>{(s||edit(g)).circuit=ci.value||undefined};
   fields.push(field('Kabel',cs),field('Stromkreis',ci))}
  if(c.trade==='electrical'&&c.shape==='box')fields.push(...clampFields(g,s,ro));
  const ports=h('table',{class:'insttab'},h('tr',{},['Anschluss','Status','an'].map(x=>h('th',{text:x}))),g.ports.map(q=>h('tr',{},h('td',{},h('span',{style:'color:'+PORT[q.status]},'● '),q.id+' '+portText(q)),
   h('td',{text:STATUS_DE[q.status]+(q.transfer&&q.status!=='connected'?' '+TRANSFER_DE[q.transfer]:'')}),h('td',{text:q.connected_to||'–'}))));
  const btns=on&&!s?h('div',{style:'display:flex;gap:.5rem;margin-top:.4rem'},h('button',{class:'btn2',text:'Löschen',onclick:()=>remove(g.id)}),h('button',{class:'btn2',text:'Duplizieren',onclick:()=>duplicate(edit(g))})):null;
  panel.append(h('h3',{style:'margin-top:0',text:(s?'Neues Teil: ':'Teil '+g.id+': ')+(c.name||g.component)}),h('div',{class:'note',text:layerText(w,faceOf(w),g)+(c.estimated?' · Platzhalter, Werte geschätzt':'')}),
   ro?h('div',{class:'note',style:'color:#1C69D4',text:'Nur Ansicht – zum Ändern oben „Installation bearbeiten“ klicken.'}):null,...fields,ports,btns,
   h('p',{class:'note',text:s?'In die Wand klicken zum Ablegen; in der Nähe eines passenden Anschlusses (5 cm) rastet das Teil ein. Esc = abbrechen.':'Rechtsklick auf einen Anschluss: bewusst offen, trennen, im Nachbarraum weiterbauen.'}));
  fill()}
 function fill(){const g=curGeo();if(!g||!pf.L)return;const w=wall();const [fa,fb]=faceRange(w,view),m=mirrorOf(w,view);const a=document.activeElement;
  const set=(k,v)=>{if(a!==pf[k])pf[k].value=v};set('L',cmv(m?fb-g.u:g.u-fa));set('Z',cmv(g.z));set('T',cmv(g.depth));if(g.length!=null)set('N',cmv(g.length));
  const r=g.rot||{};set('P',r.plane||0);set('K',r.tilt||0);set('Q',r.turn||0);pf.F.checked=!!r.flip;drawSection(g)}
 // wall section at the selected part: room | face | layers | other face; click or drag sets the depth (snaps to layer lines)
 function drawSection(g){sec.textContent='';const w=wall();if(!g||!w){sec.style.display='none';return}sec.style.display='block';
  const f=faceOf(w),first=['outside','left'].includes(f),Wd=Math.max(sec.clientWidth||600,300),front=0.15,sc=(Wd-40)/(w.thickness+front+0.05);
  const X=d=>20+(front-d)*sc;sec.setAttribute('viewBox','0 0 '+Wd+' 70');
  (w.layers||[]).forEach(l=>{const d0=first?-l.offset:-(w.thickness-l.offset-l.thickness),d1=d0-l.thickness;
   const rc=sv('rect',{x:X(d0),y:15,width:(d0-d1)*sc,height:35,fill:((H.materials[l.material]||{}).appearance||{}).color||'#ccc',stroke:'#555'});
   rc.addEventListener('pointermove',ev=>showTip(ev,[(H.materials[l.material]||{}).name||l.material,num(cmv(l.thickness))+' cm']));rc.addEventListener('pointerleave',hideTip);sec.appendChild(rc)});
  const t=sv('text',{x:4,y:11,'font-size':10,fill:'#555'});t.textContent='Raum (vor der Wand) ← Wandseite → in der Wand';sec.appendChild(t);
  const ds=[];g.legs.forEach(l=>l.forEach(P=>ds.push(proj(w,f,P).dep)));if(!ds.length)ds.push(proj(w,f,g.origin).dep);const r=(g.outer_diameter||0)/2;
  const lo=Math.min(...ds)-r,hi=Math.max(...ds)+r;sec.appendChild(sv('rect',{x:X(hi),y:22,width:Math.max(2,(hi-lo)*sc),height:21,fill:g.color,'fill-opacity':.8,stroke:'#1C69D4'}));
  sec.appendChild(sv('line',{x1:X(0),y1:8,x2:X(0),y2:58,stroke:'#000','stroke-width':2}));
  const d=proj(w,f,g.origin).dep;sec.appendChild(sv('line',{x1:X(d),y1:5,x2:X(d),y2:62,stroke:'#C62828','stroke-width':2}));
  const lab=sv('text',{x:X(d)+4,y:66,'font-size':10,fill:'#C62828'});lab.textContent=num(cmv(d))+' cm';sec.appendChild(lab);
  if(!on)return;const stops=[0,-w.thickness];(w.layers||[]).forEach(l=>{const d0=first?-l.offset:-(w.thickness-l.offset-l.thickness);stops.push(d0,d0-l.thickness,d0-l.thickness/2)});
  const setDepth=ev=>{const q=new DOMPoint(ev.clientX,ev.clientY).matrixTransform(sec.getScreenCTM().inverse());let v=front-(q.x-20)/sc;
   const near=stops.map(s=>[Math.abs(X(s)-q.x),s]).sort((a,b)=>a[0]-b[0])[0];if(near&&near[0]<6)v=near[1]-(near[1]<0?r:0);const tgt=carry&&carry.id===cur?carry:edit(g);
   tgt.depth=r4(Math.round(v*1000)/1000);draw()};
  sec.onpointerdown=ev=>{sec.setPointerCapture(ev.pointerId);setDepth(ev);sec.onpointermove=setDepth};sec.onpointerup=()=>{sec.onpointermove=null}}
 function table(w){tab.textContent='';const s=last&&last.w===w?last:null;if(!s)return;const [fa,fb]=faceRange(w,view),m=mirrorOf(w,view);
  if(!s.own.length){tab.appendChild(h('tr',{},h('td',{class:'note',text:'Keine Einbauteile auf dieser Wandseite.'+(s.ghosts.length?' '+s.ghosts.length+' auf der anderen Seite (blass).':'')})));return}
  tab.appendChild(h('tr',{},['Teil','Komponente','Abstand links','Höhe','Tiefe','Länge','offen'].map(x=>h('th',{text:x}))));
  s.own.forEach(p=>{const tr=h('tr',{style:'cursor:pointer'+(cur===p.id?';background:#F2F7FD':'')},h('td',{text:p.id+(buf&&buf.has(p.id)?' *':'')}),h('td',{text:p.component_name||p.component}),
   h('td',{class:'n',text:num(cmv(m?fb-p.u:p.u-fa))}),h('td',{class:'n',text:num(cmv(p.z))}),h('td',{class:'n',text:num(cmv(p.depth))}),
   h('td',{class:'n',text:p.length!=null?num(cmv(p.length)):''}),h('td',{class:'n',text:String(p.ports.filter(q=>q.status==='open').length)}));
   tr.onclick=()=>{cur=p.id;buildPanel();draw()};tab.appendChild(tr)})}
 // panel inputs keep their focus while typing: then only the values are refreshed
 function after(w){if(panel.contains(document.activeElement)){buildBar(w);fill()}else buildPanel();table(w)}
 function reset(){if(dirty()&&!confirm('Änderungen an Einbauteilen verwerfen?'))return false;buf=null;dels=new Set();carry=null;cur=null;on=false;menu.style.display='none';return true}
 document.addEventListener('pointerdown',ev=>{if(!menu.contains(ev.target))menu.style.display='none'});
 // ?part=<id>: show that part (its face) selected
 if(urlPart){const p=(inst().parts||[]).find(x=>x.id===urlPart);if(p&&p.host){cur=p.id;const exterior=(ST.walls.find(x=>x.id===p.host.wall)||{}).category==='exterior_wall';
  const v=(exterior?p.host.face==='outside':p.host.face==='left')?'outside':'inside';const r=document.querySelector('input[name=wview][value='+v+']');if(r){r.checked=true;view=v}}}
 return {drawParts,after,reset,dirty,on:()=>on}})();
draw();
