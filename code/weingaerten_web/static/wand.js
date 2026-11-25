// /waende: wall view of one face with its openings, zoom, wall list and table, edit mode for openings and floors.
let D=JSON.parse(document.getElementById('wanddata').textContent);
const EN=D.enums;const el=r=>D.elements[r]||{};
const col=r=>((el(r).appearance||{}).color)||'#cccccc';
let H=D.house;
// every storey's walls are listed; the storey of the selected wall is ST (used by the opening API)
const storeys=()=>(H.storeys||[]).slice().sort((a,b)=>(a.elevation||0)-(b.elevation||0));
const storeyOf=id=>{const q=StoreyPick.of(H),all=storeys();return (q&&q.walls.some(w=>w.id===id)?q:all.find(s=>(s.walls||[]).some(w=>w.id===id)))};
const hashId=decodeURIComponent(location.hash.slice(1));
let ST=storeyOf(hashId)||StoreyPick.of(H)||{walls:[]};
// view mode by default; edit mode buffers the wall's openings in `edits` until Speichern / Abbrechen
let view='outside',wallId=ST.walls.some(w=>w.id===hashId)?hashId:(ST.walls[0]||{}).id,curSel=null,work=null,editing=false,edits=null;
const svg=document.getElementById('wallsvg'),panel=document.getElementById('oppanel'),list=document.getElementById('wallist'),otab=document.getElementById('optable');
const wall=()=>ST.walls.find(w=>w.id===wallId)||ST.walls[0];
const comps=()=>Object.keys(D.elements).filter(r=>r.startsWith('component:')&&el(r).opening_capable&&['window','door','passage'].includes(el(el(r).class).geometry));
const compGeo=r=>el(el(r).class).geometry;const compP=r=>el(r).params||{};
const colorOf=r=>role=>col((el(r).materials||{})[role]);
function rough(o){const p=compP(o.component),j=o.joint==null?0.01:o.joint;return {u0:o.offset,u1:o.offset+(+p.width||0)+2*j,zb:o.sill,zt:o.sill+(+p.height||0)+2*j}}
function faceRange(w,v){const r=w.u_range[v==='outside'?'outside':'inside']||w.u_range.left;return [Math.min(...r),Math.max(...r)]}
function allowed(w){const a=faceRange(w,'outside'),b=faceRange(w,'inside');return [Math.max(a[0],b[0]),Math.min(a[1],b[1])]}
function mirrorOf(w,v){const a=w.direction*Math.PI/180,d=[Math.cos(a),Math.sin(a)],n=w.normal_in;const f=v==='outside'?n:[-n[0],-n[1]];const r=[-f[1],f[0]];return r[0]*d[0]+r[1]*d[1]<0}
const plain=o=>({id:o.id,component:o.component,offset:o.offset,sill:o.sill,joint:o.joint==null?0.01:o.joint,inset:o.inset==null?0.1:o.inset,reveal_material:o.reveal_material||undefined});
function opsOf(w){return editing&&edits?edits:(w.openings||[]).map(plain)}
const same=(a,b)=>['id','component','offset','sill','joint','inset','reveal_material'].every(k=>a[k]===b[k]);
// pending changes of the edited wall against the server state: ids to delete, openings to save
function changes(){if(!editing||!edits)return {dels:[],saves:[]};const orig=(wall().openings||[]).map(plain);
 const keep=new Set(edits.filter(o=>!o._new).map(o=>o.id));
 return {dels:orig.filter(o=>!keep.has(o.id)).map(o=>o.id),saves:edits.filter(o=>o._new||!same(o,orig.find(x=>x.id===o.id)))}}
const dirty=()=>{const c=changes();return c.dels.length+c.saves.length>0};
function topAt(w,u){const p=w.profile||[[0,w.height],[1,w.height]];if(u<=p[0][0])return p[0][1];
 for(let i=1;i<p.length;i++)if(u<=p[i][0]){const a=p[i-1],b=p[i];return b[0]-a[0]<1e-9?b[1]:a[1]+(b[1]-a[1])*(u-a[0])/(b[0]-a[0])}return p[p.length-1][1]}
