// Documents (invoices, quotes) on the catalog pages: list row, filters, read-only detail and the `Belege` section
// of companies, materials and components. Uses the helpers of katalog.js (h, el, link, kv, table, eur, D).
const KatDocs={
 TYPE_DE:{invoice:'Rechnung',quote:'Angebot',order_confirmation:'Auftragsbestätigung',credit_note:'Gutschrift',plan:'Plan'},
 CAT_DE:{'anschluss-elektrik-strom':'Anschluss Elektrik/Strom','dachdecker-aussenwaende':'Dachdecker/Außenwände',
  'garten-baustoffe':'Garten/Baustoffe','heizung-kamin':'Heizung/Kamin','innenausbau':'Innenausbau',
  'tueren-fenster-rollladen':'Türen/Fenster/Rollladen','wasser-abwasser':'Wasser/Abwasser'},
 date(d){return d?d.split('-').reverse().join('.'):'–'},
 money(v,c){return typeof v==='number'?eur(v,c):'–'},
 search(e){return [e.name,e.id,e.number,el(e.supplier).name,...(e.items||[]).map(i=>i.description)].join(' ').toLowerCase()},
 row(ref,e,s){s.append(h('span',{text:KatDocs.date(e.date),style:'flex:none'}),h('span',{class:'pill',text:KatDocs.TYPE_DE[e.doc_type]||e.doc_type}),
  h('b',{text:e.name||e.id}),h('span',{text:el(e.supplier).name||e.supplier||''}),h('span',{text:KatDocs.money(e.total_gross,e.currency)}))},
 // filter selects in the tool box; pass(row) tells whether a row matches them
 sels:null,
 filters(tool,apply){const docs=Object.keys(D.elements).filter(r=>r.startsWith('document:')).map(el);
  const opts=(all,label)=>[['',all]].concat([...new Set(docs.map(label[0]).filter(Boolean))].map(v=>[v,label[1](v)]).sort((a,b)=>a[1].localeCompare(b[1])));
  const mk=(id,title,o)=>{const s=h('select',{id,title});o.forEach(([v,t])=>s.appendChild(h('option',{value:v,text:t})));s.onchange=apply;return s};
  KatDocs.sels={doc_type:mk('docfilter-type','Typ',opts('Alle Typen',[e=>e.doc_type,v=>KatDocs.TYPE_DE[v]||v])),
   category:mk('docfilter-category','Kategorie',opts('Alle Kategorien',[e=>e.category,v=>KatDocs.CAT_DE[v]||v])),
   supplier:mk('docfilter-company','Firma',opts('Alle Firmen',[e=>e.supplier,v=>el(v).name||v])),
   year:mk('docfilter-year','Jahr',opts('Alle Jahre',[e=>(e.date||'').slice(0,4),v=>v]).sort((a,b)=>b[0].localeCompare(a[0])))};
  tool.appendChild(h('div',{style:'display:flex;flex-wrap:wrap;gap:4px;width:100%'},...Object.values(KatDocs.sels)))},
 pass(row){if(!KatDocs.sels)return true;const e=el(row.dataset.ref);
  return Object.entries(KatDocs.sels).every(([k,s])=>!s.value||(k==='year'?(e.date||'').slice(0,4):e[k])===s.value)},
 sums(e){const n=k=>+(e[k]||0),out=[];let items=(e.items||[]).reduce((a,i)=>a+(+i.total_price||0),0);
  if(e.items_gross&&typeof e.vat_rate==='number')items/=1+e.vat_rate/100;
  if(typeof e.subtotal_net==='number'&&Math.abs(items-n('subtotal_net'))>0.05)out.push('Positionen '+eur(items)+' ≠ Zwischensumme '+eur(n('subtotal_net')));
  const net=n('subtotal_net')-n('discount_net')+n('shipping_net')-n('deductions_net');
  if(typeof e.total_net==='number'&&Math.abs(net-n('total_net'))>0.05)out.push('Netto '+eur(net)+' ≠ '+eur(n('total_net')));
  if(typeof e.total_gross==='number'&&Math.abs(n('total_net')+n('vat_amount')-n('total_gross'))>0.05)out.push('Brutto ≠ Netto + MwSt.');return out},
 view(body,ref,e){const c=e.currency,m=v=>KatDocs.money(v,c);
  body.append(kv([['Typ',KatDocs.TYPE_DE[e.doc_type]||e.doc_type],['Firma',e.supplier?link(e.supplier):'–'],['Datum',KatDocs.date(e.date)],
   ['Nummer',e.number],['Kundennr.',e.customer_number],['Kategorie',KatDocs.CAT_DE[e.category]||e.category],['Projekt',e.project],
   ['Beschreibung',e.description],['PDF',e.pdf||'nicht vorhanden'],
   ['Import',e.imported_from],['Originaldatei',e.original_filename],['Datei',e.file]]),
   h('h4',{text:'Positionen'}),table(['Pos.','Beschreibung','Menge','Einheit','EP','GP','Katalog'],(e.items||[]).map(i=>[i.position,i.description,
    i.quantity==null?'–':num(i.quantity),i.unit_raw&&i.unit_raw!==i.unit?i.unit+' ('+i.unit_raw+')':i.unit,m(i.unit_price),m(i.total_price),
    i.ref?(D.elements[i.ref]?link(i.ref):i.ref):'–'])));
  if(e.items_gross)body.appendChild(h('p',{class:'note',text:'Positionspreise sind brutto (inkl. MwSt.), die Summen netto.'}));
  body.append(h('h4',{text:'Summen'}),kv([['Zwischensumme netto',m(e.subtotal_net)],...(e.discount_net?[['Rabatt',m(e.discount_net)]]:[]),
   ...(e.shipping_net?[['Versand',m(e.shipping_net)]]:[]),...(e.deductions_net?[['Abzüge (Abschläge, Rabatte)',m(e.deductions_net)]]:[]),
   ['Netto',m(e.total_net)],['MwSt.'+(typeof e.vat_rate==='number'?' '+num(e.vat_rate)+' %':''),m(e.vat_amount)],['Brutto',h('b',{text:m(e.total_gross)})]]));
  KatDocs.sums(e).forEach(t=>body.appendChild(h('p',{class:'bad',text:'Belegsumme weicht ab: '+t})));
  if((e.related||[]).length)body.append(h('h4',{text:'Zugehörige Dokumente'}),h('ul',{},...e.related.map(r=>h('li',{},D.elements[r]?link(r):r))))},
 // documents that reference ref (supplier, item or offer), newest first
 belege(body,ref){const docs=(D.usage[ref]||[]).filter(r=>r.startsWith('document:')&&D.elements[r]).sort((a,b)=>(el(b).date||'').localeCompare(el(a).date||''));
  if(!docs.length)return;
  body.append(h('h4',{text:'Belege'}),table(['Datum','Typ','Beleg','Brutto'],docs.map(r=>{const d=el(r);
   return [KatDocs.date(d.date),KatDocs.TYPE_DE[d.doc_type]||d.doc_type,link(r),KatDocs.money(d.total_gross,d.currency)]})))}};
