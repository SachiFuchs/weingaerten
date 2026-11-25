// Katalog pages: master list with filter, detail view and edit form of assemblies, materials, products and components.
const D=JSON.parse(document.getElementById('katdata').textContent);
const EN=D.enums,PAGE=D.page,root=document.getElementById('katdetail'),list=document.getElementById('katlist');
const CAT=Object.fromEntries(EN.assembly_category),GEO=Object.fromEntries(EN.geometry),PT=Object.fromEntries(EN.ptype);
const SELK='weingaerten.katalog.sel.'+PAGE;
let editing=null,curRef=null;
const btnBox=document.getElementById('katbtns'),headName=document.getElementById('katname'),NEWB=document.getElementById('katnew');
const el=r=>D.elements[r]||{};const mats=()=>Object.keys(D.elements).filter(r=>r.startsWith('material:')).sort((a,b)=>(el(a).name||a).localeCompare(el(b).name||b));
const col=r=>((el(r).appearance||{}).color)||'#cccccc';
const bgOf=ap=>{ap=ap||{};const hc=EN.hatch_css[ap.hatch];return (hc?hc+',':'')+(ap.color||'#ccc')};
// standard colours of the material colour field [name, hex]
const STD_COLORS=[['Weiß','#FFFFFF'],['Hellgrau','#D9D9D9'],['Beton','#A7A9AC'],['Anthrazit','#3C3F44'],['Schwarz','#1A1A1A'],['Ziegelrot','#B5523B'],
 ['Dachziegel','#9C3D2E'],['Sand','#E2D3B0'],['Fichte','#E3C590'],['Eiche','#B8864B'],['Nussbaum','#6B4A2F'],['Terrakotta','#C8703E'],
 ['Dämmung gelb','#F2D35B'],['Grün','#5E8C4A'],['Blau','#3A6EA5'],['Stahl','#B8BEC6']];