function minTop(w,a,b){return Math.min(topAt(w,a),topAt(w,b),...(w.profile||[]).filter(p=>p[0]>a&&p[0]<b).map(p=>p[1]))}
// zones where other walls of the storey abut this wall: u range along the wall, z range, side (outside = low normal side)
function joins(w){const a=w.direction*Math.PI/180,d=[Math.cos(a),Math.sin(a)],n=w.normal_in,s=w.start,E=1e-3;
 const pr=p=>[(p[0]-s[0])*d[0]+(p[1]-s[1])*d[1],(p[0]-s[0])*n[0]+(p[1]-s[1])*n[1]];
 const box=fp=>{const q=fp.map(pr);return {u0:Math.min(...q.map(p=>p[0])),u1:Math.max(...q.map(p=>p[0])),t0:Math.min(...q.map(p=>p[1])),t1:Math.max(...q.map(p=>p[1]))}};
 const me=box(w.footprint);const out=[];
 (ST.walls||[]).forEach(x=>{if(x.id===w.id||!x.footprint)return;const b=box(x.footprint);
  if(b.t1<me.t0-E||b.t0>me.t1+E||b.u1<me.u0-E||b.u0>me.u1+E)return;
  const zb=Math.max(0,(x.z0||0)-(w.z0||0)),zt=Math.min(w.height,(x.z1==null?w.height:x.z1-(w.z0||0)));if(zt-zb<E)return;
  const corner=b.t0<me.t1-E&&b.t1>me.t0+E;  // corner/end inside this wall's thickness: both faces
  [['outside',corner||b.t0<me.t0-E],['inside',corner||b.t1>me.t1+E]].forEach(([side,on])=>{if(!on)return;const [fa,fb]=faceRange(w,side);
   const u0=Math.max(b.u0,fa),u1=Math.min(b.u1,fb);if(u1-u0>E)out.push({id:x.id,name:x.name||x.id,side,u0,u1,zb,zt,corner})})});
 return out}
function problems(w,o){const out=[];const r=rough(o),[a,b]=allowed(w);const p=compP(o.component);
 if(r.u0<a-1e-4||r.u1>b+1e-4)out.push('Öffnung ragt über die Wand');if(r.zt>minTop(w,r.u0,r.u1)+1e-4)out.push('Öffnung höher als die Wand');
 if(r.zb<0)out.push('Brüstung < 0');if((o.inset==null?0.1:o.inset)+(+p.depth||0)>w.thickness+1e-4)out.push('Bauteil tiefer als die Wand');
 joins(w).forEach(q=>{if(Math.min(r.u1,q.u1)-Math.max(r.u0,q.u0)>1e-4&&Math.min(r.zt,q.zt)-Math.max(r.zb,q.zb)>1e-4)out.push('Öffnung im Anschluss von '+q.name)});
 opsOf(w).forEach(x=>{if(x.id===o.id)return;const q=rough(x);const ov=Math.max(0,Math.min(r.u1,q.u1)-Math.max(r.u0,q.u0))*Math.max(0,Math.min(r.zt,q.zt)-Math.max(r.zb,q.zb));if(ov>1e-4)out.push('Überlappt mit '+x.id)});
 return out}
let S=100,PADL=40,PADT=30;
// zoom of the wall view, only in the edit modes (openings or installation): 1 = fitted to the width
const ZOOMS=[1,1.5,2,3,4,6,8];let ZOOM=1;
const zwrap=h('div',{id:'wzoomwrap',style:'overflow:auto;max-height:80vh'});svg.parentNode.insertBefore(zwrap,svg);zwrap.appendChild(svg);
const zlab=h('span',{class:'note',style:'min-width:3.5em;display:inline-block;text-align:center'});
const zbar=h('div',{id:'wzoombar',style:'display:none;gap:.4rem;align-items:center;margin:.3rem 0'},
 h('button',{class:'btn2',text:'−',title:'verkleinern (Strg+Mausrad)',onclick:()=>zoomStep(-1)}),zlab,
 h('button',{class:'btn2',text:'+',title:'vergrößern (Strg+Mausrad)',onclick:()=>zoomStep(1)}),
 h('button',{class:'btn2',text:'Einpassen',onclick:()=>setZoom(1)}),h('span',{class:'note',text:'Zoom: Strg+Mausrad um den Mauszeiger'}));
