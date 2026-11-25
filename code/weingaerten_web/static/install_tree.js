// /waende palette tab "Baum": configurable TGA trees (catalog/tga-trees); only objects suited for the current insertion
// (wall + in / in front of it) are offered, deprecated abstract objects and objects without suitability never.
const InstallTree=(()=>{
const TABKEY='weingaerten.waende.paltab',OKEY='weingaerten.waende.tgatree';
function tab(){return localStorage.getItem(TABKEY)||'tree'}
// tab bar Baum | Katalog; onSwitch redraws the palette
function tabs(onSwitch){const t=tab(),b=(k,l)=>h('button',{class:'btn2'+(t===k?' on':''),style:t===k?'font-weight:bold;border-color:#1C69D4':null,
  text:l,onclick:()=>{localStorage.setItem(TABKEY,k);onSwitch()}});
 return h('div',{style:'display:flex;gap:4px;margin-bottom:4px'},b('tree','Baum'),b('catalog','Katalog'))}
// placement filter of the current insertion mode (in the wall / in front of it); no placement = not suited
function suits(p,place){return !!p&&!p.none&&(p.hosts||[]).includes('wall')&&(p.modes||[]).includes(place==='in'?'in':'on')}
// offered now: in the palette catalog, not deprecated, suited and fitting a free port of the chosen part
function offered(n,ctx){const row=!n.deprecated&&ctx.cat(n.ref);return !!row&&suits(n.placement||row.placement,ctx.place)&&ctx.fits(row)}
function render(ctx){let open;try{open=new Set(JSON.parse(localStorage.getItem(OKEY)||'[]'))}catch(e){open=new Set()}
 const box=h('div',{class:'insttree'});
 const count=nodes=>nodes.reduce((s,n)=>s+(n.nodes?count(n.nodes):offered(n,ctx)?1:0),0);
 function folder(name,nodes,key){const ok=count(nodes);
  const d=h('details',{},h('summary',{class:!ok?'off':null},name+' ',h('span',{class:'cnt',text:'('+ok+')'})));
  d.open=open.has(key)||(ctx.chosen&&ok>0);
  d.addEventListener('toggle',()=>{if(d.open)open.add(key);else open.delete(key);localStorage.setItem(OKEY,JSON.stringify([...open]))});
  const items=h('div',{class:'items'});
  nodes.forEach(n=>{if(n.nodes)d.appendChild(folder(n.name||n.id,n.nodes,key+'/'+n.id));else if(offered(n,ctx))items.appendChild(leaf(n))});
  if(items.childNodes.length)d.appendChild(items);if(!ok)d.appendChild(h('div',{class:'note items',text:'nichts Passendes'}));return d}
 function leaf(n){const row=ctx.cat(n.ref),b=ctx.btn(row);b.textContent='';
  b.append(swatch(row.color),' <'+n.name+'>');if(n.assembly)b.title+=' – Baugruppe';return b}
 (ctx.trees||[]).forEach(t=>box.appendChild(folder(t.name,t.nodes,t.id)));
 if(!(ctx.trees||[]).length)box.appendChild(h('p',{class:'note',text:'Keine TGA-Bäume im Katalog (/katalog/tga).'}));return box}
return {tab,tabs,render,suits}})();
