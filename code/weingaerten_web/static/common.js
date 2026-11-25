// Shared browser helpers of all pages: element builder h, POST to /api, toast and messages, form fields, swatches, StoreyPick.
function h(tag,attrs,...kids){const e=document.createElement(tag);for(const k in attrs||{}){const v=attrs[k];if(v==null)continue;
 if(k==='class')e.className=v;else if(k==='style')e.style.cssText=v;else if(k.startsWith('on'))e[k]=v;else if(k==='text')e.textContent=v;else e.setAttribute(k,v)}
 kids.flat().forEach(c=>{if(c!=null&&c!==false)e.appendChild(typeof c==='string'?document.createTextNode(c):c)});return e}
const num=v=>String(v).replace('.',',');
const StoreyPick={of(H){const all=H.storeys||[],id=new URLSearchParams(location.search).get('storey');return all.find(s=>s.id===id)||all[0]}};
const cmf=t=>{let s=(t*100).toFixed(2).replace(/0+$/,'').replace(/\.$/,'');return s.replace('.',',')+' cm'};
const cmv=t=>+(t*100).toFixed(2);const tom=c=>Math.round(c*100)/10000;
function post(url,body){return fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(r=>r.json().then(j=>({ok:r.ok,j})))}
function toast(msg){const t=document.getElementById('kattoast');if(!t)return;t.textContent=msg;t.style.display='block';setTimeout(()=>t.style.display='none',3000)}
function slugify(s){return s.toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'')}
function swatch(c){return h('span',{class:'sw',style:'background:'+c})}
function field(label,input,hint){return h('label',{class:'kf'},h('span',{text:label}),input,hint?h('small',{class:'note',text:hint}):null,h('small',{class:'kmsg',style:'color:#C62828'}))}
function inp(v,attrs){const i=h('input',Object.assign({type:'text'},attrs||{}));i.value=v==null?'':v;return i}
function sel(opts,v){const s=h('select',{});opts.forEach(([k,l])=>s.appendChild(h('option',{value:String(k),text:l})));if(v!=null)s.value=String(v);return s}
function msg(el,t){const k=el.closest('.kf');const m=k?k.querySelector('.kmsg'):null;if(m)m.textContent=t||'';el.style.outline=t?'2px solid #C62828':'';return !t}
const SVGNS='http://www.w3.org/2000/svg';
function sv(tag,attrs){const e=document.createElementNS(SVGNS,tag);for(const k in attrs)e.setAttribute(k,attrs[k]);return e}