zwrap.parentNode.insertBefore(zbar,zwrap);
// arrows around the view: neighbour walls on the shown face (left / right as seen; one arrow each), ceiling above
// (not implemented yet), the room in front of the face below (only faces that bound a room, i.e. inside views)
const navTop=h('div',{id:'wnavtop',class:'wnav'}),navBot=h('div',{id:'wnavbot',class:'wnav'});zwrap.parentNode.insertBefore(navTop,zwrap);zwrap.after(navBot);
const navBtn=(text,title,fn)=>h('button',{class:'btn2',text,title,disabled:fn?null:'disabled',onclick:fn||null});
function drawNav(w){navTop.textContent='';navBot.textContent='';const [fa,fb]=faceRange(w,view),m=mirrorOf(w,view),L=new Map(),R=new Map();
 // left as seen: low u unless the view is mirrored
 joins(w).filter(q=>q.side===view).forEach(q=>(((q.u0+q.u1)/2<(fa+fb)/2)!==m?L:R).set(q.id,q.name));
 // walls at the two wall ends (corners lie outside the shorter face, so the face joins miss them)
 const a=w.direction*Math.PI/180,d=[Math.cos(a),Math.sin(a)],n=w.normal_in,s0=w.start,E=0.02,pr=p=>[(p[0]-s0[0])*d[0]+(p[1]-s0[1])*d[1],(p[0]-s0[0])*n[0]+(p[1]-s0[1])*n[1]];
 const box=fp=>{const q=fp.map(pr);return [Math.min(...q.map(p=>p[0])),Math.max(...q.map(p=>p[0])),Math.min(...q.map(p=>p[1])),Math.max(...q.map(p=>p[1]))]},me=box(w.footprint);
 (ST.walls||[]).forEach(x=>{if(x.id===w.id||!x.footprint)return;const b=box(x.footprint);if(b[3]<me[2]-E||b[2]>me[3]+E||b[1]<me[0]-E||b[0]>me[1]+E)return;
  if(b[0]<me[0]+w.thickness+E)(m?R:L).set(x.id,x.name||x.id);else if(b[1]>me[1]-w.thickness-E)(m?L:R).set(x.id,x.name||x.id)});
 const side=w.faces[view==='outside'?'outside':'inside']?view:'left',rooms=(ST.rooms||[]).filter(r=>(r.faces||[]).some(f=>f.wall===w.id&&f.side===side));
 navTop.append(h('span',{},[...L].map(([id,n])=>navBtn('◀ '+n,'zur angrenzenden Wand '+n,()=>pickWall(id)))),navBtn('▲ Decke','Decke – noch nicht implementiert',null),
  h('span',{},[...R].map(([id,n])=>navBtn(n+' ▶','zur angrenzenden Wand '+n,()=>pickWall(id)))));
 rooms.forEach(r=>navBot.appendChild(navBtn('▼ '+((r.number?r.number+' ':'')+r.name),'Raum auf der Seite Räume öffnen',()=>{location.href='/raeume?storey='+encodeURIComponent(ST.id)+'#'+encodeURIComponent(r.id)})))}
const zoomable=()=>editing||!!(window.InstallUI&&InstallUI.on());
// keeps the point under (cx, cy) of the scroll box in place
function setZoom(z,cx,cy){z=Math.max(1,Math.min(8,z));if(z===ZOOM)return;const r=zwrap.getBoundingClientRect();
 const px=cx==null?zwrap.clientWidth/2:cx-r.left,py=cy==null?zwrap.clientHeight/2:cy-r.top;
 const fx=(zwrap.scrollLeft+px)/Math.max(1,zwrap.scrollWidth),fy=(zwrap.scrollTop+py)/Math.max(1,zwrap.scrollHeight);
 ZOOM=z;draw();zwrap.scrollLeft=fx*zwrap.scrollWidth-px;zwrap.scrollTop=fy*zwrap.scrollHeight-py}
