// IFC mapping (field `ifc` {entity, predefined_type, object_type}) on the catalog pages: view row and form part.
// Components may override the mapping of their class; `inherited` is the class mapping shown as default.
const KatIfc={
 text(x){return x?x.entity+(x.predefined_type?' · '+x.predefined_type:'')+(x.object_type?' „'+x.object_type+'“':''):'–'},
 row(e,inherited){return ['IFC',e.ifc?KatIfc.text(e.ifc):inherited?KatIfc.text(inherited)+' (von der Klasse)':'–']},
 form(e,page,inherited){
  const own=e.ifc||{},EN_IFC=EN.ifc_entities,names=(EN.ifc_page_entities[page]||[]).slice();
  if(own.entity&&!names.includes(own.entity))names.push(own.entity);  // keep values entered elsewhere
  const none=inherited?'wie Klasse ('+KatIfc.text(inherited)+')':'– keine –';
  const ent=sel([['',none]].concat(names.map(n=>[n,n])),own.entity||''),typ=h('select',{}),obj=inp(own.object_type);
  function types(){const list=(EN_IFC[ent.value]||[]).concat(['USERDEFINED','NOTDEFINED']),cur=typ.value||own.predefined_type||'';
   if(cur&&!list.includes(cur))list.push(cur);typ.textContent='';typ.appendChild(h('option',{value:'',text:'–'}));
   list.forEach(t=>typ.appendChild(h('option',{value:t,text:t})));typ.value=list.includes(cur)?cur:'';
   typ.disabled=ent.value==='';sync()}
  function sync(){obj.disabled=typ.value!=='USERDEFINED'||typ.disabled}
  ent.onchange=()=>{typ.value='';types()};typ.onchange=sync;types();
  return {fields:[field('IFC-Klasse',ent,page==='assembly'?'Instanzklasse der Bauteile mit diesem Aufbau (Typ = …Type)':'Instanzklasse (Typ = …Type)'),
    field('IFC-PredefinedType',typ),field('IFC-ObjectType',obj,'nur bei USERDEFINED')],
   collect(o){if(!ent.value){delete o.ifc;return true}
    const x={entity:ent.value};if(typ.value)x.predefined_type=typ.value;
    if(typ.value==='USERDEFINED'){if(!obj.value.trim())return msg(obj,'Pflichtfeld bei USERDEFINED');x.object_type=obj.value.trim()}
    msg(obj,'');o.ifc=x;return true}}}};
