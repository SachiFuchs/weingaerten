// Katalog – TGA: Darstellungs-Editor (simplified view in the wall plane: shapes rect/circle/line/text + Anschlusspunkte).
const KatTgaDraw=(()=>{
const NS='http://www.w3.org/2000/svg',GRID=0.01,SNAP=0.001;
const TOOLS={select:'Auswahl',rect:'Rechteck',circle:'Kreis',line:'Linie',text:'Text',cable:'Kabel',port:'Anschlusspunkt'};
const DIRS={'-1,0,0':'links','1,0,0':'rechts','0,1,0':'oben','0,-1,0':'unten','0,0,1':'vorne (aus der Wand)','0,0,-1':'hinten (in die Wand)'};
const ANGLE={'':'Standard (Leitung beliebig, sonst rechtwinklig)',right:'nur rechtwinklig (Rohr in Rohr)',any:'beliebiger Winkel (Leitungen)'};
const LINES={ht:'HT',kg:'KG',ppr:'PP-R',conduit:'Leerrohr',insert:'Einsatz',power:'Kabelende'};
const GEND={spigot:'Spitzende',socket:'Muffe',any:'beliebig'};
const TRADES={electrical:'Elektro',waste_water:'Abwasser',water_supply:'Zuwasser'};
const SHAPES={box:'Dose',insert:'Einsatz',fitting:'Formteil',valve:'Ventil',cap:'Kappe',pipe:'Rohr'};
let st={};
const r4=v=>Math.round(v*1e4)/1e4,snap=v=>Math.round(v/SNAP)*SNAP,mm=v=>v==null?'':String(Math.round(v*10000)/10).replace('.',',');
const fromMm=s=>{const t=String(s).trim().replace(',','.');return t===''?null:+t/1000};
// cable: smooth curve (Catmull-Rom) through end a, bend points, end b; ends follow the ports (from/to), cached in `ends`
function portXY(id){const q=(st.e.install.ports||[]).find(p=>p.id===id);return q?[q.pos[0],q.pos[1]]:null}
function cablePts(f){const a=portXY(f.from)||(f.ends||[])[0],b=portXY(f.to)||(f.ends||[])[1];return a&&b?[a,...(f.points||[]),b]:null}
function curve(P){if(P.length<3)return 'M'+P.map(p=>p.join(' ')).join(' L');let d='M'+P[0].join(' ');
 for(let i=0;i<P.length-1;i++){const p0=P[i-1]||P[i],p1=P[i],p2=P[i+1],p3=P[i+2]||p2;
  d+=' C'+[p1[0]+(p2[0]-p0[0])/6,p1[1]+(p2[1]-p0[1])/6,p2[0]-(p3[0]-p1[0])/6,p2[1]-(p3[1]-p1[1])/6,p2[0],p2[1]].map(r4).join(' ')}return d}
function syncEnds(){shapes().forEach(f=>{if(f.kind!=='cable')return;const a=portXY(f.from),b=portXY(f.to);if(a&&b)f.ends=[a,b]})}
// index where a new bend point at (x,y) belongs: nearest segment of the control polygon
function bendIndex(P,x,y){let best=0,bd=1e9;for(let i=0;i<P.length-1;i++){const [ax,ay]=P[i],[bx,by]=P[i+1],L=(bx-ax)**2+(by-ay)**2;
  const t=L?Math.max(0,Math.min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/L)):0,d=Math.hypot(ax+t*(bx-ax)-x,ay+t*(by-ay)-y);if(d<bd){bd=d;best=i}}return best}
let keysOn=false;
function keys(){if(keysOn)return;keysOn=true;document.addEventListener('keydown',ev=>{
  if(!st.box||!st.box.isConnected||!st.editable||!st.pick)return;const a=document.activeElement;if(a&&/INPUT|SELECT|TEXTAREA/.test(a.tagName))return;
  if(ev.key==='Escape'){st.pick=null;st.cableFrom=null;draw();return}
  if(ev.key==='Delete'||ev.key==='Backspace'){ev.preventDefault();remove();return}
  const d={ArrowLeft:[-1,0],ArrowRight:[1,0],ArrowUp:[0,1],ArrowDown:[0,-1]}[ev.key];if(!d)return;ev.preventDefault();
  const s=ev.shiftKey?GRID:SNAP;move(d[0]*s,d[1]*s,snapshot());changed();draw()})}
// remove the selected shape / port / bend point
function remove(){const p=st.pick;if(!p)return;
 if(p.t==='shape')shapes().splice(p.i,1);
 else if(p.t==='bend'){shapes()[p.i].points.splice(p.j,1);st.pick={t:'shape',i:p.i};changed();draw();return}
 else{const ps=st.e.install.ports;if(ps.length<2)return;const id=ps[p.i].id,used=shapes().filter(f=>f.kind==='cable'&&(f.from===id||f.to===id));
  if(used.length&&!confirm('Anschlusspunkt „'+id+'“ wird von '+used.length+' Kabel(n) benutzt – Kabel mitlöschen?'))return;
  ps.splice(p.i,1);used.forEach(f=>shapes().splice(shapes().indexOf(f),1))}
 st.pick=null;changed();draw()}
// position snapshot of the selection and a mover applying an offset to it
function snapshot(){const p=st.pick;if(p.t==='port')return st.e.install.ports[p.i].pos.slice();const f=shapes()[p.i];
 if(p.t==='bend')return f.points[p.j].slice();return {x:f.x,y:f.y,x2:f.x2,y2:f.y2,points:(f.points||[]).map(q=>q.slice())}}
function move(dx,dy,o){const p=st.pick;if(p.t==='port'){const q=st.e.install.ports[p.i];q.pos=[r4(o[0]+dx),r4(o[1]+dy),q.pos[2]];return}
 const f=shapes()[p.i];if(p.t==='bend'){f.points[p.j]=[r4(o[0]+dx),r4(o[1]+dy)];return}
 if(f.kind==='cable'){f.points=o.points.map(q=>[r4(q[0]+dx),r4(q[1]+dy)]);return}
 f.x=r4(o.x+dx);f.y=r4(o.y+dy);if(f.kind==='line'){f.x2=r4(o.x2+dx);f.y2=r4(o.y2+dy)}}
function sv(tag,a){const e=document.createElementNS(NS,tag);for(const k in a||{})if(a[k]!=null)e.setAttribute(k,a[k]);return e}
// render(box, element, editable, onChange): draws into box; onChange() marks the form dirty
function render(box,e,editable,onChange){st={box,e,editable,onChange:onChange||(()=>{}),tool:'select',pick:null,cableFrom:null,zoom:st.zoom||2500};box.textContent='';keys();
 box.style.display='block';box.style.overflow='auto';
 if(!e||!String(e.class||'').startsWith('tga-class:')||e.abstract||e.assembly){box.appendChild(h('p',{class:'note',text:e&&e.assembly?'Baugruppe – Darstellung kommt vom Hauptobjekt.':e&&e.abstract?'Abstraktes Objekt (veraltet) – Darstellung kommt vom konkreten Bauteil.':'Darstellung nur für TGA-Bauteile.'}));return}
 if(!e.install){box.appendChild(h('p',{class:'note',text:'Keine Einbaudaten (Darstellung, Anschlusspunkte).'}));
  if(editable){const tr=sel(Object.entries(TRADES),'electrical'),sh=sel(Object.entries(SHAPES),'box');
   box.append(h('span',{style:'display:inline-flex;gap:6px;align-items:center'},'Gewerk',tr,'Form',sh,h('button',{class:'btn2',text:'Darstellung anlegen',onclick:()=>{
    e.install={trade:tr.value,shape:sh.value,size:[0.07,0.07,0.04],ports:[{id:'a',pos:[0,0.035,-0.02],dir:[0,1,0],line:'power',dn:3,gender:'any'}]};st.onChange();render(box,e,editable,onChange)}})))}
  return}
 draw()}
function shapes(){const l=st.e.install.layout=st.e.install.layout||{};l.shapes=l.shapes||[];return l.shapes}
function changed(){syncEnds();const l=st.e.install.layout;if(l&&l.shapes&&!l.shapes.length)delete l.shapes;if(l&&!Object.keys(l).length)delete st.e.install.layout;st.onChange()}
function extent(){const xs=[0.1,-0.1],ys=[0.1,-0.1],s=st.e.install.size;if(s){xs.push(s[0]/2,-s[0]/2);ys.push(s[1]/2,-s[1]/2)}
 ((st.e.install.layout||{}).shapes||[]).forEach(f=>{if(f.kind==='cable'){(cablePts(f)||[]).forEach(q=>{xs.push(q[0]);ys.push(q[1])});return}
  xs.push(f.x+(f.w||f.r||0),f.x-(f.w||f.r||0),f.x2||f.x);ys.push(f.y+(f.h||f.r||0),f.y-(f.h||f.r||0),f.y2||f.y)});
 (st.e.install.ports||[]).forEach(p=>{xs.push(p.pos[0]);ys.push(p.pos[1])});
 const m=Math.max(...xs.map(Math.abs),...ys.map(Math.abs))+0.02;return m}
function draw(){const {box,e,editable}=st;box.textContent='';
 const bar=h('div',{style:'display:flex;gap:4px;flex-wrap:wrap;align-items:center;margin-bottom:4px'},h('b',{text:'Darstellung'}));
 if(editable)Object.entries(TOOLS).forEach(([k,l])=>bar.appendChild(h('button',{class:'btn2',text:l,style:st.tool===k?'border-color:#1C69D4;font-weight:bold':null,onclick:()=>{st.tool=k;st.cableFrom=null;draw()}})));
 bar.appendChild(h('span',{class:'note',text:editable?(st.tool==='cable'?(st.cableFrom?' Kabel: zweiten Anschlusspunkt anklicken (Esc = abbrechen)':' Kabel: ersten Anschlusspunkt anklicken'):' Anklicken = auswählen, Ziehen = zeichnen/verschieben, Entf = löschen, Pfeiltasten = 1 mm (Shift 1 cm), Kabel: Klick auf Kurve = Biegepunkt, Doppelklick = entfernen, Mausrad = Zoom'):' (Ansicht in der Wandebene, Mausrad = Zoom)'}));
 const m=st.dragM||extent(),px=Math.round(2*m*st.zoom);
 const svg=sv('svg',{width:px,height:px,viewBox:[-m,-m,2*m,2*m].join(' '),style:'background:#fff;border:1px solid #ddd;touch-action:none;flex:none'});
 st.svg=svg;st.m=m;
 const g=sv('g',{transform:'scale(1,-1)'});svg.appendChild(g);
 for(let v=Math.ceil(-m/GRID)*GRID;v<=m;v+=GRID){const major=Math.abs(Math.round(v*100)%10)===0,c=major?'#E0E0E0':'#F2F2F2';
  g.append(sv('line',{x1:v,y1:-m,x2:v,y2:m,stroke:c,'stroke-width':m/400}),sv('line',{x1:-m,y1:v,x2:m,y2:v,stroke:c,'stroke-width':m/400}))}
 g.append(sv('line',{x1:-m,y1:0,x2:m,y2:0,stroke:'#BDBDBD','stroke-width':m/300}),sv('line',{x1:0,y1:-m,x2:0,y2:m,stroke:'#BDBDBD','stroke-width':m/300}));
 const s=e.install.size;if(s)g.appendChild(sv('rect',{x:-s[0]/2,y:-s[1]/2,width:s[0],height:s[1],fill:'none',stroke:'#90A4AE','stroke-dasharray':m/50,'stroke-width':m/250}));
 const sw=m/200,hit=m/40,HL='#1C69D4';
 // areas (rect/circle) below, thin elements (line/cable/text) on top so they stay clickable
 const all=(e.install.layout||{}).shapes||[],order=all.map((f,i)=>i).sort((a,b)=>(/rect|circle/.test(all[a].kind)?0:1)-(/rect|circle/.test(all[b].kind)?0:1)||a-b);
 order.forEach(i=>{const f=all[i],on=st.pick&&(st.pick.t==='shape'||st.pick.t==='bend')&&st.pick.i===i,stroke=on?HL:(f.stroke||'#455A64'),fill=f.fill||'none',w=on?sw*2.5:sw;
  const n=sv('g',{'data-shape':i,style:'cursor:'+(editable?'move':'pointer')+';pointer-events:all'});
  if(f.kind==='rect')n.appendChild(sv('rect',{x:f.x-(f.w||0)/2,y:f.y-(f.h||0)/2,width:f.w||0,height:f.h||0,fill,stroke,'stroke-width':w,'pointer-events':'all'}));
  else if(f.kind==='circle')n.appendChild(sv('circle',{cx:f.x,cy:f.y,r:f.r||0,fill,stroke,'stroke-width':w,'pointer-events':'all'}));
  else if(f.kind==='line')n.append(sv('line',{x1:f.x,y1:f.y,x2:f.x2,y2:f.y2,stroke:'transparent','stroke-width':hit}),sv('line',{x1:f.x,y1:f.y,x2:f.x2,y2:f.y2,stroke,'stroke-width':w*1.5}));
  else if(f.kind==='cable'){const P=cablePts(f);if(!P)return;const d=curve(P);
   n.append(sv('path',{d,fill:'none',stroke:'transparent','stroke-width':hit,'data-curve':i}),sv('path',{d,fill:'none',stroke,'stroke-width':Math.max(w*2,f.width||0),'stroke-linecap':'round','pointer-events':'none'}))}
  else{const t=sv('text',{x:f.x,y:-f.y,transform:'scale(1,-1)','font-size':f.size||0.01,fill:stroke,'text-anchor':'middle','dominant-baseline':'middle','font-weight':on?'bold':null});t.textContent=f.text||'T';n.appendChild(t)}
  g.appendChild(n)});
 const pk=st.pick,sf=pk&&(pk.t==='shape'||pk.t==='bend')?shapes()[pk.i]:null;
 if(sf){const hs=m/70,handle=(x,y,k,round)=>g.appendChild(round?sv('circle',{cx:x,cy:y,r:hs*0.7,fill:'#fff',stroke:HL,'stroke-width':sw,'data-handle':k,style:'cursor:crosshair'})
   :sv('rect',{x:x-hs/2,y:y-hs/2,width:hs,height:hs,fill:'#fff',stroke:HL,'stroke-width':sw,'data-handle':k,style:'cursor:nwse-resize'}));
  const box=(x0,y0,x1,y1)=>g.appendChild(sv('rect',{x:Math.min(x0,x1)-hs/2,y:Math.min(y0,y1)-hs/2,width:Math.abs(x1-x0)+hs,height:Math.abs(y1-y0)+hs,fill:'none',stroke:HL,'stroke-width':sw/2,'stroke-dasharray':m/80,'pointer-events':'none'}));
  if(sf.kind==='rect'){box(sf.x-sf.w/2,sf.y-sf.h/2,sf.x+sf.w/2,sf.y+sf.h/2);if(editable)[[-1,-1],[1,-1],[1,1],[-1,1]].forEach(([a,b])=>handle(sf.x+a*sf.w/2,sf.y+b*sf.h/2,'size'))}
  else if(sf.kind==='circle'){box(sf.x-sf.r,sf.y-sf.r,sf.x+sf.r,sf.y+sf.r);if(editable)handle(sf.x+sf.r,sf.y,'size')}
  else if(sf.kind==='line'){if(editable){handle(sf.x,sf.y,'p1');handle(sf.x2,sf.y2,'p2')}}
  else if(sf.kind==='cable'){(sf.points||[]).forEach((q,j)=>{const c=sv('circle',{cx:q[0],cy:q[1],r:hs*0.8,fill:pk.t==='bend'&&pk.j===j?HL:'#fff',stroke:HL,'stroke-width':sw,'data-bend':j,style:'cursor:move'});g.appendChild(c)})}
  else box(sf.x-(sf.size||0.01),sf.y-(sf.size||0.01)/2,sf.x+(sf.size||0.01),sf.y+(sf.size||0.01)/2)}
 (e.install.ports||[]).forEach((p,i)=>{const on=st.pick&&st.pick.t==='port'&&st.pick.i===i||st.cableFrom===p.id,c=on?'#1C69D4':'#C62828',[x,y]=p.pos,[dx,dy]=p.dir,L=m/8;
  const pg=sv('g',{'data-port':i,style:'cursor:'+(editable?'move':'pointer')});
  if(Math.abs(dx)+Math.abs(dy)>0.01)pg.append(sv('line',{x1:x,y1:y,x2:x+dx*L,y2:y+dy*L,stroke:c,'stroke-width':sw*1.5}),sv('circle',{cx:x+dx*L,cy:y+dy*L,r:m/120,fill:c}));
  else pg.append(sv('circle',{cx:x,cy:y,r:m/40,fill:'none',stroke:c,'stroke-width':sw}),sv(p.dir[2]>0?'circle':'line',p.dir[2]>0?{cx:x,cy:y,r:m/200,fill:c}:{x1:x-m/60,y1:y-m/60,x2:x+m/60,y2:y+m/60,stroke:c,'stroke-width':sw}));
  pg.append(sv('circle',{cx:x,cy:y,r:m/70,fill:c}),sv('circle',{cx:x,cy:y,r:m/30,fill:'transparent','pointer-events':'all'}));
  const t=sv('text',{x,y:-(y+m/30),transform:'scale(1,-1)','font-size':m/22,fill:c,'text-anchor':'middle'});t.textContent=p.id+(p.angle==='any'||(!p.angle&&p.line==='power')?' ∠':'');pg.appendChild(t);g.appendChild(pg)});
 svg.addEventListener('wheel',ev=>{ev.preventDefault();st.zoom=Math.max(500,Math.min(12000,st.zoom*(ev.deltaY<0?1.2:1/1.2)));draw()},{passive:false});
 mouse(svg,m);
 const props=h('div',{style:'min-width:260px;flex:1'});propPanel(props);
 box.append(bar,h('div',{style:'display:flex;gap:10px;align-items:flex-start'},svg,props))}
// pointer position in local m; always on the CURRENT svg (draw() replaces it while dragging)
function pt(svg,ev){const s=st.svg&&st.svg.isConnected?st.svg:svg,ctm=s.getScreenCTM();if(!ctm)return [0,0];
 const p=s.createSVGPoint();p.x=ev.clientX;p.y=ev.clientY;const q=p.matrixTransform(ctm.inverse());return [snap(q.x),snap(-q.y)]}
// own hit test in model coordinates (the browser's SVG hit test is unreliable at m-scale coordinates);
// returns {dataset:{handle|bend|port|shape}, curve} like the former DOM target, priority: handles, bends, ports, thin shapes, areas
function sample(P){if(P.length<3)return P;const q=[];for(let i=0;i<P.length-1;i++){const p0=P[i-1]||P[i],p1=P[i],p2=P[i+1],p3=P[i+2]||p2;
  for(let k=0;k<12;k++){const t=k/12,t2=t*t,t3=t2*t,c=j=>0.5*(2*p1[j]+(-p0[j]+p2[j])*t+(2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t2+(-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t3);q.push([c(0),c(1)])}}
 q.push(P[P.length-1]);return q}
function segDist(x,y,[ax,ay],[bx,by]){const L=(bx-ax)**2+(by-ay)**2,t=L?Math.max(0,Math.min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/L)):0;return Math.hypot(ax+t*(bx-ax)-x,ay+t*(by-ay)-y)}
function hitTest(x,y){const tol=7/st.zoom,all=(st.e.install.layout||{}).shapes||[],near=(a,b)=>Math.hypot(a-x,b-y)<=tol,pk=st.pick;
 const sf=pk&&(pk.t==='shape'||pk.t==='bend')?all[pk.i]:null;
 if(sf&&st.editable){if(sf.kind==='rect'&&[[-1,-1],[1,-1],[1,1],[-1,1]].some(([a,b])=>near(sf.x+a*sf.w/2,sf.y+b*sf.h/2)))return {dataset:{handle:'size'}};
  if(sf.kind==='circle'&&near(sf.x+sf.r,sf.y))return {dataset:{handle:'size'}};
  if(sf.kind==='line'){if(near(sf.x,sf.y))return {dataset:{handle:'p1'}};if(near(sf.x2,sf.y2))return {dataset:{handle:'p2'}}}}
 if(sf&&sf.kind==='cable'){const j=(sf.points||[]).findIndex(q=>near(q[0],q[1]));if(j>=0)return {dataset:{bend:j}}}
 const ps=st.e.install.ports||[];let best=-1,bd=1e9;ps.forEach((q,i)=>{const d=Math.hypot(q.pos[0]-x,q.pos[1]-y);if(d<=tol*1.5&&d<bd){bd=d;best=i}});
 if(best>=0)return {dataset:{port:best}};
 for(let i=all.length-1;i>=0;i--){const f=all[i];
  if(f.kind==='line'&&segDist(x,y,[f.x,f.y],[f.x2,f.y2])<=tol)return {dataset:{shape:i}};
  if(f.kind==='cable'){const P=cablePts(f);if(P){const s=sample(P);for(let k=0;k<s.length-1;k++)if(segDist(x,y,s[k],s[k+1])<=tol)return {dataset:{shape:i},curve:true}}}
  if(f.kind==='text'){const s=f.size||0.01,w=Math.max(s,(f.text||'T').length*s*0.6)/2;if(Math.abs(x-f.x)<=w+tol&&Math.abs(y-f.y)<=s/2+tol)return {dataset:{shape:i}}}}
 for(let i=all.length-1;i>=0;i--){const f=all[i];
  if(f.kind==='rect'&&Math.abs(x-f.x)<=f.w/2+tol&&Math.abs(y-f.y)<=f.h/2+tol)return {dataset:{shape:i}};
  if(f.kind==='circle'&&Math.hypot(x-f.x,y-f.y)<=f.r+tol)return {dataset:{shape:i}}}
 return null}
function mouse(svg,m){
 svg.addEventListener('dblclick',ev=>{if(!st.editable||!st.pick)return;const [x,y]=pt(svg,ev),b=hitTest(x,y);if(!b||b.dataset.bend==null)return;ev.preventDefault();
  shapes()[st.pick.i].points.splice(+b.dataset.bend,1);st.pick={t:'shape',i:st.pick.i};changed();draw()});
 svg.addEventListener('pointerdown',ev=>{ev.preventDefault();const [x,y]=pt(svg,ev),start=[x,y],t=hitTest(x,y);
  // cable tool: two clicks on ports
  if(st.editable&&st.tool==='cable'){const pp=t&&t.dataset.port!=null?st.e.install.ports[+t.dataset.port]:null;
   if(!pp){st.cableFrom=null;draw();return}
   if(!st.cableFrom||st.cableFrom===pp.id){st.cableFrom=pp.id;draw();return}
   shapes().push({kind:'cable',from:st.cableFrom,to:pp.id,points:[]});st.cableFrom=null;st.tool='select';st.pick={t:'shape',i:shapes().length-1};changed();draw();return}
  if(t&&t.dataset.handle&&st.editable){const f=shapes()[st.pick.i],k=t.dataset.handle;
   drag(svg,ev,(cx,cy)=>{if(k==='size'){if(f.kind==='rect'){f.w=r4(Math.max(SNAP,Math.abs(cx-f.x)*2));f.h=r4(Math.max(SNAP,Math.abs(cy-f.y)*2))}else f.r=r4(Math.max(SNAP,Math.hypot(cx-f.x,cy-f.y)))}
    else if(k==='p1'){f.x=cx;f.y=cy}else{f.x2=cx;f.y2=cy}});return}
  if(t&&t.dataset.bend!=null){st.pick={t:'bend',i:st.pick.i,j:+t.dataset.bend};if(!st.editable){draw();return}const o=snapshot();
   drag(svg,ev,(cx,cy)=>move(cx-start[0],cy-start[1],o));draw();return}
  if(t){const was=st.pick;st.pick=t.dataset.port!=null?{t:'port',i:+t.dataset.port}:{t:'shape',i:+t.dataset.shape};
   if(!st.editable){draw();return}
   const f=st.pick.t==='shape'?shapes()[st.pick.i]:null;
   // click on the curve of the already selected cable inserts a bend point there
   if(f&&f.kind==='cable'&&was&&was.i===st.pick.i&&(was.t==='shape'||was.t==='bend')&&t.curve){const P=cablePts(f);if(P){
    const j=bendIndex(P,x,y);f.points=f.points||[];f.points.splice(j,0,[x,y]);st.pick={t:'bend',i:st.pick.i,j};changed();const o=snapshot();
    drag(svg,ev,(cx,cy)=>move(cx-start[0],cy-start[1],o));draw();return}}
   const o=snapshot();drag(svg,ev,(cx,cy)=>move(cx-start[0],cy-start[1],o));draw();return}
  if(!st.editable||st.tool==='select'){st.pick=null;draw();return}
  if(st.tool==='port'){const ps=st.e.install.ports;let n=ps.length+1;while(ps.some(p=>p.id==='p'+n))n++;
   ps.push({id:'p'+n,pos:[x,y,0],dir:[0,1,0],line:st.e.install.trade==='electrical'?'conduit':'ht',dn:20,gender:'socket'});st.pick={t:'port',i:ps.length-1};changed();draw();return}
  const f={kind:st.tool,x,y};if(f.kind==='rect'){f.w=SNAP;f.h=SNAP}else if(f.kind==='circle')f.r=SNAP;else if(f.kind==='line'){f.x2=x;f.y2=y}else{f.text='Text';f.size=0.01}
  shapes().push(f);st.pick={t:'shape',i:shapes().length-1};
  drag(svg,null,(cx,cy)=>{if(f.kind==='rect'){f.w=r4(Math.max(SNAP,Math.abs(cx-x)*2));f.h=r4(Math.max(SNAP,Math.abs(cy-y)*2))}
   else if(f.kind==='circle')f.r=r4(Math.max(SNAP,Math.hypot(cx-x,cy-y)));else if(f.kind==='line'){f.x2=cx;f.y2=cy}})})}
// drag: view extent frozen until the pointer is released (no jumping), then redrawn to fit
// ev0: pointerdown event -> nothing moves before the pointer travelled 3 px (a plain click only selects)
function drag(svg,ev0,move){st.dragM=st.m;let live=!ev0,moved=!ev0;
 const mv=ev=>{ev.preventDefault();if(!live&&Math.hypot(ev.clientX-ev0.clientX,ev.clientY-ev0.clientY)<3)return;live=moved=true;const [x,y]=pt(svg,ev);move(x,y);draw()};
 const up=()=>{document.removeEventListener('pointermove',mv);document.removeEventListener('pointerup',up);st.dragM=null;if(moved)changed();draw()};
 document.addEventListener('pointermove',mv);document.addEventListener('pointerup',up)}
// list of all drawing elements: row click / Bearbeiten selects, Löschen removes; selected row highlighted
function elementList(){const {e,editable}=st,wrap=h('div',{style:'margin:6px 0;max-height:220px;overflow:auto;border:1px solid #ddd'});
 const t=h('table',{style:'width:100%;border-collapse:collapse;font-size:12px'});wrap.appendChild(t);
 const row=(pk,label,info)=>{const on=!!st.pick&&(pk.t==='port'?st.pick.t==='port':st.pick.t!=='port')&&st.pick.i===pk.i;
  const sel=()=>{st.pick=pk;st.cableFrom=null;draw()};
  const tr=h('tr',{style:'cursor:pointer;'+(on?'background:#E3EEFB;font-weight:bold':''),onclick:sel},h('td',{text:label}),h('td',{class:'note',text:info}),
   h('td',{style:'white-space:nowrap;text-align:right'},editable?h('button',{class:'btn2',text:on?'wird bearbeitet':'Bearbeiten',onclick:ev=>{ev.stopPropagation();sel()}}):null,
    editable?h('button',{class:'btn2',text:'Löschen',onclick:ev=>{ev.stopPropagation();st.pick=pk;remove()}}):null));t.appendChild(tr)};
 const pos=v=>mm(v[0])+' / '+mm(v[1]);
 ((e.install.layout||{}).shapes||[]).forEach((f,i)=>row({t:'shape',i},TOOLS[f.kind]||f.kind,
  f.kind==='cable'?f.from+' → '+f.to+', '+(f.points||[]).length+' Biegepunkte':f.kind==='text'?'„'+(f.text||'')+'“':f.kind==='line'?pos([f.x,f.y])+' → '+pos([f.x2,f.y2]):pos([f.x,f.y])));
 (e.install.ports||[]).forEach((q,i)=>row({t:'port',i},'Anschluss '+q.id,pos(q.pos)));
 if(!t.children.length)t.appendChild(h('tr',{},h('td',{class:'note',text:'keine Elemente'})));
 return h('div',{},h('b',{text:'Elemente'}),wrap)}
// property panel of the selected shape / port (lengths in mm)
function propPanel(box){const {e,editable}=st,ro=!editable;
 const num=(obj,k,label)=>{const i=inp(mm(obj[k]),{size:6,disabled:ro?'disabled':null});i.onchange=()=>{const v=fromMm(i.value);if(v==null)delete obj[k];else obj[k]=r4(v);changed();draw()};return field(label+' mm',i)};
 const txt=(obj,k,label)=>{const i=inp(obj[k]==null?'':obj[k],{disabled:ro?'disabled':null});i.onchange=()=>{if(i.value==='')delete obj[k];else obj[k]=i.value;changed();draw()};return field(label,i)};
 const pick=(obj,k,label,map,cast)=>{const s=sel(Object.entries(map),obj[k]==null?'':String(obj[k]));s.disabled=ro;s.onchange=()=>{if(s.value==='')delete obj[k];else obj[k]=cast?cast(s.value):s.value;changed();draw()};return field(label,s)};
 const size=e.install.size||[];const sz=h('span',{style:'display:inline-flex;gap:4px;align-items:center'});
 ['B','H','T'].forEach((l,j)=>{const i=inp(mm(size[j]),{size:5,disabled:ro?'disabled':null});i.onchange=()=>{const v=fromMm(i.value);const s=(e.install.size||[0.05,0.05,0.03]).slice();if(v>0)s[j]=r4(v);e.install.size=s;changed();draw()};sz.append(l,i)});
 box.append(field('Körper B × H × T',sz));
 box.appendChild(elementList());
 const p=st.pick;
 if(p&&p.t==='bend'&&!shapes()[p.i])st.pick=null;
 if(!p){box.appendChild(h('p',{class:'note',text:(e.install.ports||[]).length+' Anschlusspunkte, '+((e.install.layout||{}).shapes||[]).length+' Formen – zum Bearbeiten anklicken.'}));return}
 if(p.t==='shape'||p.t==='bend'){const f=shapes()[p.i];if(!f){st.pick=null;return}
  if(f.kind==='cable'){const ids=Object.fromEntries((e.install.ports||[]).map(q=>[q.id,q.id]));
   box.append(h('h4',{text:'Kabel'}),pick(f,'from','von Anschluss',ids),pick(f,'to','nach Anschluss',ids),
    h('p',{class:'note',text:(f.points||[]).length+' Biegepunkte – Klick auf die Kurve fügt einen ein, Doppelklick entfernt ihn.'}),
    num(f,'width','Strichstärke'),txt(f,'stroke','Farbe (#RRGGBB)'));
   if(p.t==='bend'){const q=f.points[p.j];if(q)box.append(h('h4',{text:'Biegepunkt '+(p.j+1)}),num(q,0,'x'),num(q,1,'y'))}
   if(editable)box.append(h('button',{class:'btn2',text:'Biegepunkte zurücksetzen',onclick:()=>{f.points=[];st.pick={t:'shape',i:p.i};changed();draw()}}),
    p.t==='bend'?h('button',{class:'btn2',text:'Biegepunkt löschen',onclick:remove}):null,h('button',{class:'btn2',text:'Kabel löschen',onclick:()=>{st.pick={t:'shape',i:p.i};remove()}}));
   return}
  box.append(h('h4',{text:TOOLS[f.kind]}),num(f,'x','x'),num(f,'y','y'));
  if(f.kind==='rect')box.append(num(f,'w','Breite'),num(f,'h','Höhe'));if(f.kind==='circle')box.append(num(f,'r','Radius'));
  if(f.kind==='line')box.append(num(f,'x2','x Ende'),num(f,'y2','y Ende'));if(f.kind==='text')box.append(txt(f,'text','Text'),num(f,'size','Schrifthöhe'));
  box.append(txt(f,'stroke','Linienfarbe (#RRGGBB)'),f.kind!=='line'&&f.kind!=='text'?txt(f,'fill','Füllung (#RRGGBB / none)'):null)}
 else{const q=e.install.ports[p.i];if(!q){st.pick=null;return}
  const pos=h('span',{style:'display:inline-flex;gap:4px;align-items:center'});
  ['x','y','Tiefe w'].forEach((l,j)=>{const i=inp(mm(q.pos[j]),{size:5,disabled:ro?'disabled':null});i.onchange=()=>{const v=fromMm(i.value);if(v!=null){q.pos[j]=r4(v);changed();draw()}};pos.append(l,i)});
  const dirKey=q.dir.join(','),dirs=Object.assign({},DIRS);if(!dirs[dirKey])dirs[dirKey]='frei ('+q.dir.map(v=>Math.round(v*100)/100).join(', ')+')';
  box.append(h('h4',{text:'Anschlusspunkt'}),txt(q,'id','id'),field('Lage mm',pos),
   pick(q,'dir','Richtung',dirs,v=>v.split(',').map(Number)),pick(q,'angle','Winkel',ANGLE),pick(q,'line','Leitungssystem',LINES),
   field('DN / Adern',(()=>{const i=inp(q.dn,{size:5,disabled:ro?'disabled':null});i.onchange=()=>{const v=+String(i.value).replace(',','.');if(v>0){q.dn=v;changed()}};return i})()),
   pick(q,'gender','Art',GEND),pick(q,'flow','Fluss',{'':'–',in:'rein',out:'raus',none:'keiner'}),
   field('Adern (Einführung, z. B. 3,5)',(()=>{const i=inp((q.cores||[]).join(','),{size:8,disabled:ro?'disabled':null});i.onchange=()=>{const v=i.value.split(/[,; ]+/).map(Number).filter(n=>n>0);if(v.length)q.cores=v;else delete q.cores;changed()};return i})()),
   field('Kabeltypen (Einführung)',(()=>{const i=inp((q.cable_types||[]).join(', '),{disabled:ro?'disabled':null});i.onchange=()=>{const v=i.value.split(',').map(s=>s.trim()).filter(Boolean);if(v.length)q.cable_types=v;else delete q.cable_types;changed()};return i})()),
   txt(q,'label','Bezeichnung'));
  if(editable)box.appendChild(h('button',{class:'btn2',text:'Anschlusspunkt löschen',disabled:e.install.ports.length<2?'disabled':null,
   onclick:remove}))}
 if(editable&&p.t==='shape')box.appendChild(h('button',{class:'btn2',text:'Form löschen',onclick:remove}))}
return {render}})();