function zoomStep(d,cx,cy){const z=d>0?ZOOMS.find(x=>x>ZOOM+1e-9):ZOOMS.slice().reverse().find(x=>x<ZOOM-1e-9);if(z)setZoom(z,cx,cy)}
zwrap.addEventListener('wheel',ev=>{if(!ev.ctrlKey||!zoomable())return;ev.preventDefault();zoomStep(ev.deltaY<0?1:-1,ev.clientX,ev.clientY)},{passive:false});
function zoomUI(){const on=zoomable();if(!on&&ZOOM!==1){ZOOM=1}zbar.style.display=on?'flex':'none';zlab.textContent=Math.round(ZOOM*100)+' %'}
function sx(w,u){const [fa,fb]=faceRange(w,view);return PADL+(mirrorOf(w,view)?(fb-u):(u-fa))*S}
function sz(w,z){return PADT+(w.height-z)*S}
function draw(){const w=wall();if(!w){svg.textContent='';return}
 const [fa,fb]=faceRange(w,view);zoomUI();const width=zwrap.clientWidth||900;S=Math.min(120,(width-2*PADL)/(fb-fa))*ZOOM;
 const Wp=(fb-fa)*S+2*PADL,Hp=w.height*S+PADT+110;svg.setAttribute('viewBox','0 0 '+Wp+' '+Hp);
 if(ZOOM===1){svg.removeAttribute('width');svg.style.width='';svg.setAttribute('height',Hp*(width/Wp))}else{svg.setAttribute('width',Wp);svg.style.width=Wp+'px';svg.setAttribute('height',Hp)}svg.textContent='';
 const face=w.faces[view==='outside'?'outside':'inside']||w.faces.left;
 document.getElementById('wedit').href='/grundriss?storey='+encodeURIComponent(ST.id)+'#'+encodeURIComponent(w.id);document.getElementById('wtitle').textContent=(w.name||w.id)+' – '+(view==='outside'?'Außenansicht':'Innenansicht')+' – Fläche '+num((fb-fa).toFixed(3))+' × '+num(w.height)+' m'+((w.profile||[]).some(p=>Math.abs(p[1]-w.height)>1e-6)?' (Giebel, max.)':'');
 svg.appendChild(sv('polygon',{points:[[fa,0],[fb,0],[fb,topAt(w,fb)],...(w.profile||[]).filter(p=>p[0]>fa&&p[0]<fb).reverse().map(p=>[p[0],p[1]]),[fa,topAt(w,fa)]]
  .map(p=>sx(w,p[0]).toFixed(1)+','+sz(w,p[1]).toFixed(1)).join(' '),fill:face.color||'#eee',stroke:'#333','stroke-width':1}));
 svg.appendChild(sv('line',{x1:PADL-20,y1:sz(w,0),x2:PADL+(fb-fa)*S+20,y2:sz(w,0),stroke:'#000','stroke-width':2}));
 const pts=new Set([fa,fb]);const defs=sv('defs',{}),pat=sv('pattern',{id:'wjoin',width:8,height:8,patternUnits:'userSpaceOnUse'});
 pat.appendChild(sv('rect',{width:8,height:8,fill:'#e6e6e6'}));[[2,0,2,8],[6,0,6,8],[0,2,8,2],[0,6,8,6]].forEach(l=>pat.appendChild(sv('line',{x1:l[0],y1:l[1],x2:l[2],y2:l[3],stroke:'#888','stroke-width':.8})));
 const pc=sv('pattern',{id:'wcorner',width:8,height:8,patternUnits:'userSpaceOnUse',patternTransform:'rotate(45)'});
 pc.appendChild(sv('rect',{width:8,height:8,fill:'#e6e6e6'}));pc.appendChild(sv('line',{x1:0,y1:0,x2:0,y2:8,stroke:'#888','stroke-width':1.6}));
 defs.append(pat,pc);svg.appendChild(defs);
 joins(w).filter(q=>q.side===view).forEach(q=>{const x0=Math.min(sx(w,q.u0),sx(w,q.u1)),x1=Math.max(sx(w,q.u0),sx(w,q.u1));const zt=Math.min(q.zt,minTop(w,q.u0,q.u1));
  const r=sv('rect',{x:x0,y:sz(w,zt),width:x1-x0,height:(zt-q.zb)*S,fill:q.corner?'url(#wcorner)':'url(#wjoin)','data-join':q.corner?'corner':'joint',stroke:'#666','stroke-width':1});
  const info=q.corner?['Ecke mit '+q.name,'Gehört zu: '+(w.name||w.id)+' (Wandende, Gehrung)','Nachbarwand '+q.name+' stößt auf der Gehrungslinie an']
   :['Anschluss '+q.name,'Gehört zu: '+(w.name||w.id)+' (Fläche hinter der Nachbarwand)',q.name+' stößt hier an die '+(view==='outside'?'Außen':'Innen')+'seite'];
  info.push('Bereich '+num(cmv(Math.abs(q.u1-q.u0)))+' cm breit, Höhe '+num(cmv(zt-q.zb))+' cm','Hier keine Fenster/Türen');
  r.addEventListener('pointermove',ev=>showTip(ev,info));r.addEventListener('pointerleave',hideTip);svg.appendChild(r);pts.add(q.u0);pts.add(q.u1)});
 if(window.LiningUI)LiningUI.drawAreas(w,pts);
 drawHeating(w);
 const ops=opsOf(w);
 ops.forEach(o=>{const r=rough(o);const x0=Math.min(sx(w,r.u0),sx(w,r.u1)),x1=Math.max(sx(w,r.u0),sx(w,r.u1));const y0=sz(w,r.zt),y1=sz(w,r.zb);
  const pr=problems(w,o);const isSel=curSel===o.id;const j=(o.joint==null?0.01:o.joint)*S;
  const g=sv('g',{'data-id':o.id,style:editing?'cursor:move':'cursor:pointer'});
  g.appendChild(sv('rect',{x:x0,y:y0,width:x1-x0,height:y1-y0,fill:'#fff',stroke:pr.length?'#C62828':(isSel?'#1C69D4':'#333'),'stroke-width':isSel||pr.length?2.5:1,
   'stroke-dasharray':o._new?'6 4':'none'}));
  const fg=sv('g',{});drawFront(fg,compGeo(o.component),compP(o.component),colorOf(o.component),x0+j,y0+j,S,mirrorOf(w,view));g.appendChild(fg);
  if(pr.length)g.appendChild(sv('rect',{x:x0,y:y0,width:x1-x0,height:y1-y0,fill:'rgba(198,40,40,.18)'}));
  const t=sv('text',{x:(x0+x1)/2,y:y0-6,'text-anchor':'middle','font-size':12,fill:'#1C69D4'});t.textContent=o.id;g.appendChild(t);
  const t2=sv('text',{x:x1+4,y:(y0+y1)/2,'font-size':10,fill:'#555'});t2.textContent='BRH '+num(cmv(o.sill))+' / H '+num(cmv(r.zt-r.zb));g.appendChild(t2);
  g.addEventListener('pointerdown',ev=>startDrag(ev,o));svg.appendChild(g);pts.add(r.u0);pts.add(r.u1)});
 if(window.InstallUI)InstallUI.drawParts(w,pts);
 const P=[...pts].sort((a,b)=>sx(w,a)-sx(w,b));const yy=sz(w,0)+40;
 P.forEach(u=>svg.appendChild(sv('line',{x1:sx(w,u),y1:yy-6,x2:sx(w,u),y2:yy+6,stroke:'#1C69D4'})));
 for(let i=0;i<P.length-1;i++){const a=sx(w,P[i]),b=sx(w,P[i+1]);svg.appendChild(sv('line',{x1:a,y1:yy,x2:b,y2:yy,stroke:'#1C69D4'}));
  const t=sv('text',{x:(a+b)/2,y:yy-4,'text-anchor':'middle','font-size':11,fill:'#1C69D4'});t.textContent=num(cmv(Math.abs(P[i+1]-P[i])));svg.appendChild(t)}
 const t=sv('text',{x:PADL,y:yy+28,'font-size':11,fill:'#777'});t.textContent='Maße in cm, '+(mirrorOf(w,view)?'Blick: Wandende links':'Blick: Wandanfang links');svg.appendChild(t);
 drawList();drawTable();modeButtons();drawNav(w);if(window.LiningUI)LiningUI.table(w);if(window.InstallUI)InstallUI.after(w)}
