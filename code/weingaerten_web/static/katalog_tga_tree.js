// Katalog – TGA: tree editor (tga-tree), TGA assemblies and the component fields cut, placement and layout
// (abstract objects are deprecated: shown read-only, never offered).
const KatTgaTree=(()=>{
const HOSTS={wall:'Wand',floor:'Boden',ceiling:'Decke',roof:'Dach'};
const MODES={in:'in (eingelassen)',on:'auf (aufliegend)'};
const SYMBOLS={box:'Dose',socket:'Steckdose',switch:'Schalter',lamp:'Leuchte',pipe:'Rohr',fitting:'Formteil',valve:'Ventil',cable:'Kabel',other:'Sonstiges'};
const SIDES={top:'oben',bottom:'unten',left:'links',right:'rechts',front:'vorne',back:'hinten'};
let X=null;
// ctx = {E, D, nameOf, link, kv, table, bind, dirty, checks}
function init(ctx){X=ctx}
const isTree=r=>r.startsWith('tga-tree:');
const isAbstract=r=>!!(X.E[r]||{}).abstract;
const isAssembly=r=>!!(X.E[r]||{}).assembly;
const ROLES=['L','L1','L2','L3','N','PE'];
// effective suitability as text, null = none (never offered)
function suitText(ref){const p=(X.D.placement||{})[ref],e=X.E[ref]||{};if(!p||p.none)return null;
 return p.hosts.map(x=>HOSTS[x]).join(', ')+' – '+p.modes.map(x=>MODES[x]).join(', ')+(isAssembly(ref)?' (vom Hauptobjekt)':p.derived?' (abgeleitet aus Montage)':(e.placement||{}).estimated?' (geschätzt)':'')}
const kindText=r=>!X.E[r]?'unbekannt':isAbstract(r)?'veraltet (abstrakt)':isAssembly(r)?'Baugruppe':'konkret';
const m=v=>v==null?'':String(v).replace('.',',')+' m';
const valText=(v,k)=>typeof v==='number'?String(v).replace('.',','):String(k&&X.L?X.L(k,v):v);

// --- view ---------------------------------------------------------------------------------------------------------
// one tree as nested list; deprecated abstract objects and objects without suitability are marked
function nodeList(nodes){const ul=h('ul',{style:'margin:2px 0 2px 18px;padding:0'});
 (nodes||[]).forEach(n=>{const li=h('li',{});
  if(!n.ref){const f=n.filter;li.append(h('b',{text:n.name||n.id}),f?h('span',{class:'note',text:' Filter: '+[f.class?X.nameOf(f.class):null,f.query?'„'+f.query+'“':null].filter(Boolean).join(', ')}):null,nodeList(n.nodes))}
  else{const s=suitText(n.ref);li.append(X.link(n.ref),' ',h('span',{class:'pill',text:kindText(n.ref)}),
   h('span',{class:'note',style:s?null:'color:#C62828',text:' '+(isAbstract(n.ref)?'wird nicht mehr angeboten':s?'Eignung: '+s:'keine Eignung – wird nicht angeboten')}))}
  ul.appendChild(li)});return ul}
function view(body,ref){const e=X.E[ref];const t=(X.D.trees||[]).find(x=>x.ref===ref);
 body.append(X.kv([['Bäume-Reihenfolge',e.order==null?'–':e.order],['Beschreibung',e.description],['Datei',e.file]]),
  h('h4',{text:'Knoten'}),nodeList(e.nodes))}
// assemblies using `ref` as main object or part: [{ref, as, ports}]
function usedIn(ref){const n=((X.E[ref]||{}).install||{}).ports;const count=(n||[]).length;
 return Object.keys(X.E).filter(r=>isAssembly(r)).sort((a,b)=>X.nameOf(a).localeCompare(X.nameOf(b))).flatMap(r=>{const g=X.E[r].assembly,out=[];
  if(g.main===ref)out.push({ref:r,as:'Hauptobjekt',ports:g.max_connections==null?'alle ('+count+')':g.max_connections+' von '+count});
  (g.parts||[]).forEach(p=>{if(p.ref===ref)out.push({ref:r,as:'Bestandteil'+(p.count>1?' × '+p.count:'')+(p.role?' (Leiter '+p.role+')':''),ports:'–'})});return out})}
// extra rows of a tga-component: assembly, deprecated abstract object, cut, suitability, layout
function compView(ref,e){const out=[],a=(X.D.abstracts||{})[ref],g=(X.D.assemblies||{})[ref];
 if(g){out.push(h('h4',{text:'Baugruppe'}),X.kv([['Hauptobjekt',g.main?X.link(g.main):'–'],
   ['erlaubte Anschlusspunkte',g.max_connections==null?'alle ('+(g.main_ports||0)+')':g.max_connections+' von '+(g.main_ports||0)],
   ['max. Anschlüsse',g.capacity==null?'– (keine Begrenzung)':g.capacity+' (kleinster Wert aus erlaubten Anschlusspunkten und Polzahl der Klemmen)']]),
  X.table(['Bestandteil','Anzahl','Leiter','Pole'],g.items.map(i=>[X.link(i.ref),i.count,i.role||'–',i.poles==null?'–':i.poles])))}
 if(a){out.push(h('h4',{text:'Abstraktes TGA-Objekt (veraltet)'}),h('p',{class:'note',style:'color:#C62828',text:'Abstrakte Objekte werden nicht mehr angeboten – im Baum durch konkrete Objekte oder Baugruppen ersetzen.'}),
  X.kv([['fest',Object.entries(a.fixed).map(([k,v])=>k+' = '+(X.L?X.L(k,v):v)).join(', ')],
   ['konkretisiert durch',a.axes.map(x=>(x.label||x.param)+(x.unit?' ['+x.unit+']':'')).join(', ')],['Vorgabe',a.default?X.link(a.default):'–']]),
  X.table(['Konkretes Objekt'].concat(a.axes.map(x=>x.label||x.param)),a.candidates.map(c=>[X.link(c.ref)].concat(a.axes.map(x=>valText(c.values[x.param],x.param))))))}
 const used=usedIn(ref);
 if(!g)out.push(h('h4',{text:'Verwendet in Baugruppen'}),used.length?X.table(['Baugruppe','als','erlaubte Anschlusspunkte'],used.map(u=>[X.link(u.ref),u.as,u.ports]))
  :h('p',{class:'note',text:'in keiner Baugruppe verwendet'}));
 const rows=[];
 if(e.cut)rows.push(['Kürzung','bis '+m(e.cut.max_length)+(e.cut.min_length?' (ab '+m(e.cut.min_length)+')':'')+(e.cut.default_length?', Vorgabe '+m(e.cut.default_length):'')]);
 if(!a){const s=suitText(ref);rows.push(['Eignung',s||h('span',{style:'color:#C62828;font-weight:bold',text:'keine Eignung – wird in keiner Palette angeboten'})])}
 const l=(e.install||{}).layout;
 if(l){if(l.size)rows.push(['Ausmaße',l.size.map(v=>Math.round(v*1000)).join(' × ')+' mm']);
  if(l.points)rows.push(['Anschlusspunkte',Object.entries(l.points).map(([k,v])=>SIDES[k]+' '+v).join(', ')]);
  if(l.max_connections)rows.push(['max. Anschlüsse',l.max_connections]);if(l.symbol)rows.push(['Darstellung',SYMBOLS[l.symbol]])}
 if(rows.length)out.push(h('h4',{text:'Planung'}),X.kv(rows));
 return out}

// --- tree edit ----------------------------------------------------------------------------------------------------
// objects matching a folder filter {class, query} (inherited from the parent folders); abstract objects are never offered
let dlSeq=0;
function matches(r,f){const e=X.E[r]||{};if(e.abstract)return false;if(f.class&&e.class!==f.class&&!(e.assembly&&(X.E[e.assembly.main]||{}).class===f.class))return false;
 if(f.query){const mp=e.assembly?(X.E[e.assembly.main]||{}).params:null;const s=((e.name||'')+' '+r+' '+JSON.stringify(e.params||{})+(mp?' '+JSON.stringify(mp):'')).toLowerCase();if(!f.query.toLowerCase().split(/\s+/).every(q=>s.includes(q)))return false}return true}
function refList(f){const dl=h('datalist',{id:'tgarefs-'+(++dlSeq)});
 Object.keys(X.E).filter(r=>r.startsWith('tga-component:')&&matches(r,f)).sort((a,b)=>(isAssembly(b)-isAssembly(a))||X.nameOf(a).localeCompare(X.nameOf(b)))
  .forEach(r=>dl.appendChild(h('option',{value:r,text:(isAssembly(r)?'[Baugruppe] ':'')+X.nameOf(r)+(suitText(r)?'':' (keine Eignung)')})));return dl}
const merge=(a,b)=>Object.assign({},a,Object.fromEntries(Object.entries(b||{}).filter(([,v])=>v!==''&&v!=null&&v!==false)));
// filter row of a folder: Klasse, Suchtext; empty values are removed (the deprecated flag `abstract` is dropped)
function filterRow(n,redraw){if(n.filter)delete n.filter.abstract;const f=n.filter||{};const set=(k,v)=>{const x=Object.assign({},n.filter||{});if(v===''||v==null||v===false)delete x[k];else x[k]=v;
  if(Object.keys(x).length)n.filter=x;else delete n.filter;X.dirty()};
 const classes=[['','alle Klassen']].concat(Object.keys(X.E).filter(r=>r.startsWith('tga-class:')).map(r=>[r,X.nameOf(r)]));
 const cs=sel(classes,f.class||'');cs.onchange=()=>{set('class',cs.value);redraw()};
 const q=inp(f.query||'',{size:12,placeholder:'Suchtext'});q.onchange=()=>{set('query',q.value.trim());redraw()};
 return h('span',{class:'note',style:'display:inline-flex;gap:4px;align-items:center;margin-left:18px'},'Filter:',cs,q)}
function nodeEditor(nodes,redraw,flt){const ul=h('ul',{style:'margin:2px 0 2px 18px;padding:0;list-style:none'});
 nodes.forEach((n,i)=>{const li=h('li',{style:'margin:3px 0'}),line=h('span',{style:'display:inline-flex;gap:4px;align-items:center'});
  const move=d=>{const j=i+d;if(j<0||j>=nodes.length)return;[nodes[i],nodes[j]]=[nodes[j],nodes[i]];X.dirty();redraw()};
  const btn=(t,f,title)=>h('button',{class:'btn2',text:t,title,onclick:f});
  if(n.ref===undefined){line.append(h('span',{text:'▸'}),X.bind(inp(n.name,{size:22,placeholder:'Ordner'}),v=>{n.name=v;if(!n.id||n._auto){n.id=slugify(v)||'ordner';n._auto=true}}),
    btn('+ Ordner',()=>{n.nodes.push({id:'ordner-'+(n.nodes.length+1),name:'',nodes:[],_auto:true});X.dirty();redraw()}),
    btn('+ Objekt',()=>{n.nodes.push({id:'objekt-'+(n.nodes.length+1),ref:''});X.dirty();redraw()}))}
  else{const dl=refList(flt||{}),r=X.bind(inp(n.ref,{size:40,list:dl.id,placeholder:'tga-component:… ('+dl.childNodes.length+' passend)'}),v=>{n.ref=v.trim();if(v.includes(':'))n.id=slugify(v.split(':')[1])||n.id});
   const nm=X.bind(inp(n.name,{size:18,placeholder:'Anzeige (optional)'}),v=>{if(v)n.name=v;else delete n.name});
   line.append(h('span',{text:'•'}),dl,r,nm,h('span',{class:'note',style:X.E[n.ref]&&!isAbstract(n.ref)&&suitText(n.ref)?null:'color:#C62828',
    text:kindText(n.ref)+(X.E[n.ref]&&!isAbstract(n.ref)&&!suitText(n.ref)?', keine Eignung':'')}))}
  line.append(btn('↑',()=>move(-1),'nach oben'),btn('↓',()=>move(1),'nach unten'),btn('✕',()=>{nodes.splice(i,1);X.dirty();redraw()},'entfernen'));
  li.appendChild(line);if(n.ref===undefined){li.appendChild(filterRow(n,redraw));li.appendChild(nodeEditor(n.nodes,redraw,merge(flt,n.filter)))}ul.appendChild(li)});
 return ul}
function edit(body,e){e.nodes=e.nodes||[];const box=h('div',{});
 body.append(field('Beschreibung',X.bind(inp(e.description),v=>{if(v)e.description=v;else delete e.description})),
  field('Reihenfolge',X.bind(inp(e.order==null?'':e.order,{size:4}),v=>{const n=parseInt(v,10);if(isNaN(n))delete e.order;else e.order=n})),
  h('h4',{text:'Knoten'}),h('p',{class:'note',text:'Jeder Ordner hat einen Vorgabefilter für die Objektauswahl (Unterordner erben ihn).'}),box);
 function redraw(){box.textContent='';box.append(nodeEditor(e.nodes,redraw,{}),
  h('span',{style:'display:inline-flex;gap:4px;margin-top:4px'},
   h('button',{class:'btn2',text:'+ Ordner',onclick:()=>{e.nodes.push({id:'ordner-'+(e.nodes.length+1),name:'',nodes:[],_auto:true});X.dirty();redraw()}}),
   h('button',{class:'btn2',text:'+ Objekt',onclick:()=>{e.nodes.push({id:'objekt-'+(e.nodes.length+1),ref:''});X.dirty();redraw()}})))}
 redraw()}
// node ids must be unique per folder; helper fields are removed before SAVE
function cleanNodes(nodes){const seen={};(nodes||[]).forEach(n=>{delete n._auto;let id=n.id||'k';while(seen[id])id+='-2';seen[id]=1;n.id=id;
 if(n.ref===undefined){if(!n.name)n.name=id;cleanNodes(n.nodes)}});return nodes}

// --- component fields ---------------------------------------------------------------------------------------------
function numIn(v,fn){return X.bind(inp(v==null?'':String(v).replace('.',','),{size:6}),s=>{const t=String(s).trim().replace(',','.');fn(t===''?null:+t)})}
function compForm(e,box,ref){box.textContent='';
 // deprecated abstract object: kept as is, can only be removed (then it is a concrete object)
 if(e.abstract)box.append(h('div',{class:'note',style:'color:#C62828'},'Abstraktes TGA-Objekt (veraltet, wird nicht mehr angeboten) ',h('button',{class:'btn2',text:'Abstraktion entfernen',onclick:()=>{delete e.abstract;X.dirty();compForm(e,box,ref)}})));
 // cut
 const ct=h('input',{type:'checkbox'});ct.checked=!!e.cut;const ctBox=h('span',{style:'display:inline-flex;gap:6px;align-items:center'});
 ct.onchange=()=>{if(ct.checked)e.cut={max_length:50,default_length:1};else delete e.cut;X.dirty();drawCut()};
 function drawCut(){ctBox.textContent='';if(!e.cut)return;
  // default length is required (length of a new part, e.g. 1 m of a 50 m ring); empty -> 1 m (at most max)
  const warn=h('span',{class:'kmsg',style:'color:#C62828'});
  const check=()=>{warn.textContent=e.cut.default_length>e.cut.max_length?'Vorgabe größer als max. Länge':''};
  ctBox.append('bis',numIn(e.cut.max_length,v=>{if(v)e.cut.max_length=v;check()}),'m, Vorgabe *',numIn(e.cut.default_length,v=>{e.cut.default_length=v||Math.min(1,e.cut.max_length);check()}),
   'm, ab',numIn(e.cut.min_length,v=>{if(v)e.cut.min_length=v;else delete e.cut.min_length}),'m',warn);check()}
 box.append(h('div',{},h('label',{},ct,' Kürzungseigenschaft '),ctBox));drawCut();
 // placement
 const pl=e.placement||{};
 const setPl=(k,v)=>{e.placement=Object.assign({},e.placement||{},{[k]:v});if(!v.length)delete e.placement[k];
  if(!e.placement.hosts&&!e.placement.modes)delete e.placement};
 box.append(field('geeignet für',X.checks(HOSTS,pl.hosts,v=>setPl('hosts',v))),field('Einbau',X.checks(MODES,pl.modes,v=>setPl('modes',v))));
 // layout (only parts with an install block)
 if(e.install){const l=e.install.layout||{};
  const setL=(k,v)=>{const x=Object.assign({},e.install.layout||{});if(v==null||v==='')delete x[k];else x[k]=v;
   if(Object.keys(x).length)e.install.layout=x;else delete e.install.layout};
  const pts=h('span',{style:'display:inline-flex;gap:6px;align-items:center'});
  Object.entries(SIDES).forEach(([k,lb])=>pts.append(lb,numIn((l.points||{})[k],v=>{const p=Object.assign({},(e.install.layout||{}).points||{});
   if(v==null)delete p[k];else p[k]=Math.round(v);setL('points',Object.keys(p).length?p:null)})));
  const size=h('span',{style:'display:inline-flex;gap:6px;align-items:center'}),dims=(l.size||[]).map(v=>Math.round(v*1000));
  ['B','H','T'].forEach((lb,i)=>size.append(lb,numIn(dims[i],v=>{dims[i]=v;setL('size',[0,1,2].every(j=>dims[j]>0)?dims.slice(0,3).map(x=>x/1000):null)})));
  size.append('mm');
  box.append(h('h4',{text:'Layout (Planung)'}),field('Ausmaße (falls nicht am Produkt)',size),field('Anschlusspunkte',pts),
   field('max. Anschlüsse',numIn(l.max_connections,v=>setL('max_connections',v==null?null:Math.round(v)))),
   field('Darstellung',X.bind(sel([['','–']].concat(Object.entries(SYMBOLS)),l.symbol||''),v=>setL('symbol',v))))}}
// --- assembly form ------------------------------------------------------------------------------------------------
// main object (concrete TGA object with install data; class, KG and system are taken from it) and the parts as a list:
// object, count and for clamps the conductor (L, N, PE ...) they clamp; max. connections = smallest pole count
function assemblyForm(e,box){box.textContent='';const g=e.assembly;g.parts=g.parts||[];
 const comps=Object.keys(X.E).filter(r=>r.startsWith('tga-component:')&&!isAbstract(r)&&!isAssembly(r)&&r!=='tga-component:'+e.id);
 const mains=comps.filter(r=>X.E[r].install||X.E[r].class==='tga-class:cable').sort((a,b)=>X.nameOf(a).localeCompare(X.nameOf(b)));
 const ms=sel([['','– Hauptobjekt wählen –']].concat(mains.map(r=>[r,X.nameOf(r)+(suitText(r)?'':' (keine Eignung)')])),g.main||'');
 ms.onchange=()=>{g.main=ms.value;const m=X.E[g.main]||{};['class','din276','system_type'].forEach(k=>{if(m[k])e[k]=m[k]});X.dirty();draw()};
 const isClamp=r=>((X.E[r]||{}).params||{}).part_type==='clamp';
 const poles=r=>((X.E[r]||{}).connection||{}).poles;
 const list=h('div',{}),info=h('div',{class:'note',style:'margin-top:4px'});
 const dl=h('datalist',{id:'tgaasm-'+(++dlSeq)});comps.sort((a,b)=>(isClamp(b)-isClamp(a))||X.nameOf(a).localeCompare(X.nameOf(b)))
  .forEach(r=>dl.appendChild(h('option',{value:r,text:X.nameOf(r)+(isClamp(r)?' ['+(poles(r)||'?')+'-polig]':'')})));
 function draw(){list.textContent='';
  g.parts.forEach((p,i)=>{const r=X.bind(inp(p.ref,{size:40,list:dl.id,placeholder:'tga-component:…'}),v=>{p.ref=v.trim();if(!isClamp(p.ref))delete p.role;draw()});
   const c=numIn(p.count||1,v=>{if(v&&v>1)p.count=Math.round(v);else delete p.count});
   const ro=X.bind(sel([['','–']].concat(ROLES.map(x=>[x,x])),p.role||''),v=>{if(v){p.role=v;delete p.count}else delete p.role;draw()});
   if(!isClamp(p.ref))ro.disabled=true;
   list.appendChild(h('div',{style:'display:flex;gap:4px;align-items:center;margin:2px 0'},r,'Anzahl',c,'Leiter',ro,
    h('span',{class:'note',text:X.E[p.ref]?(isClamp(p.ref)?(poles(p.ref)||'?')+'-polig':''):'unbekannt'}),
    h('button',{class:'btn2',text:'✕',title:'entfernen',onclick:()=>{g.parts.splice(i,1);X.dirty();draw()}})))});
  const cap=g.parts.filter(p=>p.role&&poles(p.ref)).map(p=>poles(p.ref));if(g.max_connections)cap.push(g.max_connections);
  const nPorts=((X.E[g.main]||{}).install||{}).ports;portsInfo.textContent=g.main?'Hauptobjekt hat '+(nPorts||[]).length+' Anschlusspunkte'+(g.max_connections>(nPorts||[]).length?' – zu viele erlaubt!':''):'';
  info.textContent='Eignung: '+(g.main?(suitText(g.main)||'keine – Hauptobjekt ohne Eignung, wird nicht angeboten'):'–')+
   ' · max. Anschlüsse: '+(cap.length?Math.min(...cap):'–')}
 const portsInfo=h('span',{class:'note'});
 const maxIn=numIn(g.max_connections,v=>{if(v&&v>=1)g.max_connections=Math.round(v);else delete g.max_connections;draw()});
 box.append(field('Hauptobjekt *',ms),field('erlaubte Anschlusspunkte',h('span',{style:'display:inline-flex;gap:6px;align-items:center'},maxIn,portsInfo)),
  h('p',{class:'note',text:'Einbaudaten, Darstellung und Eignung kommen vom Hauptobjekt. Leer = alle Anschlusspunkte des Hauptobjekts.'}),
  h('b',{text:'Bestandteile'}),dl,list,h('button',{class:'btn2',text:'+ Bestandteil',onclick:()=>{g.parts.push({ref:''});X.dirty();draw()}}),info);draw()}
// --- sidebar (tab Baum) -------------------------------------------------------------------------------------------
// trees with folders (open state per browser) and objects; click = select(ref) in the detail view
function sidebar(box,onSelect,cur){const KEY='weingaerten.katalog.tgatree.open';let open;try{open=new Set(JSON.parse(localStorage.getItem(KEY)||'[]'))}catch(e){open=new Set()}
 box.textContent='';
 const save=()=>localStorage.setItem(KEY,JSON.stringify([...open]));
 const item=(ref,text,pill,off)=>h('div',{class:'katrow'+(ref===cur?' on':''),'data-ref':ref,style:'padding:2px 6px;cursor:pointer'+(off?';opacity:.5':''),
  title:off||null,onclick:()=>onSelect(ref)},
  pill?h('span',{class:'pill',style:'background:#E3F2FD',text:pill}):null,' '+text);
 const off=n=>n.deprecated?'veraltet (abstrakt) – wird nicht angeboten':n.placement&&n.placement.none?'keine Eignung – wird nicht angeboten':null;
 const folder=(name,nodes,key,ref)=>{const d=h('details',{style:'margin-left:.8rem'}),s=h('summary',{style:'cursor:pointer'},h('b',{text:name}));
  if(ref)s.appendChild(h('a',{href:'#',text:' bearbeiten',style:'font-size:.85em;margin-left:6px',onclick:ev=>{ev.preventDefault();onSelect(ref)}}));
  d.appendChild(s);d.open=open.has(key);d.addEventListener('toggle',()=>{if(d.open)open.add(key);else open.delete(key);save()});
  (nodes||[]).forEach(n=>d.appendChild(n.nodes?folder(n.name||n.id,n.nodes,key+'/'+n.id):item(n.ref,'<'+n.name+'>',n.missing?'fehlt':n.assembly?'Baugruppe':n.deprecated?'veraltet':null,off(n))));return d};
 (X.D.trees||[]).forEach(t=>{const f=folder(t.name,t.nodes,t.id,t.ref);f.style.marginLeft='0';box.appendChild(f)});
 if(!(X.D.trees||[]).length)box.appendChild(h('p',{class:'note',text:'Noch kein Baum – „+ Baum“ legt einen an.'}))}
return {init,isTree,isAbstract,isAssembly,view,compView,edit,cleanNodes,compForm,assemblyForm,sidebar}})();