// '#RGB', '#RRGGBB', 'R, G, B' or 'rgb(R, G, B)' -> '#RRGGBB', else null
function parseColor(s){s=String(s||'').trim();let m=/^#([0-9a-f]{3})$/i.exec(s);if(m)return ('#'+[...m[1]].map(c=>c+c).join('')).toUpperCase();
 if(/^#[0-9a-f]{6}$/i.test(s))return s;
 m=/^(?:rgb\s*\()?\s*(\d{1,3})\s*[,; ]\s*(\d{1,3})\s*[,; ]\s*(\d{1,3})\s*\)?$/i.exec(s);if(!m)return null;const v=m.slice(1).map(Number);
 return v.every(x=>x<=255)?'#'+v.map(x=>x.toString(16).padStart(2,'0')).join('').toUpperCase():null}
// colour field: swatch row, native picker and text field, kept in sync; onchange(hex) after every valid change
function colorField(value,onchange){const cp=inp(value,{type:'color'}),hx=inp(value,{style:'width:120px',placeholder:'#RRGGBB oder R, G, B'});
 const row=h('span',{style:'display:flex;gap:3px;flex-wrap:wrap'});
 const mark=v=>row.querySelectorAll('button').forEach(b=>b.style.outline=b.dataset.hex===String(v||'').toUpperCase()?'2px solid #1C69D4':'none');
 const set=(v,txt)=>{cp.value=v.toLowerCase();if(txt)hx.value=v;mark(v);onchange(v)};
 STD_COLORS.forEach(([n,c])=>{const b=h('button',{type:'button',title:n+' '+c,'data-hex':c,style:'width:18px;height:18px;padding:0;border:1px solid #888;cursor:pointer;background:'+c});
  b.onclick=()=>set(c,true);row.appendChild(b)});
 cp.oninput=()=>set(cp.value,true);hx.oninput=()=>{const v=parseColor(hx.value);if(v)set(v,false)};
 hx.onblur=()=>{const v=parseColor(hx.value);if(v)hx.value=v};mark(parseColor(value));
 return {node:h('span',{style:'display:flex;flex-direction:column;gap:4px'},row,h('span',{style:'display:flex;gap:6px;align-items:center'},cp,hx)),text:hx}}
function bar(layers,height){const tot=layers.reduce((s,l)=>s+(+l.thickness||0),0)||1;const b=h('div',{class:'bar',style:'height:'+height+'px'});
 layers.forEach(l=>{const m=el(l.material);b.appendChild(h('div',{style:'flex:0 0 max(4px,'+((+l.thickness||0)/tot*100)+'%);background:'+bgOf(m.appearance),title:(m.name||l.material)+' – '+cmf(+l.thickness||0)}))});return b}
const choiceDe=(k,v)=>((EN.choice_de[k]||{})[String(v)])||String(v);
const clsOf=c=>el(c.class);const geoOf=c=>clsOf(c).geometry;
const colorFn=c=>role=>col((c.materials||{})[role]);
function done(msg,ref){sessionStorage.setItem('weingaerten.toast',msg);if(ref){localStorage.setItem(SELK,ref);history.replaceState(null,'','#'+encodeURIComponent(ref))}
 else{localStorage.removeItem(SELK);history.replaceState(null,'',location.pathname+location.search)}location.reload()}
function errBox(card){let b=card.querySelector('.kerr');if(!b){b=h('div',{class:'kerr bad',style:'margin:.5rem 0'});card.querySelector('.kbody').prepend(b)}b.textContent='';return b}
function showErrors(card,j){const b=errBox(card);b.appendChild(h('b',{text:'Nicht gespeichert'}));const ul=h('ul',{});(j.errors||[j.error]).forEach(t=>ul.appendChild(h('li',{text:t})));b.appendChild(ul)}
const clean=o=>{const x=JSON.parse(JSON.stringify(o));delete x.file;delete x.ref;delete x.type;return x};
const ROLE_DE={manufacturer:'Hersteller',supplier:'Lieferant'};
const eur=(v,c)=>(+v).toFixed(2).replace('.',',').replace(/\B(?=(\d{3})+(?!\d))/g,'.')+' '+((c||'EUR')==='EUR'?'€':c);
const offersOf=e=>((e.product||{}).offers||[]).filter(o=>typeof o.price==='number');
const bestPrice=e=>{const o=offersOf(e);return o.length?o.reduce((a,b)=>b.price<a.price?b:a):null};
const companies=role=>Object.keys(D.elements).filter(r=>r.startsWith('company:')&&(el(r).roles||[]).includes(role)).sort((a,b)=>(el(a).name||a).localeCompare(el(b).name||b));
const link=r=>{const t=r.split(':')[0],pg={company:'firmen',component:'bauteile',assembly:'aufbauten',material:'materialien',document:'dokumente'}[t];return h('a',{href:'/katalog/'+pg+'#'+encodeURIComponent(r),text:el(r).name||r})};

function summary(ref,e){const s=h('div',{class:'katrow','data-ref':ref,
  'data-search':PAGE==='document'?KatDocs.search(e):((e.name||'')+' '+(e.id||'')+' '+(e.category||'')+' '+(e.class||'')+' '+(e.geometry||'')).toLowerCase()});
 if(PAGE==='document')KatDocs.row(ref,e,s);
 else if(PAGE==='assembly'){const b=bar(e.layers||[],14);b.style.cssText+=';width:120px;flex:none;margin:0';s.append(b,h('b',{text:e.name||e.id}),
  h('span',{text:CAT[e.category]||e.category||''}),h('span',{text:cmf((e.layers||[]).reduce((a,l)=>a+(+l.thickness||0),0))}))}
 else if(PAGE==='material')s.append(swatch((e.appearance||{}).color||'#ccc'),h('b',{text:e.name||e.id}),h('span',{text:e.category||''}),h('span',{text:'λ '+(e.conductivity==null?'–':num(e.conductivity))}),
  bestPrice(e)?h('span',{text:'ab '+eur(bestPrice(e).price,bestPrice(e).currency)}):'');
 else if(PAGE==='component'){const p=e.params||{};s.append(frontSVG(geoOf(e),p,colorFn(e),48,36),h('b',{text:e.name||e.id}),h('span',{text:clsOf(e).name||e.class}),
  h('span',{text:p.width?cmv(p.width)+' × '+cmv(p.height)+' cm':''}),e.opening_capable?h('span',{class:'pill',text:'für Öffnungen'}):'',
  bestPrice(e)?h('span',{text:'ab '+eur(bestPrice(e).price,bestPrice(e).currency)}):'')}
 else if(PAGE==='company'){s.append(h('b',{text:e.name||e.id}),...(e.roles||[]).map(x=>h('span',{class:'pill',text:ROLE_DE[x]||x})),
  h('span',{class:'note',text:prodsOf(ref).length+' Produkte'}))}
 else s.append(h('b',{text:e.name||e.id}),h('span',{text:GEO[e.geometry]||e.geometry}),h('span',{class:'note',text:(e.parameters||[]).length+' Parameter'}));
 s.appendChild(h('code',{text:ref,style:'margin-left:auto;color:#888;background:none;overflow:hidden;text-overflow:ellipsis'}));return s}

// the detail container of the selected (or new) element; view/edit render into its .kbody
function card(ref,e,isNew){root.textContent='';const c=h('div',{class:'kdet','data-ref':ref});c.appendChild(h('div',{class:'kbody'}));root.appendChild(c);
 headName.textContent=isNew?'Neu: '+(e.name||(NEWB?NEWB.textContent.replace('+ ',''):'')):(e.name||e.id);
 KatLayout.photos(isNew?null:e);if(isNew)edit(c,e,true);else view(c,ref,e);return c}
function mayLeave(){return !(editing&&editing.dirty)||confirm('Änderungen verwerfen?')}
function mark(){list.querySelectorAll('.katrow').forEach(r=>r.classList.toggle('on',r.dataset.ref===curRef))}
function empty(){root.textContent='';headName.textContent='';btnBox.style.display='none';KatLayout.photos(null);
 root.appendChild(h('p',{class:'note',text:'Eintrag links auswählen'}))}
function select(ref,force){if(!force&&!mayLeave())return false;editing=null;
 if(!ref||!D.elements[ref]){curRef=null;mark();empty();return true}
 curRef=ref;localStorage.setItem(SELK,ref);history.replaceState(null,'','#'+encodeURIComponent(ref));mark();card(ref,el(ref),false);
 const row=list.querySelector('.katrow.on');if(row)row.scrollIntoView({block:'nearest'});return true}

function kv(rows){const dl=h('dl',{style:'display:grid;grid-template-columns:max-content 1fr;gap:4px 16px'});
 rows.filter(Boolean).forEach(([k,v])=>dl.append(h('dt',{text:k,style:'color:#666'}),h('dd',{style:'margin:0'},v instanceof Node?v:String(v==null?'–':v))));return dl}
function table(head,rows){const t=h('table',{});t.appendChild(h('tr',{},head.map(x=>h('th',{text:x}))));
 rows.forEach(r=>t.appendChild(h('tr',{},r.map(x=>h('td',{},x instanceof Node?x:String(x==null?'–':x))))));return t}
const matCell=r=>h('span',{},swatch(col(r)),' '+(el(r).name||r||'–'));

function prodsOf(cr){return Object.keys(D.elements).filter(r=>(r.startsWith('component:')||r.startsWith('material:'))&&el(r).product&&(el(r).product.manufacturer===cr||(el(r).product.offers||[]).some(o=>o.supplier===cr)))}
function productView(e){const pr=e.product;if(!pr)return null;const best=bestPrice(e);
 return h('div',{},h('h4',{text:'Produkt'}),kv([['Hersteller',pr.manufacturer?link(pr.manufacturer):'–'],['Modell',pr.model],['Artikelnr.',pr.article_no],
   ...(pr.ean?[['EAN',pr.ean]]:[]),...(pr.url?[['Shop',h('a',{href:pr.url,target:'_blank',rel:'noopener',text:pr.url})]]:[])]),
  table(['Lieferant','Preis','netto/brutto','Datum','Beleg'],(pr.offers||[]).map(o=>[o.supplier?link(o.supplier):'–',
   o===best?h('b',{text:eur(o.price,o.currency)}):eur(o.price,o.currency),{net:'netto',gross:'brutto'}[o.price_basis]||'–',o.date,
   o.document&&D.elements[o.document]?h('a',{href:'/katalog/dokumente#'+encodeURIComponent(o.document),text:o.source||el(o.document).name}):o.source])),...detailsView(pr))}
const DETAIL_DE={product_data:'Produktdaten',dimensions_weight:'Maße & Gewicht'};
const detailsView=pr=>Object.entries(pr.details||{}).filter(([,rows])=>Array.isArray(rows)&&rows.length)
 .map(([k,rows])=>h('div',{},h('h4',{text:DETAIL_DE[k]||k}),kv(rows.map(r=>[r.label,r.value]))));


// product block editor shared by components and materials; collect(o) writes o.product and returns false on error
function productForm(e,hint){
 const pr=JSON.parse(JSON.stringify(e.product||{}));pr.offers=pr.offers||[];const hasP=h('input',{type:'checkbox'});hasP.checked=!!e.product;
 const pbox=h('div',{style:'border-left:3px solid #1C69D4;padding-left:10px'}),otab=h('table',{class:'ptab'}),om=h('small',{style:'color:#C62828'});
 const MAN=companies('manufacturer'),SUP=companies('supplier');
 const manS=sel([['','– keiner –']].concat(MAN.map(r=>[r,el(r).name||r])),pr.manufacturer||''),modI=inp(pr.model),artI=inp(pr.article_no);
 function drawO(){otab.textContent='';otab.appendChild(h('tr',{},['Lieferant','Preis','Währung','netto/brutto','Datum','Beleg',''].map(x=>h('th',{text:x}))));
  pr.offers.forEach((o,i)=>{const s=sel(SUP.map(r=>[r,el(r).name||r]),o.supplier||SUP[0]);if(!o.supplier)o.supplier=s.value;s.onchange=()=>o.supplier=s.value;
   const p=inp(o.price==null?'':o.price,{type:'number',step:'0.01',min:'0',style:'width:90px'});p.oninput=()=>o.price=p.value===''?null:+p.value;
   const cu=inp(o.currency||'EUR',{style:'width:55px'});cu.oninput=()=>o.currency=cu.value.trim();
   const pb=sel([['','–'],['net','netto'],['gross','brutto']],o.price_basis||'');pb.onchange=()=>{if(pb.value)o.price_basis=pb.value;else delete o.price_basis};
   const dt=inp(o.date,{type:'date'});dt.oninput=()=>{if(dt.value)o.date=dt.value;else delete o.date};
   const sr=inp(o.source);sr.oninput=()=>{if(sr.value.trim())o.source=sr.value.trim();else delete o.source};
   otab.appendChild(h('tr',{},h('td',{},s),h('td',{},p),h('td',{},cu),h('td',{},pb),h('td',{},dt),h('td',{},sr),
    h('td',{},h('button',{class:'btn2',text:'✕',onclick:()=>{pr.offers.splice(i,1);editing.dirty=true;drawO()}}))))})}
 const addO=h('button',{class:'btn2',text:'+ Angebot',onclick:()=>{if(!SUP.length){om.textContent='Zuerst eine Firma mit Rolle Lieferant anlegen';return}pr.offers.push({supplier:SUP[0],price:null,currency:'EUR'});editing.dirty=true;drawO()}});
 pbox.append(field('Hersteller',manS),field('Modell',modI),field('Artikelnr.',artI),h('h4',{text:'Angebote'}),otab,addO,om);drawO();
 const sync=()=>pbox.style.display=hasP.checked?'':'none';hasP.onchange=sync;sync();
 return {fields:[field('Produkt',hasP,hint),pbox],collect(o){
  if(!hasP.checked){delete o.product;return true}
  om.textContent='';const x={};['ean','url','details'].forEach(k=>{if(pr[k])x[k]=pr[k]});  // fields without input are kept
  if(manS.value)x.manufacturer=manS.value;if(modI.value.trim())x.model=modI.value.trim();if(artI.value.trim())x.article_no=artI.value.trim();
  const ok=!pr.offers.some(q=>!(typeof q.price==='number'&&q.price>=0));if(!ok)om.textContent='Jedes Angebot braucht einen Preis ≥ 0';
  x.offers=pr.offers.map(q=>{const y={supplier:q.supplier,price:q.price,currency:q.currency||'EUR'};['price_basis','date','source'].forEach(k=>{if(q[k])y[k]=q[k]});return y});o.product=x;return ok}}}

function tgaRow(ref){const t=(D.usage[ref]||[]).filter(u=>u.startsWith('tga-component:'));if(!t.length)return null;
 return ['TGA-Bauteil',h('span',{},...t.flatMap((u,i)=>[i?', ':'',h('a',{href:'/katalog/tga#'+encodeURIComponent(u),text:u.split(':')[1]})]),
  h('span',{class:'note',text:' – Produkt und Angebote gelten auch dort'}))]}
function view(c,ref,e){const body=c.querySelector('.kbody');body.textContent='';
 if(PAGE==='document'){KatDocs.view(body,ref,e);btnBox.textContent='';btnBox.style.display='none';return}
 if(PAGE==='assembly'){const tot=(e.layers||[]).reduce((a,l)=>a+(+l.thickness||0),0);
  body.appendChild(h('p',{},(CAT[e.category]||e.category)+' · Schichtung '+(EN.layer_order_de[e.layer_order]||e.layer_order)+' · Gesamtdicke ',h('b',{text:cmf(tot)})));
  if(e.description)body.appendChild(h('p',{class:'note',text:e.description}));body.append(kv([KatIfc.row(e)]),bar(e.layers||[],28));
  body.appendChild(table(['Nr','Material','Kategorie','Dicke','Wärmeleitwert λ'],(e.layers||[]).map((l,i)=>[i+1,D.elements[l.material]?h('span',{},swatch(col(l.material)),' ',link(l.material)):matCell(l.material),el(l.material).category,cmf(l.thickness),el(l.material).conductivity==null?'–':num(el(l.material).conductivity)])))}
 else if(PAGE==='material'){const ap=e.appearance||{};body.append(h('div',{style:'width:60px;height:30px;border:1px solid #888;background:'+bgOf(ap)}),
  kv([['Name',e.name],['Kategorie',e.category],['Beschreibung',e.description],['Wärmeleitwert λ',e.conductivity==null?'–':num(e.conductivity)+' W/(m·K)'],
   ['Rohdichte',e.density==null?'–':num(e.density)+' kg/m³'],['Farbe',ap.color],['Rauheit',ap.roughness==null?'–':num(ap.roughness)],
   ['Schraffur',(EN.hatch.find(x=>x[0]===ap.hatch)||[0,ap.hatch])[1]],['Kennwerte',e.values_source],['Import',(e.imported_from||[]).join(', ')||null],tgaRow(ref),['Datei',e.file]]),productView(e))}
 else if(PAGE==='component'){const cl=clsOf(e),p=e.params||{};
  body.appendChild(h('div',{style:'display:flex;gap:1.5rem;flex-wrap:wrap;align-items:flex-start'},frontSVG(cl.geometry,p,colorFn(e),240,200),
   h('div',{},kv([['Klasse',cl.name||e.class],['Beschreibung',e.description],['für Öffnungen geeignet',e.opening_capable?'ja':'nein'],KatIfc.row(e,cl.ifc),['Datei',e.file]]),
    table(['Parameter','Wert'],(cl.parameters||[]).map(q=>[q.name,p[q.key]==null?'–':q.type==='length'?cmf(p[q.key]):q.type==='choice'?choiceDe(q.key,p[q.key]):q.type==='bool'?(p[q.key]?'ja':'nein'):num(p[q.key])])),
    table(['Rolle','Material'],(cl.material_roles||[]).map(r=>[r.name,matCell((e.materials||{})[r.key])])),productView(e))))}
 else if(PAGE==='company'){const ps=prodsOf(ref);
  body.append(kv([['Rollen',(e.roles||[]).map(x=>ROLE_DE[x]||x).join(', ')],['Beschreibung',e.description],['Adresse',e.address],['Web',e.web],['Datei',e.file]]),
   h('h4',{text:'Hergestellte Produkte'}),table(['Produkt','Preis'],ps.filter(r=>el(r).product.manufacturer===ref).map(r=>[link(r),bestPrice(el(r))?eur(bestPrice(el(r)).price,bestPrice(el(r)).currency):'–'])),
   h('h4',{text:'Angebotene Produkte'}),table(['Produkt','Preis'],ps.flatMap(r=>(el(r).product.offers||[]).filter(o=>o.supplier===ref).map(o=>[link(r),eur(o.price,o.currency)]))))}
 else{const comps=Object.keys(D.elements).filter(r=>r.startsWith('component:')&&el(r).class===ref);
  const fmt=(q,v)=>v==null||v===''?'–':q.type==='length'?cmf(v):q.type==='choice'?choiceDe(q.key,v):q.type==='bool'?(v?'ja':'nein'):num(v);
  body.append(kv([['Rezept',GEO[e.geometry]||e.geometry],['für Öffnungen geeignet',e.opening_capable?'ja':'nein'],KatIfc.row(e),['Beschreibung',e.description],['Datei',e.file]]),
   h('h4',{text:'Parameter'}),table(['Schlüssel','Bezeichnung','Typ','Default','Min','Max','Auswahl','Pflicht'],(e.parameters||[]).map(q=>[q.key,q.name,PT[q.type]||q.type,fmt(q,q.default),
    q.min==null?'–':(q.type==='length'?cmf(q.min):num(q.min)),q.max==null?'–':(q.type==='length'?cmf(q.max):num(q.max)),(q.options||[]).map(o=>choiceDe(q.key,o)).join(', ')||'–',q.required?'ja':'nein'])),
   h('h4',{text:'Materialrollen'}),table(['Schlüssel','Bezeichnung','Default-Material'],(e.material_roles||[]).map(r=>[r.key,r.name,r.default?matCell(r.default):'–'])),
   h('p',{text:'Bauteile dieser Klasse: '+(comps.map(r=>el(r).name||r).join(', ')||'keine')}))}
 KatDocs.belege(body,ref);
 const used=D.usage[ref]||[];body.appendChild(h('p',{text:used.length?'Verwendet von: '+used.join(', '):'nicht verwendet'}));
 const del=h('button',{class:'btn2',text:'Löschen',onclick:()=>{if(!confirm('„'+(e.name||e.id)+'“ ('+ref+') löschen? Die Datei wird entfernt.'))return;
  post('/api/element/delete',{ref}).then(({ok,j})=>{if(ok)done('Gelöscht: '+(e.name||e.id));else errBox(c).textContent=j.error})}});
 if(used.length){del.disabled=true;del.title='Wird verwendet – erst die Verwendung entfernen'}
 btnBox.textContent='';btnBox.style.display='';btnBox.append(h('button',{class:'btn',id:'katedit',text:'Bearbeiten',onclick:()=>edit(c,e,false)}),del);
 if(PAGE==='component'||PAGE==='class')btnBox.appendChild(h('button',{class:'btn2',text:'Kopieren',onclick:()=>{const x=clean(e);x.id=e.id+'-kopie';x.name=(e.name||'')+' (Kopie)';newCard(x)}}))}

function edit(c,e,isNew){
 editing={card:c,dirty:false,isNew};btnBox.style.display='none';const body=c.querySelector('.kbody');body.textContent='';
 const form=h('div',{class:'kform'});body.appendChild(form);form.addEventListener('input',()=>{if(editing)editing.dirty=true});
 const name=inp(e.name),idI=inp(e.id,{pattern:'[a-z0-9]+(-[a-z0-9]+)*'});let idTouched=!isNew||!!e.id;
 if(isNew){idI.oninput=()=>idTouched=true;name.addEventListener('input',()=>{if(!idTouched)idI.value=slugify(name.value)});form.appendChild(field('id',idI,'nur a–z, 0–9 und -'))}
 form.appendChild(field('Name',name));const desc=inp(e.description);let collect;
 const req=(i)=>msg(i,i.value.trim()?'':'Pflichtfeld');
 if(PAGE==='material'){const ap=e.appearance||{};
  const cats=[...new Set(Object.values(D.elements).filter(x=>x.type==='material').map(x=>x.category).filter(Boolean))];
  const dlId='dl-'+Math.random().toString(36).slice(2);const dl=h('datalist',{id:dlId},cats.map(x=>h('option',{value:x})));
  const cat=inp(e.category,{list:dlId}),lam=inp(e.conductivity,{type:'number',step:'0.001',min:'0'}),den=inp(e.density,{type:'number',step:'1',min:'0'}),
   ro=inp(ap.roughness==null?0.9:ap.roughness,{type:'range',min:'0',max:'1',step:'0.05'}),
   rv=h('span',{text:num(ro.value)}),ha=sel(EN.hatch,ap.hatch||'none'),pv=h('div',{style:'width:60px;height:30px;border:1px solid #888'});
  let color=parseColor(ap.color)||'#CCCCCC';
  const upd=()=>{pv.style.background=bgOf({color,hatch:ha.value});rv.textContent=num(ro.value)};
  const cf=colorField(color,v=>{color=v;upd()}),hx=cf.text;ha.onchange=upd;ro.oninput=upd;upd();
  form.append(dl,field('Kategorie',cat),field('Beschreibung',desc),field('Wärmeleitwert λ W/(m·K)',lam,'leer = noch unbekannt'),field('Rohdichte kg/m³',den),
   field('Farbe',cf.node),field('Rauheit',h('span',{style:'display:flex;gap:6px;align-items:center'},ro,rv)),
   field('Schraffur',h('span',{style:'display:flex;gap:10px;align-items:center'},ha,pv)));
  const prod=productForm(e,'Material als gekaufter Artikel mit Hersteller und Lieferanten');form.append(...prod.fields);
  collect=()=>{let ok=req(name)&req(cat)&msg(hx,parseColor(hx.value)?'':'Format #RRGGBB oder R, G, B');
   const o=clean(e);o.name=name.value.trim();o.category=cat.value.trim();if(desc.value.trim())o.description=desc.value.trim();else delete o.description;
   o.conductivity=lam.value===''?null:+lam.value;if(lam.value!==''&&!(+lam.value>0))ok=msg(lam,'Wert > 0')&&0;
   if(den.value==='')delete o.density;else{o.density=+den.value;if(!(o.density>0))ok=msg(den,'Wert > 0')&&0}
   o.appearance={color:parseColor(hx.value),roughness:+ro.value,hatch:ha.value};if(!prod.collect(o))ok=0;return ok?o:null}}
 else if(PAGE==='assembly'){const cat=sel(EN.assembly_category,e.category||'exterior_wall');
  const lo=h('span',{});
  const vis=e.visualization||{},vw=sel(EN.view,vis.view||'outer_layers'),sc=sel(EN.view,vis.section||'all_layers');
  let layers=(e.layers||[]).map(l=>({material:l.material,thickness:l.thickness}));const tbl=h('table',{class:'ptab'}),tot=h('b',{}),barBox=h('div',{}),lm=h('small',{style:'color:#C62828'});
  const M=mats();const ends={outside_in:['außen','innen'],left_right:['links','rechts'],top_down:['oben','unten'],wall_out:['Wand','Raum']};
  function refresh(){const t=layers.reduce((a,x)=>a+(+x.thickness||0),0);tot.textContent=cmf(t);
   barBox.textContent='';barBox.appendChild(bar(layers,20))}
  function draw(){const order=EN.layer_order[cat.value];lo.textContent=EN.layer_order_de[order];tbl.textContent='';
   tbl.appendChild(h('tr',{},['Nr','','Material','Dicke cm','','',''].map(x=>h('th',{text:x}))));
   layers.forEach((l,i)=>{const ms=sel(M.map(r=>[r,el(r).name||r]),l.material||M[0]);if(!l.material)l.material=ms.value;const sw=swatch(col(ms.value));
    ms.onchange=()=>{l.material=ms.value;sw.style.background=col(ms.value);refresh()};
    const th=inp(l.thickness?cmv(l.thickness):'',{type:'number',step:'0.1',min:'0',style:'width:80px'});th.oninput=()=>{l.thickness=th.value===''?0:tom(+th.value);refresh()};
    const mv=d=>()=>{const j=i+d;if(j<0||j>=layers.length)return;[layers[i],layers[j]]=[layers[j],layers[i]];editing.dirty=true;draw()};
    tbl.appendChild(h('tr',{},h('td',{text:String(i+1)}),h('td',{class:'note',text:i===0?ends[order][0]:(i===layers.length-1?ends[order][1]:'')}),h('td',{},sw,' ',ms),h('td',{},th),
     h('td',{},h('button',{class:'btn2',text:'↑',onclick:mv(-1)})),h('td',{},h('button',{class:'btn2',text:'↓',onclick:mv(1)})),
     h('td',{},h('button',{class:'btn2',text:'✕',onclick:()=>{layers.splice(i,1);editing.dirty=true;draw()}}))))});refresh()}
  cat.onchange=draw;draw();const ifc=KatIfc.form(e,'assembly');
  form.append(field('Kategorie',cat,'bestimmt die Schichtung'),field('Schichtung',lo,'ergibt sich aus der Kategorie'),field('Beschreibung',desc),field('Darstellung Ansicht',vw),field('Darstellung Schnitt',sc),...ifc.fields,
   h('h4',{text:'Schichten'}),tbl,h('button',{class:'btn2',text:'+ Schicht',onclick:()=>{layers.push({material:M[0],thickness:0});editing.dirty=true;draw()}}),h('p',{},'Gesamtdicke ',tot),barBox,lm);
  collect=()=>{let ok=req(name);lm.textContent='';if(!layers.length){lm.textContent='Mindestens eine Schicht';ok=0}else if(layers.some(l=>!(l.thickness>0))){lm.textContent='Jede Schicht braucht eine Dicke > 0';ok=0}
   const o=clean(e);o.name=name.value.trim();o.category=cat.value;delete o.class;if(desc.value.trim())o.description=desc.value.trim();else delete o.description;
   o.layer_order=EN.layer_order[cat.value];o.layers=layers.map(l=>({material:l.material,thickness:l.thickness}));o.visualization={view:vw.value,section:sc.value};if(!ifc.collect(o))ok=0;return ok?o:null}}
 else if(PAGE==='component'){const classes=Object.keys(D.elements).filter(r=>r.startsWith('class:'));
  const cs=sel(classes.map(r=>[r,el(r).name||r]),e.class||classes[0]);const dyn=h('div',{});const prev=h('div',{style:'border:1px solid #E0E0E0;padding:6px'});
  const capable=h('input',{type:'checkbox'});let ctl={};
  if(!isNew)cs.disabled=true;form.append(field('Klasse',cs,isNew?'bestimmt die Parameter':'kann nicht geändert werden'),field('Beschreibung',desc));
  form.appendChild(h('div',{style:'display:flex;gap:1.5rem;flex-wrap:wrap;align-items:flex-start'},h('div',{style:'flex:1;min-width:320px'},dyn),prev));
  function current(){const cl=el(cs.value);const p={},m={};(cl.parameters||[]).forEach(q=>{const i=ctl['p:'+q.key];if(!i)return;
    if(q.type==='bool')p[q.key]=i.checked;else if(q.type==='choice'){const v=i.value;p[q.key]=(q.options||[]).find(o=>String(o)===v)}
    else if(i.value!=='')p[q.key]=q.type==='length'?tom(+i.value):+i.value});
   (cl.material_roles||[]).forEach(r=>{const i=ctl['m:'+r.key];if(i)m[r.key]=i.value});return {cl,p,m}}
  function preview(){const {cl,p,m}=current();prev.textContent='';prev.appendChild(frontSVG(cl.geometry,p,role=>col(m[role]),260,240))}
  function build(fresh){const cl=el(cs.value);dyn.textContent='';ctl={};const pv=fresh?{}:(e.params||{}),mv=fresh?{}:(e.materials||{});
   (cl.parameters||[]).forEach(q=>{const v=pv[q.key]!=null?pv[q.key]:q.default;let i;
    if(q.type==='bool'){i=h('input',{type:'checkbox'});i.checked=!!v}
    else if(q.type==='choice')i=sel((q.options||[]).map(o=>[o,choiceDe(q.key,o)]),v);
    else{const isL=q.type==='length';i=inp(v==null?'':(isL?cmv(v):v),{type:'number',step:isL?'0.1':'any'});
     if(q.min!=null)i.min=isL?cmv(q.min):q.min;if(q.max!=null)i.max=isL?cmv(q.max):q.max}
    i.addEventListener('input',preview);i.addEventListener('change',preview);ctl['p:'+q.key]=i;
    const hint=q.type==='length'&&(q.min!=null||q.max!=null)?(q.min!=null?num(cmv(q.min)):'')+'–'+(q.max!=null?num(cmv(q.max)):'')+' cm':(q.type==='length'?'cm':null);
    dyn.appendChild(field(q.name+(q.required?' *':''),i,hint))});
   (cl.material_roles||[]).forEach(r=>{const M=mats();const s=sel(M.map(x=>[x,el(x).name||x]),mv[r.key]||r.default||M[0]);const sw=swatch(col(s.value));
    s.onchange=()=>{sw.style.background=col(s.value);preview()};ctl['m:'+r.key]=s;dyn.appendChild(field('Material '+r.name,h('span',{style:'display:flex;gap:6px;align-items:center'},sw,s)))});
   capable.checked=fresh?!!cl.opening_capable:!!e.opening_capable;dyn.appendChild(field('für Öffnungen geeignet',capable));preview()}
  const ifc=KatIfc.form(e,'component',el(cs.value).ifc);form.append(...ifc.fields);
  // product section
  const prod=productForm(e,'Bauteil als fertiges Produkt mit Hersteller und Lieferanten');form.append(...prod.fields);
  cs.onchange=()=>build(true);build(isNew&&!e.params);
  collect=()=>{let ok=req(name);const {cl,p,m}=current();
   (cl.parameters||[]).forEach(q=>{const i=ctl['p:'+q.key];if(!i||q.type==='bool'||q.type==='choice')return;const v=p[q.key];
    if(v==null){ok=msg(i,q.required?'Pflichtfeld':'')&&ok;return}
    if(q.min!=null&&v<q.min-1e-9)ok=msg(i,'mindestens '+(q.type==='length'?cmf(q.min):num(q.min)))&&0;
    else if(q.max!=null&&v>q.max+1e-9)ok=msg(i,'höchstens '+(q.type==='length'?cmf(q.max):num(q.max)))&&0;else msg(i,'')});
   const o=clean(e);o.name=name.value.trim();if(desc.value.trim())o.description=desc.value.trim();else delete o.description;
   o.class=cs.value;o.opening_capable=capable.checked;o.params=p;o.materials=m;
   if(!ifc.collect(o))ok=0;if(!prod.collect(o))ok=0;return ok?o:null}}
 else if(PAGE==='company'){const roles=new Set(e.roles||[]);const rbox=h('span',{style:'display:flex;gap:14px'}),rm=h('small',{style:'color:#C62828'});
  Object.entries(ROLE_DE).forEach(([k,l])=>{const cb=h('input',{type:'checkbox'});cb.checked=roles.has(k);cb.onchange=()=>cb.checked?roles.add(k):roles.delete(k);rbox.appendChild(h('label',{},cb,' '+l))});
  const adr=inp(e.address),web=inp(e.web);form.append(field('Rollen',rbox),rm,field('Beschreibung',desc),field('Adresse',adr),field('Web',web));
  collect=()=>{let ok=req(name);rm.textContent='';if(!roles.size){rm.textContent='Mindestens eine Rolle';ok=0}
   const o=clean(e);o.name=name.value.trim();o.roles=Object.keys(ROLE_DE).filter(k=>roles.has(k));
   [['description',desc],['address',adr],['web',web]].forEach(([k,i])=>{if(i.value.trim())o[k]=i.value.trim();else delete o[k]});return ok?o:null}}
 else{const geo=sel(EN.geometry,e.geometry||'window'),capable=h('input',{type:'checkbox'});capable.checked=e.opening_capable!==false;
  let params=JSON.parse(JSON.stringify(e.parameters||[])),roles=JSON.parse(JSON.stringify(e.material_roles||[]));
  const pt=h('table',{class:'ptab'}),rt=h('table',{class:'ptab'}),pm=h('small',{style:'color:#C62828'});
  const isReq=q=>(EN.required_keys[geo.value]||[]).includes(q.key);
  function ensure(){(EN.recipe[geo.value]||[]).forEach(r=>{if(!params.some(q=>q.key===r.key))params.push(JSON.parse(JSON.stringify(r)))})}
  function drawP(){pt.textContent='';pt.appendChild(h('tr',{},['Schlüssel','Bezeichnung','Typ','Default','Min','Max','Auswahlwerte','Pflicht','','',''].map(x=>h('th',{text:x}))));
   params.forEach((q,i)=>{const rq=isReq(q);const isL=q.type==='length';
    const k=inp(q.key,{style:'width:100px'}),n=inp(q.name),t=sel(EN.ptype,q.type);if(rq){k.disabled=true;t.disabled=true}
    const dv=q.type==='bool'?h('input',{type:'checkbox'}):inp(q.default==null?'':(isL?cmv(q.default):q.default),{style:'width:70px'});if(q.type==='bool')dv.checked=!!q.default;
    const mn=inp(q.min==null?'':(isL?cmv(q.min):q.min),{type:'number',step:'any',style:'width:70px'}),mx=inp(q.max==null?'':(isL?cmv(q.max):q.max),{type:'number',step:'any',style:'width:70px'});
    const op=inp((q.options||[]).join(', '),{style:'width:110px'});if(q.type!=='choice')op.disabled=true;if(q.type==='bool'||q.type==='choice'){mn.disabled=true;mx.disabled=true}
    const rqc=h('input',{type:'checkbox'});rqc.checked=!!q.required||rq;if(rq)rqc.disabled=true;
    const parseNum=x=>x===''?undefined:(isL?tom(+x):+x);
    k.oninput=()=>q.key=k.value.trim();n.oninput=()=>q.name=n.value;t.onchange=()=>{q.type=t.value;delete q.default;delete q.min;delete q.max;if(q.type==='choice')q.options=q.options||[];drawP()};
    dv.oninput=dv.onchange=()=>{if(q.type==='bool')q.default=dv.checked;else if(q.type==='choice'){const o=(q.options||[]).find(o=>String(o)===dv.value.trim());q.default=o===undefined?dv.value.trim():o}else q.default=parseNum(dv.value)};
    mn.oninput=()=>q.min=parseNum(mn.value);mx.oninput=()=>q.max=parseNum(mx.value);
    op.oninput=()=>{const parts=op.value.split(',').map(s=>s.trim()).filter(Boolean);q.options=parts.every(s=>/^-?\d+(\.\d+)?$/.test(s))?parts.map(Number):parts};
    rqc.onchange=()=>q.required=rqc.checked;
    const mv=d=>()=>{const j=i+d;if(j<0||j>=params.length)return;[params[i],params[j]]=[params[j],params[i]];editing.dirty=true;drawP()};
    const rm=h('button',{class:'btn2',text:'✕',onclick:()=>{params.splice(i,1);editing.dirty=true;drawP()}});if(rq){rm.disabled=true;rm.title='vom Rezept benötigt'}
    pt.appendChild(h('tr',{},h('td',{},k,rq?h('small',{class:'pill',text:'Rezept'}):null),h('td',{},n),h('td',{},t),h('td',{},dv,isL?' cm':''),h('td',{},mn),h('td',{},mx),h('td',{},op),h('td',{},rqc),
     h('td',{},h('button',{class:'btn2',text:'↑',onclick:mv(-1)})),h('td',{},h('button',{class:'btn2',text:'↓',onclick:mv(1)})),h('td',{},rm)))})}
  function drawR(){rt.textContent='';rt.appendChild(h('tr',{},['Schlüssel','Bezeichnung','Default-Material',''].map(x=>h('th',{text:x}))));const M=mats();
   roles.forEach((r,i)=>{const k=inp(r.key,{style:'width:100px'}),n=inp(r.name),d=sel([['','–']].concat(M.map(x=>[x,el(x).name||x])),r.default||'');
    k.oninput=()=>r.key=k.value.trim();n.oninput=()=>r.name=n.value;d.onchange=()=>{if(d.value)r.default=d.value;else delete r.default};
    rt.appendChild(h('tr',{},h('td',{},k),h('td',{},n),h('td',{},d),h('td',{},h('button',{class:'btn2',text:'✕',onclick:()=>{roles.splice(i,1);editing.dirty=true;drawR()}}))))})}
  geo.onchange=()=>{ensure();drawP()};if(isNew&&!params.length)ensure();drawP();drawR();const ifc=KatIfc.form(e,'class');
  form.append(field('Beschreibung',desc),field('Rezept',geo,'Fenster und Tür brauchen Breite, Höhe, Tiefe, Rahmenbreite; Fenster zusätzlich Anzahl Flügel'),field('für Öffnungen geeignet',capable),...ifc.fields,
   h('h4',{text:'Parameter'}),pt,h('button',{class:'btn2',text:'+ Parameter',onclick:()=>{params.push({key:'',name:'',type:'length',required:false});editing.dirty=true;drawP()}}),pm,
   h('h4',{text:'Materialrollen'}),rt,h('button',{class:'btn2',text:'+ Rolle',onclick:()=>{roles.push({key:'',name:''});editing.dirty=true;drawR()}}));
  collect=()=>{let ok=req(name);pm.textContent='';const keys=params.map(q=>q.key),rk=roles.map(r=>r.key);const bad=[];
   params.forEach(q=>{if(!/^[a-z][a-z0-9_]*$/.test(q.key||''))bad.push('Schlüssel „'+(q.key||'')+'“ ungültig');if(!(q.name||'').trim())bad.push('Bezeichnung fehlt bei '+(q.key||'?'));
    if(q.type==='choice'&&!(q.options||[]).length)bad.push(q.key+': Auswahlwerte fehlen')});
   roles.forEach(r=>{if(!/^[a-z][a-z0-9_]*$/.test(r.key||''))bad.push('Rollen-Schlüssel „'+(r.key||'')+'“ ungültig');if(!(r.name||'').trim())bad.push('Rollen-Bezeichnung fehlt')});
   if(new Set(keys).size!==keys.length)bad.push('Parameter-Schlüssel doppelt');if(new Set(rk).size!==rk.length)bad.push('Rollen-Schlüssel doppelt');
   if(bad.length){pm.textContent=bad.join(' · ');ok=0}
   const o=clean(e);o.name=name.value.trim();if(desc.value.trim())o.description=desc.value.trim();else delete o.description;o.geometry=geo.value;o.opening_capable=capable.checked;
   o.parameters=params.map(q=>{const x={key:q.key,name:q.name,type:q.type};['default','min','max'].forEach(k=>{if(q[k]!==undefined&&q[k]!==''&&q[k]!==null&&!(typeof q[k]==='number'&&isNaN(q[k])))x[k]=q[k]});
    if(q.type==='choice')x.options=q.options||[];x.required=!!q.required||isReq(q);return x});
   o.material_roles=roles.map(r=>{const x={key:r.key,name:r.name};if(r.default)x.default=r.default;return x});if(!ifc.collect(o))ok=0;return ok?o:null}}
 const save=h('button',{class:'btn',text:'Speichern',onclick:()=>{const o=collect();const id=idI.value.trim();
  if(isNew&&!msg(idI,/^[a-z0-9]+(-[a-z0-9]+)*$/.test(id)?'':'nur a–z, 0–9 und -'))return;if(!o)return;o.id=isNew?id:e.id;
  const out=Object.assign({id:o.id,name:o.name},o);const ref=PAGE+':'+out.id;
  post('/api/element/save',{ref,element:out,create:isNew}).then(({ok,j})=>{if(ok){editing=null;done('Gespeichert: '+out.name,ref)}else showErrors(c,j)})}});
 const cancel=h('button',{class:'btn2',text:'Abbrechen',onclick:()=>{if(!mayLeave())return;editing=null;if(isNew)select(curRef,true);else view(c,c.dataset.ref,e)}});
 form.appendChild(h('div',{style:'display:flex;gap:.5rem;margin-top:1rem'},save,cancel));name.focus()}

function newCard(tpl){if(!mayLeave())return;editing=null;const keep=curRef;curRef=null;mark();curRef=keep;card(PAGE+':neu-'+Date.now(),tpl,true)}
function render(){list.textContent='';const refs=Object.keys(D.elements).filter(r=>r.startsWith(PAGE+':')).sort(PAGE==='document'
  ?(a,b)=>(el(b).date||'').localeCompare(el(a).date||'')||(el(a).name||a).localeCompare(el(b).name||b):(a,b)=>(el(a).name||a).localeCompare(el(b).name||b));
 document.getElementById('katcount').textContent=refs.length+' Einträge';
 if(!refs.length)list.appendChild(h('p',{class:'note',text:NEWB?'Noch keine Einträge – über „'+NEWB.textContent+'“ anlegen.':'Noch keine Einträge.'}));
 refs.forEach(r=>{const row=summary(r,el(r));row.onclick=()=>select(r);list.appendChild(row)})}
KatLayout.init(PAGE);render();
list.addEventListener('keydown',ev=>{if(ev.key!=='ArrowDown'&&ev.key!=='ArrowUp')return;ev.preventDefault();
 const rows=[...list.querySelectorAll('.katrow')].filter(r=>r.style.display!=='none');if(!rows.length)return;
 const i=rows.findIndex(r=>r.dataset.ref===curRef);const j=i<0?0:Math.max(0,Math.min(rows.length-1,i+(ev.key==='ArrowDown'?1:-1)));select(rows[j].dataset.ref)});
if(NEWB)NEWB.onclick=()=>{const cls=Object.keys(D.elements).filter(r=>r.startsWith('class:'));
 const tpl=PAGE==='material'?{id:'',name:'',category:'',conductivity:null,appearance:{color:'#cccccc',roughness:0.9,hatch:'none'}}
  :PAGE==='assembly'?{id:'',name:'',category:'exterior_wall',layer_order:'outside_in',layers:[],visualization:{view:'outer_layers',section:'all_layers'}}
  :PAGE==='component'?{id:'',name:'',class:cls[0]}:PAGE==='company'?{id:'',name:'',roles:['supplier']}:{id:'',name:'',geometry:'window',opening_capable:true,parameters:[],material_roles:[{key:'frame',name:'Rahmen'}]};
 if(PAGE==='component'&&!cls.length){alert('Zuerst eine Klasse anlegen (Katalog – Klassen).');return}
 if(PAGE==='class'&&tpl.geometry==='window')tpl.material_roles.push({key:'glazing',name:'Verglasung'});newCard(tpl)};
// search text and (documents) the filter selects; the count shows "<n> von <m> Einträge" while filtered
function applyFilter(){const q=document.getElementById('katsearch').value.trim().toLowerCase(),rows=[...list.querySelectorAll('.katrow')];let n=0;
 rows.forEach(c=>{const on=(!q||c.dataset.search.includes(q))&&KatDocs.pass(c);c.style.display=on?'':'none';if(on)n++});
 document.getElementById('katcount').textContent=(n<rows.length?n+' von ':'')+rows.length+' Einträge'}
if(PAGE==='document')KatDocs.filters(document.getElementById('kattool'),applyFilter);
document.getElementById('katsearch').oninput=applyFilter;
const tm=sessionStorage.getItem('weingaerten.toast');if(tm){sessionStorage.removeItem('weingaerten.toast');toast(tm)}
{const hr=location.hash?decodeURIComponent(location.hash.slice(1)):'';select(D.elements[hr]?hr:localStorage.getItem(SELK),true)}
window.addEventListener('hashchange',()=>{const hr=decodeURIComponent(location.hash.slice(1));if(D.elements[hr]&&hr!==curRef)select(hr)});
window.addEventListener('beforeunload',ev=>{if(editing&&editing.dirty){ev.preventDefault();ev.returnValue=''}});