let drag=null;
// wall heating panels (storey.wall_heating) whose field lies on the shown face of this wall
function drawHeating(w){const x=ST.wall_heating;if(!x)return;const a=w.direction*Math.PI/180,d=[Math.cos(a),Math.sin(a)],n=w.normal_in;
 const f=view==='outside'?n:[-n[0],-n[1]],dot=(p,q)=>p[0]*q[0]+p[1]*q[1],len=Math.hypot(w.end[0]-w.start[0],w.end[1]-w.start[1]);
 x.fields.forEach(fl=>{if(dot(fl.normal,f)>-0.99)return;const rel=[fl.origin[0]-w.start[0],fl.origin[1]-w.start[1]];
  if(Math.abs(dot(rel,n))>w.thickness+0.05)return;const wu=u=>dot([rel[0]+fl.direction[0]*u,rel[1]+fl.direction[1]*u],d);
  const c=x.circuits.find(k=>k.id===fl.circuit)||{};
  fl.panels.forEach(p=>{const u0=Math.min(wu(p.u0),wu(p.u1)),u1=Math.max(wu(p.u0),wu(p.u1));if(u1<-0.01||u0>len+0.01)return;
   const X0=Math.min(sx(w,u0),sx(w,u1)),X1=Math.max(sx(w,u0),sx(w,u1)),Y0=sz(w,p.z1),Y1=sz(w,p.z0);const g=sv('g',{'data-heat':fl.id});
   g.appendChild(sv('rect',{x:X0,y:Y0,width:X1-X0,height:Y1-Y0,fill:'rgba(201,180,138,.55)',stroke:'#FF7A00','stroke-width':1.2}));
   const t=sv('text',{x:(X0+X1)/2,y:(Y0+Y1)/2+5,'text-anchor':'middle','font-size':Math.max(10,Math.min(18,S*0.18)),fill:'#A04A00'});t.textContent=p.type;g.appendChild(t);
   const info=['Wandheizung: Platte Typ '+p.type+' ('+(p.name||p.component)+')',(c.name||fl.circuit)+' – '+(fl.name||fl.id),
    num(cmv(p.width))+' × '+num(cmv(p.height))+' cm, Unterkante '+num(cmv(p.z0))+' cm'];
   g.addEventListener('pointermove',ev=>showTip(ev,info));g.addEventListener('pointerleave',hideTip);svg.appendChild(g)});
  const pu=wu(fl.port.u);if(pu>=-0.01&&pu<=len+0.01){const z=Math.min(...fl.panels.map(p=>p.z0));
   svg.appendChild(sv('polygon',{points:[[sx(w,pu)-6,sz(w,z)+12],[sx(w,pu)+6,sz(w,z)+12],[sx(w,pu),sz(w,z)]].map(q=>q.join(',')).join(' '),fill:'#E040FB'}))}})}
function startDrag(ev,o){ev.preventDefault();if(curSel!==o.id)select(o.id);if(!editing||!work)return;const w=wall();
 drag={x:ev.clientX,y:ev.clientY,off:work.offset,sill:work.sill,k:(svg.viewBox.baseVal.width/svg.clientWidth)/S,m:mirrorOf(w,view)?-1:1};cap(ev)}
svg.addEventListener('pointermove',ev=>{if(!drag||!work)return;const du=(ev.clientX-drag.x)*drag.k*drag.m,dz=-(ev.clientY-drag.y)*drag.k;
 work.offset=Math.round((drag.off+du)*100)/100;if(!(['door','passage'].includes(compGeo(work.component))&&drag.sill===0))work.sill=Math.max(0,Math.round((drag.sill+dz)*100)/100);fillPanel();draw()});
