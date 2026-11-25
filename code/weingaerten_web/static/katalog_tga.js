// Katalog – TGA: classes and components with their connection rules (ends, flow, conductors, clamps, boxes, terminals).
const KatTga=(()=>{
const D=JSON.parse(document.getElementById('katdata').textContent);
const E=D.elements,root=document.getElementById('katdetail'),list=document.getElementById('katlist');
const headName=document.getElementById('katname'),btnBox=document.getElementById('katbtns');
const SELK='weingaerten.katalog.sel.tga';
let curRef=null,editing=null;
// German labels for English keys come from catalog/reference/labels-de.json (D.labels); missing entry = raw value
const LB=D.labels||{},LV=LB.values||{},LA=LB.aliases||{};
const LT=t=>LV[LA[t]||t]||{};
const L=(t,v)=>{if(v==null||v==='')return v;const m=[].concat(t).map(LT).find(m=>m[v]!=null);return m?m[v]:v};
const pick=(m,keys)=>Object.fromEntries(keys.map(k=>[k,m[k]||k]));
const LINE=LT('line'),GENDER=LT('gender'),FLOW=LT('flow'),MEDIUM=LT('medium'),METHOD=LT('method'),PARTNER=LT('partner');
const LOC=LT('location'),MOUNT=LT('mounting'),BOXF=LT('box_function'),KIND=LT('kind');
const PTYPES=['part_type','terminal_type','fitting_type'];
const ROLES=['L','L1','L2','L3','N','PE'];
const ROLE_COLOR={L:'#7B4A2A',L1:'#7B4A2A',L2:'#222222',L3:'#8A8A8A',N:'#1E5AA8',PE:'#9ACD32'};
const el=r=>E[r]||{};
const nameOf=r=>(el(r).name||(D.names[r]||{}).name||r);
const isClass=r=>r.startsWith('tga-class:');
const isTree=r=>r.startsWith('tga-tree:');
const clsOf=e=>el(e.class);
const kindOf=r=>isClass(r)?'class':isTree(r)?'tree':(clsOf(el(r)).kind||'');
const issuesOf=r=>D.issues.filter(i=>i.where===r||i.where.endsWith('/'+r.split(':')[1]+'.json'));
const ptype=e=>{const p=e.params||{};return p.part_type||p.terminal_type||p.fitting_type||''};
// parameter values for display: name from the class, choice value translated, lengths in cm, bool ja/nein
function paramsText(e){const qs=clsOf(e).parameters||[];return Object.entries(e.params||{}).map(([k,v])=>{const q=qs.find(x=>x.key===k)||{};
 const t=q.type==='length'&&typeof v==='number'?num(cmv(v))+' cm':q.type==='bool'||typeof v==='boolean'?yes(v):L(k,v);return (q.name||k)+' = '+t}).join(', ')}
const opts=(m,empty)=>(empty?[['','–']]:[]).concat(Object.entries(m));
const yes=v=>v?'ja':'nein';

function kv(rows){const dl=h('dl',{style:'display:grid;grid-template-columns:max-content 1fr;gap:4px 16px'});
 rows.filter(Boolean).forEach(([k,v])=>dl.append(h('dt',{text:k,style:'color:#666'}),h('dd',{style:'margin:0'},v instanceof Node?v:String(v==null||v===''?'–':v))));return dl}
function table(head,rows){const t=h('table',{});t.appendChild(h('tr',{},head.map(x=>h('th',{text:x}))));
 rows.forEach(r=>t.appendChild(h('tr',{},r.map(x=>h('td',{},x instanceof Node?x:String(x==null||x===''?'–':x))))));return t}
function link(r){if(r.startsWith('material:'))return h('a',{href:'/katalog/materialien#'+encodeURIComponent(r),text:nameOf(r)});
 if(r.startsWith('company:'))return h('a',{href:'/katalog/firmen#'+encodeURIComponent(r),text:nameOf(r)});
 return h('a',{href:'#'+encodeURIComponent(r),text:nameOf(r)})}
function endsText(c){const ends=(c&&c.ends)||[];if(!ends.length)return '';
 return (LINE[c.line]||c.line||'')+' '+ends.map(x=>(x.line?(LINE[x.line]||x.line)+' ':'')+'DN '+x.dn).join(' / ')}
function condCell(list){return h('span',{},...list.map(c=>h('span',{style:'margin-right:8px;white-space:nowrap'},swatch(c.color||'#fff'),' '+c.role)))}

// --- list ---------------------------------------------------------------------------------------------------------
function row(ref){const e=el(ref),c=e.connection||{},n=issuesOf(ref).length,k=kindOf(ref);
 const s=h('div',{class:'katrow','data-ref':ref,'data-kind':isClass(ref)?'class':isTree(ref)?'tree':e.class,'data-issues':String(n),
  'data-abstract':e.abstract?'1':'0','data-assembly':e.assembly?'1':'0',
  'data-search':((e.name||'')+' '+e.id+' '+(e.class||'')+' '+ptype(e)+' '+L(PTYPES,ptype(e))+' '+(c.line||'')+(e.abstract?' abstrakt veraltet':'')+(e.assembly?' baugruppe':'')).toLowerCase()});
 s.append(h('span',{class:'pill',text:k==='class'?'Klasse':k==='tree'?'Baum':(KIND[k]||k)}),h('b',{text:e.name||e.id}));
 if(e.abstract)s.append(h('span',{class:'pill',style:'background:#EEEEEE;color:#777',title:'abstrakte Objekte werden nicht mehr angeboten',text:'veraltet (abstrakt)'}));
 if(e.assembly)s.append(h('span',{class:'pill',style:'background:#E3F2FD',text:'Baugruppe'}));
 if(!isClass(ref)&&!isTree(ref)&&!e.abstract&&((D.placement||{})[ref]||{}).none)s.append(h('span',{class:'pill',style:'background:#FFCDD2',title:'ohne Eignung – wird in keiner Palette angeboten',text:'keine Eignung'}));
 if(isClass(ref))s.append(h('span',{class:'note',text:(e.connection_rules||[]).length+' Regeln'}));
 else if(isTree(ref))s.append(h('span',{class:'note',text:(e.nodes||[]).length+' Knoten'}));
 else{const t=endsText(c);if(t)s.append(h('span',{text:t}));
  if(c.poles)s.append(h('span',{text:c.poles+'-polig'}));
  if(D.conductors[ref])s.append(condCell(D.conductors[ref]));
  if(c.mounting)s.append(h('span',{text:MOUNT[c.mounting]}));
  if(c.accepts)s.append(h('span',{text:c.accepts.join(' ')}))}
 if(n)s.append(h('span',{class:'pill',style:'background:#FFE0B2',text:n+' Hinweis'+(n>1?'e':'')}));
 s.appendChild(h('code',{text:ref,style:'margin-left:auto;color:#888;background:none;overflow:hidden;text-overflow:ellipsis'}));
 s.onclick=()=>select(ref);return s}
const rank=r=>isTree(r)?0:isClass(r)?1:2;
function fillList(){list.textContent='';Object.keys(E).sort((a,b)=>(rank(a)-rank(b))||nameOf(a).localeCompare(nameOf(b)))
 .forEach(r=>list.appendChild(row(r)));applyFilter()}
function applyFilter(){const q=document.getElementById('katsearch').value.trim().toLowerCase(),kind=document.getElementById('tgafilter-kind').value,
 only=document.getElementById('tgafilter-issues').checked,rows=[...list.querySelectorAll('.katrow')];let n=0;
 rows.forEach(c=>{const on=(!q||c.dataset.search.includes(q))&&(!kind||c.dataset.kind===kind||(kind==='abstract'&&c.dataset.abstract==='1')||(kind==='assembly'&&c.dataset.assembly==='1'))&&(!only||c.dataset.issues!=='0');
  c.style.display=on?'':'none';if(on)n++});
 document.getElementById('katcount').textContent=(n<rows.length?n+' von ':'')+rows.length+' Einträge'}
function mark(){list.querySelectorAll('.katrow').forEach(r=>r.classList.toggle('on',r.dataset.ref===curRef))}

// --- detail -------------------------------------------------------------------------------------------------------
function card(ref,isNew){root.textContent='';const c=h('div',{class:'kdet','data-ref':ref},h('div',{class:'kbody'}));root.appendChild(c);return c}
function select(ref,force){if(!force&&editing&&editing.dirty&&!confirm('Änderungen verwerfen?'))return;editing=null;
 if(!ref||!E[ref]){curRef=null;mark();root.textContent='';headName.textContent='';btnBox.style.display='none';KatLayout.photos(null);
  root.appendChild(h('p',{class:'note',text:'Eintrag links auswählen'}));return}
 curRef=ref;localStorage.setItem(SELK,ref);history.replaceState(null,'','#'+encodeURIComponent(ref));mark();
 const c=card(ref);headName.textContent=el(ref).name||ref;bottom(el(ref),false);view(c,ref);
 if(tab()==='tree')KatTgaTree.sidebar(treeBox,select,curRef);
 const r=list.querySelector('.katrow.on');if(r)r.scrollIntoView({block:'nearest'})}
function issueBox(ref){const is=issuesOf(ref);if(!is.length)return null;
 return h('div',{},h('h4',{text:'Hinweise'}),h('ul',{},...is.map(i=>h('li',{class:i.level==='errors'?'bad':'',
  style:i.level==='errors'?'':'color:#8D6E00',text:i.message}))))}
function rulesView(rules){return table(['System','Typen','Medium','Verbindung','Partner','Orte','gerichtet','Regel'],
 (rules||[]).map(r=>[LINE[r.line]||'alle',(r.types||[]).map(t=>L(PTYPES,t)).join(', ')||'alle',MEDIUM[r.medium]||r.medium,METHOD[r.method]||r.method,
  (r.partners||[]).map(p=>PARTNER[p]||p).join(', '),(r.locations||[]).map(p=>LOC[p]||p).join(', '),yes(r.directed),r.note]))}
function connView(ref,e){const c=e.connection;const out=[h('h4',{text:'Verbindung'})];
 if(!c){out.push(h('p',{class:'note',text:'keine Verbindungsdaten'}));return out}
 out.push(kv([['Leitungssystem',LINE[c.line]||c.line],c.poles?['Pole',c.poles]:null,
  c.cross_section?['Querschnitt',num(c.cross_section[0])+' – '+num(c.cross_section[1])+' mm²']:null,
  c.poles?['Endstück erlaubt',yes(c.may_be_end)]:null,c.poles?['Teilbelegung erlaubt',yes(c.partial_use)]:null,
  c.mounting?['Montage',MOUNT[c.mounting]]:null,c.box_function?['Dosenart',BOXF[c.box_function]]:null,
  c.accepts?['nimmt auf',condCell(c.accepts.map(r=>({role:r,color:ROLE_COLOR[r]})))]:null,
  D.conductors[ref]?['Leiter',h('span',{},condCell(D.conductors[ref]),h('span',{class:'note',
   text:D.conductors[ref].length&&D.conductors[ref][0].derived?' (Standard aus Aderzahl)':' (eigene Belegung)'}))]:null,
  c.note?['Hinweis',c.note]:null]));
 if((c.ends||[]).length)out.push(table(['Anschluss','System','DN','Art','Fluss'],c.ends.map(x=>[x.id,LINE[x.line||c.line]||'',x.dn,GENDER[x.gender]||x.gender,FLOW[x.flow]||'–'])));
 return out}
function productView(e){const p=e.material_product||e.product;if(!p)return [];
 return [h('h4',{text:e.material_product?'Produkt (aus Material)':'Produkt'}),kv([e.material_product?['Quelle',link(e.catalog_material)]:null,['Hersteller',p.manufacturer?link(p.manufacturer):'–'],['Modell',p.model],['Artikelnr.',p.article_no],
  p.url?['Shop',h('a',{href:p.url,target:'_blank',rel:'noopener',text:p.url})]:null]),
  table(['Lieferant','Preis','Datum','Quelle'],(p.offers||[]).map(o=>[o.supplier?link(o.supplier):'–',(+o.price).toFixed(2).replace('.',',')+' €',o.date,o.source]))]}
function view(card,ref){const e=el(ref),body=card.querySelector('.kbody');
 if(isTree(ref))KatTgaTree.view(body,ref);
 else if(isClass(ref)){body.append(kv([['Art',KIND[e.kind]||e.kind],['Beschreibung',e.description],['Parameter',(e.parameters||[]).map(p=>p.name).join(', ')],['Datei',e.file]]),
  h('h4',{text:'Verbindungsregeln'}),rulesView(e.connection_rules));
  const comps=Object.keys(E).filter(r=>el(r).class===ref);body.append(h('p',{class:'note',text:comps.length+' Bauteile dieser Klasse'}))}
 else{body.append(kv([['Klasse',link(e.class)],['KG',e.din276],['System',e.system_type],
  ['Parameter',paramsText(e)],
  e.catalog_material?['Material',link(e.catalog_material)]:null,e.estimated?['geschätzt','ja']:null,['Hinweis',e.note],['Datei',e.file]]),
  ...(e.assembly?[]:connView(ref,e)),...KatTgaTree.compView(ref,e));
  const rules=(clsOf(e).connection_rules||[]).filter(r=>(!r.line||r.line===((e.connection||{}).line||(e.params||{}).system_line))&&(!r.types||r.types.includes(ptype(e))));
  if(rules.length)body.append(h('h4',{text:'Regeln der Klasse'}),rulesView(rules));
  body.append(...productView(e))}
 const ib=issueBox(ref);if(ib)body.appendChild(ib);
 const del=h('button',{class:'btn2',text:'Löschen',onclick:()=>{if(!confirm('„'+(e.name||e.id)+'“ ('+ref+') löschen?'))return;
  post('/api/element/delete',{ref}).then(({ok,j})=>{if(ok)done('Gelöscht: '+(e.name||e.id));else alert(j.error)})}});
 btnBox.textContent='';btnBox.style.display='';btnBox.append(h('button',{class:'btn',id:'katedit',text:'Bearbeiten',onclick:()=>edit(card,ref,clean(e),false)}),
  ...(e.assembly?[h('button',{class:'btn2',text:'Kopieren',title:'neue Baugruppe als Kopie anlegen (erst beim Speichern erzeugt)',onclick:()=>copyAssembly(e)})]:[]),del)}
// copy of an assembly: name "<name> (KOPIE)", free id from the name; photos stay with the original (folder is per id)
function copyAssembly(e){const x=clean(e);delete x.photos;x.name=(e.name||e.id)+' (KOPIE)';
 const base=slugify(x.name);let id=base,i=2;while(E['tga-component:'+id])id=base+'-'+i++;x.id=id;
 curRef=null;mark();const c=card('new');headName.textContent='Neu: Kopie von '+(e.name||e.id);edit(c,'tga-component:new',x,true)}
const clean=o=>{const x=JSON.parse(JSON.stringify(o));delete x.ref;delete x.type;delete x.file;delete x.material_product;return x};
function done(msg,ref){sessionStorage.setItem('weingaerten.toast',msg);if(ref){localStorage.setItem(SELK,ref);history.replaceState(null,'','#'+encodeURIComponent(ref))}
 else{localStorage.removeItem(SELK);history.replaceState(null,'',location.pathname)}location.reload()}

// --- tabs Liste / Baum, bottom area (Darstellungs-Editor + photos) ---------------------------------------------------
const TABK='weingaerten.katalog.tgatab',treeBox=document.getElementById('kattree');
const tab=()=>localStorage.getItem(TABK)||'list';
function showTab(){const t=tab();['kattool','tgafilter','katlist'].forEach(id=>document.getElementById(id).style.display=t==='list'?'':'none');
 treeBox.style.display=t==='tree'?'':'none';if(t==='tree')KatTgaTree.sidebar(treeBox,select,curRef);
 document.querySelectorAll('#kattabs button').forEach(b=>{const on=b.dataset.tab===t;b.style.fontWeight=on?'bold':'';b.style.borderColor=on?'#1C69D4':''})}
function bottom(e,editable){const box=document.getElementById('katphotos'),bar=document.getElementById('katvsplit');
 if(!e||!e.class){KatLayout.photos(e);return}
 box.style.display=bar.style.display='';KatTgaDraw.render(box,e,editable,dirty);
 const list=Array.isArray(e.photos)?e.photos:[];if(list.length){const ph=h('div',{style:'display:flex;gap:8px;height:120px;margin-top:8px'});
  list.forEach(f=>{const src='/catalog-photo/'+encodeURIComponent(e.id)+'/'+encodeURIComponent(f);const img=h('img',{src,alt:f,title:f,style:'height:100%;cursor:zoom-in'});
   img.onclick=()=>window.open(src,'_blank','noopener');ph.appendChild(img)});box.appendChild(ph)}}

// --- edit ---------------------------------------------------------------------------------------------------------
const numOrNull=s=>{const t=String(s).trim().replace(',','.');return t===''?null:+t};
function checks(map,vals,onChange){const box=h('span',{style:'display:flex;gap:10px;flex-wrap:wrap'});
 Object.entries(map).forEach(([k,l])=>{const c=h('input',{type:'checkbox'});c.checked=(vals||[]).includes(k);
  c.onchange=()=>onChange(Object.keys(map).filter((_,i)=>box.querySelectorAll('input')[i].checked));box.appendChild(h('label',{},c,' '+l))});return box}
function tableEditor(items,cols,make){const wrap=h('div',{});
 function draw(){wrap.textContent='';const t=h('table',{});t.appendChild(h('tr',{},...cols.map(c=>h('th',{text:c})),h('th',{})));
  items.forEach((it,i)=>{const tr=h('tr',{});make(it).forEach(x=>tr.appendChild(h('td',{},x)));
   tr.appendChild(h('td',{},h('button',{class:'btn2',text:'↑',onclick:()=>{if(i){items.splice(i-1,0,items.splice(i,1)[0]);draw();dirty()}}}),
    h('button',{class:'btn2',text:'✕',onclick:()=>{items.splice(i,1);draw();dirty()}})));t.appendChild(tr)});wrap.appendChild(t)}
 draw();return {wrap,draw}}
function dirty(){if(editing)editing.dirty=true}
function bind(input,fn){input.addEventListener('input',()=>{fn(input.type==='checkbox'?input.checked:input.value);dirty()});
 input.addEventListener('change',()=>{fn(input.type==='checkbox'?input.checked:input.value);dirty()});return input}

function paramInputs(e,box){box.textContent='';const cls=el(e.class);e.params=e.params||{};
 (cls.parameters||[]).forEach(q=>{const v=e.params[q.key];let i;
  if(q.type==='choice'){i=sel([['','–']].concat((q.options||[]).map(o=>[o,String(L(q.key,o))])),v==null?'':v);bind(i,x=>{if(x==='')delete e.params[q.key];else e.params[q.key]=isNaN(+x)||typeof (q.options||[])[0]==='string'?x:+x})}
  else if(q.type==='bool'){i=h('input',{type:'checkbox'});i.checked=!!v;bind(i,x=>e.params[q.key]=x)}
  else if(q.type==='text'){i=inp(v);bind(i,x=>{if(x==='')delete e.params[q.key];else e.params[q.key]=x})}
  else{const cm=q.type==='length';i=inp(v==null?'':(cm?cmv(v):v),{inputmode:'decimal'});
   bind(i,x=>{const n=numOrNull(x);if(n==null)delete e.params[q.key];else e.params[q.key]=cm?tom(n):n})}
  box.appendChild(field(q.name+(q.type==='length'?' (cm)':'')+(q.required?' *':''),i))})}

function connForm(e,box){box.textContent='';const kind=clsOf(e).kind;
 const has=h('input',{type:'checkbox'});has.checked=!!e.connection;
 box.appendChild(field('Verbindungsdaten',h('label',{},has,' vorhanden')));
 const inner=h('div',{});box.appendChild(inner);
 has.onchange=()=>{if(has.checked)e.connection=e.connection||{line:(e.params||{}).system_line||(kind==='cable'?'power':'')};else delete e.connection;dirty();draw()};
 function draw(){inner.textContent='';const c=e.connection;if(!c)return;
  inner.appendChild(field('Leitungssystem',bind(sel(opts(pick(LINE,['ht','kg','ppr','alu_composite','power']),true),c.line||''),x=>{if(x)c.line=x;else delete c.line})));
  if(kind==='pipe'||kind==='fitting'||(c.ends||[]).length||c.line==='ppr'||c.line==='ht'||c.line==='kg'){c.ends=c.ends||[];
   const te=tableEditor(c.ends,['Anschluss','System (Übergang)','DN','Art','Fluss'],x=>[
    bind(inp(x.id,{size:4}),v=>x.id=v),
    bind(sel(opts(pick(LINE,['ht','kg','ppr','alu_composite','thread','metal','other']),true),x.line||''),v=>{if(v)x.line=v;else delete x.line}),
    bind(inp(x.dn,{size:4,inputmode:'decimal'}),v=>x.dn=numOrNull(v)),
    bind(sel(opts(pick(GENDER,['spigot','socket','any'])),x.gender),v=>x.gender=v),
    bind(sel(opts({in:'rein',out:'raus',none:'kein'},true),x.flow||''),v=>{if(v)x.flow=v;else delete x.flow})]);
   inner.append(h('h4',{text:'Anschlüsse'}),te.wrap,h('button',{class:'btn2',text:'+ Anschluss',onclick:()=>{
    c.ends.push({id:String.fromCharCode(97+c.ends.length),dn:(e.params||{}).dn||(e.params||{}).nominal_size_dn||20,gender:'socket'});te.draw();dirty()}}),
    h('p',{class:'note',text:'Abwasser: Muffe = rein, Spitzende = raus (Muffe gegen die Fließrichtung). PP-R: Rohr = Spitzende, Formteil = Muffe.'}))}
  if(kind==='cable'){const own=c.conductors=c.conductors||[];
   const te=tableEditor(own,['Rolle','Farbe'],x=>[bind(sel(ROLES.map(r=>[r,r]),x.role),v=>x.role=v),
    bind(h('input',{type:'color',value:x.color||ROLE_COLOR[x.role]||'#cccccc'}),v=>x.color=v)]);
   inner.append(h('h4',{text:'Leiter (leer = Standard aus Aderzahl)'}),te.wrap,h('button',{class:'btn2',text:'+ Leiter',onclick:()=>{own.push({role:'L'});te.draw();dirty()}}))}
  if(ptype(e)==='clamp'){c.cross_section=c.cross_section||[0.2,4];
   inner.append(field('Pole',bind(inp(c.poles,{inputmode:'numeric',size:4}),v=>{const n=numOrNull(v);if(n==null)delete c.poles;else c.poles=Math.round(n)})),
    field('Querschnitt min (mm²)',bind(inp(num(c.cross_section[0]),{size:5}),v=>c.cross_section[0]=numOrNull(v))),
    field('Querschnitt max (mm²)',bind(inp(num(c.cross_section[1]),{size:5}),v=>c.cross_section[1]=numOrNull(v))),
    field('Endstück erlaubt',bind(Object.assign(h('input',{type:'checkbox'}),{checked:!!c.may_be_end}),v=>c.may_be_end=v)),
    field('Teilbelegung erlaubt',bind(Object.assign(h('input',{type:'checkbox'}),{checked:!!c.partial_use}),v=>c.partial_use=v)))}
  if(ptype(e)==='box')inner.append(field('Montage',bind(sel(opts(pick(MOUNT,['surface','flush','hollow_wall']),true),c.mounting||''),v=>{if(v)c.mounting=v;else delete c.mounting})),
   field('Dosenart',bind(sel(opts(pick(BOXF,['junction','device']),true),c.box_function||''),v=>{if(v)c.box_function=v;else delete c.box_function})));
  if(kind==='terminal'&&c.line==='power')inner.appendChild(field('nimmt Leiter auf',checks(Object.fromEntries(ROLES.map(r=>[r,r])),c.accepts,v=>{c.accepts=v;dirty()})));
  inner.appendChild(field('Hinweis',bind(inp(c.note),v=>{if(v)c.note=v;else delete c.note})))}
 draw()}

function rulesForm(e,box){e.connection_rules=e.connection_rules||[];const rules=e.connection_rules;
 function draw(){box.textContent='';rules.forEach((r,i)=>{const fs=h('fieldset',{style:'margin:6px 0'},h('legend',{text:'Regel '+(i+1)}));
  fs.append(field('System',bind(sel(opts(pick(LINE,['ht','kg','ppr','alu_composite','power']),true),r.line||''),v=>{if(v)r.line=v;else delete r.line})),
   field('Typen (Komma)',bind(inp((r.types||[]).join(', ')),v=>{const t=v.split(',').map(s=>s.trim()).filter(Boolean);if(t.length)r.types=t;else delete r.types}),'part_type / terminal_type / fitting_type, leer = alle'),
   field('Medium',bind(sel(opts(pick(MEDIUM,['power','water_supply','waste_water','heating'])),r.medium),v=>r.medium=v)),
   field('Verbindung',bind(sel(opts(pick(METHOD,['clamp','weld','push','press','screw']),true),r.method||''),v=>{if(v)r.method=v;else delete r.method})),
   field('Partner',checks(pick(PARTNER,['pipe','fitting','cable','clamp','box','terminal','part']),r.partners,v=>{r.partners=v})),field('Orte (Kabel)',checks(pick(LOC,['box','terminal']),r.locations,v=>{if(v.length)r.locations=v;else delete r.locations})),
   field('Fließrichtung beachten',bind(Object.assign(h('input',{type:'checkbox'}),{checked:!!r.directed}),v=>{if(v)r.directed=true;else delete r.directed})),
   field('Regeltext',bind(inp(r.note),v=>{if(v)r.note=v;else delete r.note})),
   h('button',{class:'btn2',text:'Regel entfernen',onclick:()=>{rules.splice(i,1);dirty();draw()}}));box.appendChild(fs)});
  box.appendChild(h('button',{class:'btn2',text:'+ Regel',onclick:()=>{rules.push({medium:'power',partners:[]});dirty();draw()}}))}
 draw()}

function edit(card,ref,e,isNew){editing={dirty:isNew};const body=card.querySelector('.kbody');body.textContent='';
 const classRef=isClass(ref),treeRef=isTree(ref);const idIn=inp(e.id,{disabled:!isNew});
 const nameIn=bind(inp(e.name),v=>{e.name=v;if(isNew){idIn.value=slugify(v);e.id=idIn.value}});
 body.append(field('Name *',nameIn),field('id',idIn));
 if(treeRef)KatTgaTree.edit(body,e);
 else if(classRef){body.append(field('Beschreibung',bind(inp(e.description),v=>{if(v)e.description=v;else delete e.description})),h('h4',{text:'Verbindungsregeln'}));
  const rb=h('div',{});body.appendChild(rb);rulesForm(e,rb)}
 else if(e.assembly){const ab=h('div',{});body.append(field('Hinweis',bind(inp(e.note),v=>{if(v)e.note=v;else delete e.note})),
  h('h4',{text:'Baugruppe'}),ab);KatTgaTree.assemblyForm(e,ab)}
 else{const classes=Object.keys(E).filter(isClass).map(r=>[r,nameOf(r)]);
  const pb=h('div',{class:'kgrid'}),cb=h('div',{});
  body.append(field('Klasse',bind(sel(classes,e.class),v=>{e.class=v;e.params={};paramInputs(e,pb);connForm(e,cb)})),
   field('KG (DIN 276)',bind(inp(e.din276,{size:4}),v=>e.din276=v)),field('System',bind(inp(e.system_type),v=>e.system_type=v)),
   field('Hinweis',bind(inp(e.note),v=>{if(v)e.note=v;else delete e.note})),
   h('h4',{text:'Parameter'}),pb,h('h4',{text:'Verbindung'}),cb);paramInputs(e,pb);connForm(e,cb);
  const tb=h('div',{});body.append(h('h4',{text:'Kürzung, Eignung'}),tb);KatTgaTree.compForm(e,tb,ref);bottom(e,true)}
 const err=h('div',{class:'kerr bad',style:'margin:.5rem 0'});body.prepend(err);
 btnBox.textContent='';btnBox.append(h('button',{class:'btn',text:'Speichern',onclick:ev=>{const sb=ev.currentTarget;
  if(!e.name||!e.id){err.textContent='Name fehlt';return}
  if(e.assembly&&!e.assembly.main){err.textContent='Hauptobjekt fehlt';return}
  const nref=(classRef?'tga-class:':treeRef?'tga-tree:':'tga-component:')+e.id;
  if(treeRef)KatTgaTree.cleanNodes(e.nodes);
  // saving can take long (core validates the whole model): lock the button until the answer arrives
  const busy=on=>{sb.disabled=on;sb.textContent=on?'Speichere …':'Speichern'};busy(true);
  post('/api/element/save',{ref:nref,element:e,create:isNew}).then(({ok,j})=>{if(ok){editing=null;done('Gespeichert: '+e.name,nref)}
   else{busy(false);err.textContent='';err.appendChild(h('b',{text:'Nicht gespeichert'}));err.appendChild(h('ul',{},...(j.errors||[j.error]).map(t=>h('li',{text:t}))))}})
   .catch(x=>{busy(false);err.textContent='Nicht gespeichert: '+x})}}),
  h('button',{class:'btn2',text:'Abbrechen',onclick:()=>{editing=null;select(isNew?null:ref,true)}}))}

// --- start --------------------------------------------------------------------------------------------------------
KatLayout.init('tga');
KatTgaTree.init({E,D,nameOf,link,kv,table,bind,dirty,checks,L});
const kindSel=document.getElementById('tgafilter-kind');
[['','Alle'],['tree','Bäume'],['assembly','Baugruppen'],['class','Klassen']].concat(Object.keys(E).filter(isClass).map(r=>[r,nameOf(r)])).concat([['abstract','veraltet (abstrakt)']]).forEach(([k,l])=>kindSel.appendChild(h('option',{value:k,text:l})));
kindSel.onchange=applyFilter;document.getElementById('tgafilter-issues').onchange=applyFilter;
document.getElementById('katsearch').oninput=applyFilter;
document.getElementById('katnew').onclick=()=>{if(editing&&editing.dirty&&!confirm('Änderungen verwerfen?'))return;
 curRef=null;mark();const tpl={id:'',name:'',class:'tga-class:install-part',din276:'440',system_type:'Stromkreis',params:{part_type:'clamp'},
  connection:{line:'power',poles:3,cross_section:[0.2,4],may_be_end:true,partial_use:true}};
 const c=card('new');headName.textContent='Neu: TGA-Bauteil';edit(c,'tga-component:new',tpl,true)};
document.getElementById('katnewasm').onclick=()=>{if(editing&&editing.dirty&&!confirm('Änderungen verwerfen?'))return;
 curRef=null;mark();const c=card('new');headName.textContent='Neu: TGA-Baugruppe';KatLayout.photos(null);
 edit(c,'tga-component:new',{id:'',name:'',class:'tga-class:install-part',din276:'440',system_type:'Stromkreis',params:{},assembly:{main:'',parts:[]}},true)};
document.getElementById('katnewtree').onclick=()=>{if(editing&&editing.dirty&&!confirm('Änderungen verwerfen?'))return;
 curRef=null;mark();const c=card('new');headName.textContent='Neu: TGA-Baum';KatLayout.photos(null);
 edit(c,'tga-tree:new',{id:'',name:'',nodes:[]},true)};
fillList();
document.querySelectorAll('#kattabs button').forEach(b=>b.onclick=()=>{localStorage.setItem(TABK,b.dataset.tab);showTab()});showTab();
const tm=sessionStorage.getItem('weingaerten.toast');if(tm){sessionStorage.removeItem('weingaerten.toast');toast(tm)}
{const hr=location.hash?decodeURIComponent(location.hash.slice(1)):'';select(E[hr]?hr:localStorage.getItem(SELK),true)}
window.addEventListener('hashchange',()=>{const hr=decodeURIComponent(location.hash.slice(1));if(E[hr]&&hr!==curRef)select(hr)});
window.addEventListener('beforeunload',ev=>{if(editing&&editing.dirty){ev.preventDefault();ev.returnValue=''}});
return {select}})();