svg.addEventListener('pointerup',()=>{drag=null});
document.addEventListener('keydown',ev=>{if(!work||['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName))return;const st=ev.shiftKey?0.1:0.01;const m=mirrorOf(wall(),view)?-1:1;
 if(ev.key==='ArrowLeft')work.offset-=st*m;else if(ev.key==='ArrowRight')work.offset+=st*m;else if(ev.key==='ArrowUp')work.sill+=st;else if(ev.key==='ArrowDown')work.sill=Math.max(0,work.sill-st);else return;
 work.offset=Math.round(work.offset*100)/100;work.sill=Math.round(work.sill*100)/100;ev.preventDefault();fillPanel();draw()});
function confirmDiscard(){return !dirty()||confirm('Änderungen verwerfen?')}
let saving=false;
// view mode: a click only highlights; edit mode: the opening of `edits` goes into the panel
function select(id){curSel=id;work=editing&&edits?edits.find(x=>x.id===id)||null:null;buildPanel();draw();return true}
function modeButtons(){const show=(id,on)=>{document.getElementById(id).style.display=on?'':'none'};
 show('wedmode',!editing);show('opnew',editing);show('opsave',editing);show('wcancel',editing);
 const c=changes(),bad=editing&&edits?edits.some(o=>problems(wall(),o).length):false;const sb=document.getElementById('opsave');sb.disabled=saving||bad||!(c.dels.length+c.saves.length);sb.textContent=saving?'Speichert …':'Speichern und zurück'}
function startEdit(){const w=wall();if(!w)return;editing=true;edits=(w.openings||[]).map(plain);select(curSel)}
function stopEdit(){editing=false;ZOOM=1;edits=null;work=null;saveErr.textContent='';buildPanel();draw()}
function cancelEdit(){if(!confirmDiscard())return;stopEdit()}
const saveErr=h('div',{id:'wsaveerr',style:'color:#C62828;margin:.4rem 0'});document.getElementById('katdetail').prepend(saveErr);
// deletes first, then saves one by one; on an error the rest stays pending in edit mode
function saveEdit(){const w=wall();saveErr.textContent='';const err=t=>saveErr.appendChild(h('div',{text:t}));
 const ids=edits.map(o=>o.id);const others=new Set(ST.walls.filter(x=>x.id!==w.id).flatMap(x=>(x.openings||[]).map(o=>o.id)));
 const bad=edits.filter(o=>!/^[a-z0-9]+(-[a-z0-9]+)*$/.test(o.id)||ids.indexOf(o.id)!==ids.lastIndexOf(o.id)||(o._new&&others.has(o.id)));
 if(bad.length){bad.forEach(o=>err('id ungültig oder doppelt: '+o.id+' (nur a–z, 0–9 und -)'));return}
 const c=changes();const steps=c.dels.map(id=>()=>post('/api/opening/delete',{storey:ST.id,wall:w.id,id}).then(r=>[r,id]))
  .concat(c.saves.map(o=>()=>{const b={id:o.id,component:o.component,offset:o.offset,sill:o.sill,joint:o.joint,inset:o.inset};if(o.reveal_material)b.reveal_material=o.reveal_material;
   return post('/api/opening/save',{storey:ST.id,wall:w.id,opening:b,create:!!o._new}).then(r=>[r,o.id])}));
 const n=steps.length;const run=i=>i>=n?Promise.resolve(true):steps[i]().then(([{ok,j},id])=>{if(!ok){err(id+':');(j.errors||[j.error]).forEach(t=>err(t));return false}
  const o=edits.find(x=>x.id===id);if(o)delete o._new;return run(i+1)});
 saving=true;modeButtons();
 run(0).catch(e=>{err(String(e));return false}).then(done=>reload(done,done?'Gespeichert: '+n+' Änderung'+(n===1?'':'en'):null))}
function newOpening(){if(!editing)return;const w=wall();const C=comps();if(!C.length){alert('Kein Bauteil „für Öffnungen geeignet“ im Katalog.');return}
 const ids=new Set(ST.walls.filter(x=>x.id!==w.id).flatMap(x=>(x.openings||[]).map(o=>o.id)).concat(edits.map(o=>o.id)));let n=1;while(ids.has('o-'+n))n++;
 const comp=C.find(r=>compGeo(r)==='window')||C[0];const p=compP(comp);const rw=(+p.width)+0.02;
 const [a,b]=allowed(w);const occ=edits.map(o=>{const r=rough(o);return [r.u0,r.u1]}).sort((x,y)=>x[0]-y[0]);let best=[a,b],cur=a,bestLen=-1;
 occ.concat([[b,b]]).forEach(([u0,u1])=>{if(u0-cur>bestLen){bestLen=u0-cur;best=[cur,u0]}cur=Math.max(cur,u1)});
 const off=Math.round(((best[0]+best[1])/2-rw/2)*100)/100;const plaster=Object.keys(D.elements).find(r=>r==='material:interior-plaster');
 work={id:'o-'+n,component:comp,offset:off,sill:['door','passage'].includes(compGeo(comp))?0:0.9,joint:0.01,inset:0.1,reveal_material:plaster,_new:true};
 edits.push(work);curSel=work.id;buildPanel();draw()}
let pf={};
function buildPanel(){panel.style.display=work?'block':'none';panel.textContent='';if(!work)return;const w=wall();pf={};
 panel.appendChild(h('h3',{text:work._new?'Neue Öffnung':'Öffnung '+work.id,style:'margin-top:0'}));
 const C=comps();const groups={};C.forEach(r=>{const c=el(el(r).class).name||el(r).class;(groups[c]=groups[c]||[]).push(r)});
 const cs=h('select',{});Object.keys(groups).forEach(gn=>{const og=h('optgroup',{label:gn});groups[gn].forEach(r=>og.appendChild(h('option',{value:r,text:el(r).name||r})));cs.appendChild(og)});
 if(!C.includes(work.component))cs.appendChild(h('option',{value:work.component,text:(el(work.component).name||work.component)+' (nicht geeignet)'}));cs.value=work.component;
 const prev=h('span',{});const upPrev=()=>{prev.textContent='';prev.appendChild(frontSVG(compGeo(cs.value),compP(cs.value),colorOf(cs.value),60,50))};upPrev();
 const id=inp(work.id);id.disabled=!work._new;
 const L=inp('',{type:'number',step:'0.1'}),R=inp('',{type:'number',step:'0.1'}),B=inp('',{type:'number',step:'0.1',min:'0'}),J=inp('',{type:'number',step:'0.1',min:'0'}),I=inp('',{type:'number',step:'0.1',min:'0'});
 const M=Object.keys(D.elements).filter(r=>r.startsWith('material:')).sort((a,b)=>(el(a).name||a).localeCompare(el(b).name||b));
 const rv=sel([['','– keine –']].concat(M.map(r=>[r,el(r).name||r])),work.reveal_material||'');
 pf={L,R,B,J,I};const ch=()=>draw();
 cs.onchange=()=>{work.component=cs.value;upPrev();fillPanel();ch()};
 L.oninput=()=>{if(L.value==='')return;const v=tom(+L.value);const [fa,fb]=faceRange(w,view);const r=rough(work);const rw=r.u1-r.u0;
  work.offset=Math.round((mirrorOf(w,view)?fb-v-rw:fa+v)*10000)/10000;fillPanel('L');ch()};
 R.oninput=()=>{if(R.value==='')return;const v=tom(+R.value);const [fa,fb]=faceRange(w,view);const r=rough(work);const rw=r.u1-r.u0;
  work.offset=Math.round((mirrorOf(w,view)?fa+v:fb-v-rw)*10000)/10000;fillPanel('R');ch()};
 B.oninput=()=>{if(B.value!==''){work.sill=tom(+B.value);ch()}};J.oninput=()=>{if(J.value!==''){work.joint=tom(+J.value);fillPanel('J');ch()}};I.oninput=()=>{if(I.value!==''){work.inset=tom(+I.value);ch()}};
 rv.onchange=()=>{work.reveal_material=rv.value||undefined;draw()};id.oninput=()=>{work.id=id.value.trim();curSel=work.id;draw()};
 const probs=h('div',{id:'opprobs',style:'color:#C62828;margin:.4rem 0'});
 // removal is only buffered; Speichern in the header deletes it on the server
 const del=h('button',{class:'btn2',text:'Löschen',onclick:()=>{edits=edits.filter(o=>o!==work);work=null;curSel=null;buildPanel();draw()}});
 panel.append(field('Bauteil',h('span',{style:'display:flex;gap:8px;align-items:center'},cs,prev)),field('id',id),field('Abstand links cm',L,'wie in der aktuellen Ansicht'),field('Abstand rechts cm',R),
  field('Brüstung cm',B,'Unterkante Rohbauöffnung über Geschossboden'),field('Fuge cm',J),field('Einbautiefe cm',I,'von der Außenseite'),field('Laibung',rv),probs,
  h('div',{style:'display:flex;gap:.5rem'},del),h('p',{class:'note',text:'Ziehen mit der Maus oder Pfeiltasten (1 cm, mit Shift 10 cm). Übernehmen mit Speichern oben.'}));
 fillPanel()}
function fillPanel(skip){if(!work||!pf.L)return;const w=wall();const [fa,fb]=faceRange(w,view);const r=rough(work);const m=mirrorOf(w,view);
 const left=m?fb-r.u1:r.u0-fa,right=m?r.u0-fa:fb-r.u1;
 if(skip!=='L')pf.L.value=cmv(left);if(skip!=='R')pf.R.value=cmv(right);if(document.activeElement!==pf.B)pf.B.value=cmv(work.sill);
 if(skip!=='J'&&document.activeElement!==pf.J)pf.J.value=cmv(work.joint);if(document.activeElement!==pf.I)pf.I.value=cmv(work.inset);
 const pr=problems(w,work);const box=document.getElementById('opprobs');if(box){box.textContent='';pr.forEach(t=>box.appendChild(h('div',{text:t})))}}
const FK='weingaerten.waende.storey',floorSel=document.getElementById('wfloor'),wsearch=document.getElementById('wsearch');
function fillFloors(){const keep=floorSel.value||localStorage.getItem(FK)||'';floorSel.textContent='';
 floorSel.appendChild(h('option',{value:'',text:'Alle Geschosse'}));storeys().forEach(s=>floorSel.appendChild(h('option',{value:s.id,text:s.name||s.id})));
 floorSel.value=storeys().some(s=>s.id===keep)?keep:''}
function drawList(){list.textContent='';const cw=wall();document.getElementById('katname').textContent=cw?(cw.name||cw.id)+' – '+(ST.name||ST.id):'';
 const f=floorSel.value,q=wsearch.value.trim().toLowerCase();let n=0,tot=0;
 storeys().forEach(s=>(s.walls||[]).forEach(w=>{tot++;if(f&&s.id!==f)return;if(q&&!((w.name||'')+' '+w.id+' '+(s.name||'')).toLowerCase().includes(q))return;n++;
  const c=h('div',{class:'wcard'+(w.id===wallId&&s===ST?' on':''),'data-wall':w.id},h('b',{text:w.name||w.id}),
   h('div',{class:'note',text:(s.name||s.id)+' · '+num(w.length)+' m · '+(w.openings||[]).length+' Öffnungen'}));
  c.onclick=()=>pickWall(w.id,s);list.appendChild(c)}));
 document.getElementById('katcount').textContent=(n===tot?tot:n+' von '+tot)+' Wände';
 if(!n)list.appendChild(h('p',{class:'note',style:'padding:0 8px',text:'Keine Wand passt zum Filter.'}));
 const on=list.querySelector('.wcard.on');if(on)on.scrollIntoView({block:'nearest'})}
function pickWall(id,s){s=s||storeyOf(id);if(!s||(id===wallId&&s===ST)||!confirmDiscard()||(window.InstallUI&&!InstallUI.reset()))return;ST=s;wallId=id;
 history.replaceState(null,'','?storey='+encodeURIComponent(s.id)+(new URLSearchParams(location.search).get('embed')?'&embed=1':'')+'#'+encodeURIComponent(id));
 editing=false;edits=null;work=null;curSel=null;ZOOM=1;saveErr.textContent='';if(window.LiningUI)LiningUI.reset();buildPanel();draw()}
function drawTable(){const w=wall();otab.textContent='';otab.appendChild(h('tr',{},['Id','Bauteil','Abstand links','Breite','Brüstung','Höhe','Laibung',''].map(x=>h('th',{text:x}))));
 const [fa,fb]=faceRange(w,view);const m=mirrorOf(w,view);
 opsOf(w).forEach(o=>{const r=rough(o);const tr=h('tr',{style:'cursor:pointer'+(curSel===o.id?';background:#F2F7FD':'')},h('td',{text:o.id}),h('td',{text:el(o.component).name||o.component}),
  h('td',{class:'n',text:num(cmv(m?fb-r.u1:r.u0-fa))}),h('td',{class:'n',text:num(cmv(r.u1-r.u0))}),h('td',{class:'n',text:num(cmv(o.sill))}),h('td',{class:'n',text:num(cmv(r.zt-r.zb))}),
  h('td',{text:o.reveal_material?(el(o.reveal_material).name||o.reveal_material):'–'}),h('td',{},o._new?h('span',{class:'note',text:'neu'}):h('a',{href:'/haus3d#'+encodeURIComponent(o.id),text:'in 3D zeigen'})));
  tr.onclick=ev=>{if(ev.target.tagName!=='A')select(o.id)};otab.appendChild(tr)})}
// done: all changes saved -> back to view mode; otherwise stay in edit mode, the diff is recomputed against the new state
function reload(done,msgText){fetch('/api/house',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'}).then(r=>r.json()).finally(()=>{saving=false}).then(j=>{H=j;ST=(H.storeys||[]).find(s=>s.id===ST.id)||StoreyPick.of(H);
 if(done){editing=false;edits=null;work=null}select(curSel);if(msgText)toast(msgText)})}
document.getElementById('opnew').onclick=newOpening;document.getElementById('wedmode').onclick=startEdit;
document.getElementById('opsave').onclick=saveEdit;document.getElementById('wcancel').onclick=cancelEdit;
fillFloors();floorSel.onchange=()=>{localStorage.setItem(FK,floorSel.value);drawList()};wsearch.oninput=drawList;
document.querySelectorAll('input[name=wview]').forEach(r=>r.onchange=()=>{view=r.value;ZOOM=1;if(window.LiningUI)LiningUI.reset();fillPanel();draw()});
window.addEventListener('resize',draw);window.addEventListener('beforeunload',ev=>{if(dirty()||(window.LiningUI&&LiningUI.dirty())||(window.InstallUI&&InstallUI.dirty())){ev.preventDefault();ev.returnValue=''}});
WaendeLayout.init();new ResizeObserver(()=>draw()).observe(document.getElementById('katdetail'));
window.addEventListener('hashchange',()=>pickWall(decodeURIComponent(location.hash.slice(1))));
draw();
