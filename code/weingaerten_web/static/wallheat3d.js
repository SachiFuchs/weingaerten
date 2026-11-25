// Wall heating (Wandheizung) in /haus3d: heating panels as boards on the room faces, pipe meanders and feed lines
// in orange, distributor as a metal box, duct to the basement as a hatched column.
// window.WallHeat3d.build(THREE, group, pick, storeys, shown) adds meshes; tip(u) returns tooltip lines for kinds wh_*.
window.WallHeat3d=(function(){
 const PIPE='#FF7A00',BOARD='#C9B48A',DIST='#B8BEC6',DUCT='#D9D2C3';
 const m2=t=>t.toFixed(2).replace('.',',')+' m²';const m=t=>t.toFixed(1).replace('.',',')+' m';
 const v3=(T,p)=>new T.Vector3(p[0],p[2],p[1]);
 function add(group,pick,mesh,data){mesh.userData=data;group.add(mesh);pick.push(mesh)}
 function line(T,group,pick,pts,data){if(!pts||pts.length<2)return;
  const g=new T.BufferGeometry().setFromPoints(pts.map(p=>v3(T,p)));add(group,pick,new T.Line(g,new T.LineBasicMaterial({color:PIPE})),data)}
 function board(T,p,normal){
  // box spanned by the panel front corners and its depth along the field normal
  const [a,b,,d]=p.corners,t=p.depth[1]-p.depth[0];const A=v3(T,a),B=v3(T,b),D=v3(T,d);
  const ux=B.clone().sub(A),uz=D.clone().sub(A),n=new T.Vector3(normal[0],0,normal[1]);
  const mesh=new T.Mesh(new T.BoxGeometry(ux.length(),uz.length(),t),new T.MeshStandardMaterial({color:BOARD,roughness:0.9,transparent:true,opacity:0.55}));
  const basis=new T.Matrix4().makeBasis(ux.clone().normalize(),uz.clone().normalize(),n);mesh.quaternion.setFromRotationMatrix(basis);
  mesh.position.copy(A).add(ux.multiplyScalar(0.5)).add(uz.multiplyScalar(0.5)).add(n.clone().multiplyScalar(t/2));return mesh}
 function build(T,group,pick,storeys,shown){
  (storeys||[]).filter(s=>s.wall_heating&&shown(s.id)).forEach(s=>{const x=s.wall_heating;
   x.fields.forEach(f=>{const c=x.circuits.find(k=>k.id===f.circuit)||{};
    f.panels.forEach(p=>{add(group,pick,board(T,p,f.normal),{kind:'wh_panel',x,f,c,p});line(T,group,pick,p.pipe,{kind:'wh_pipe',x,f,c,p})});
    (f.links||[]).forEach(k=>{line(T,group,pick,k.points,{kind:'wh_link',x,f,c,k});
     // straight press coupling 11.6/11.6 as in the press window: metal sleeve along the pipe with two red press rings
     const ax=k.axis?new T.Vector3(k.axis[0],k.axis[2],k.axis[1]):v3(T,k.points[k.points.length-1]).sub(v3(T,k.points[0]));if(ax.length()<1e-6)ax.set(0,1,0);ax.normalize();
     const q=new T.Quaternion().setFromUnitVectors(new T.Vector3(0,1,0),ax),mid=v3(T,k.position);
     [[0,0.06,0.009,DIST,0.7],[-0.006,0.006,0.0105,'#D32F2F',0.1],[0.006,0.006,0.0105,'#D32F2F',0.1]].forEach(([o,l,r,col,met])=>{
      const s=new T.Mesh(new T.CylinderGeometry(r,r,l,14),new T.MeshStandardMaterial({color:col,roughness:0.35,metalness:met}));
      s.quaternion.copy(q);s.position.copy(mid).add(ax.clone().multiplyScalar(o));add(group,pick,s,{kind:'wh_link',x,f,c,k})})});
    line(T,group,pick,f.feed_supply,{kind:'wh_feed',x,f,c,part:'Vorlauf'});line(T,group,pick,f.feed_return,{kind:'wh_feed',x,f,c,part:'Rücklauf'})});
   const dd=x.distributor,[px,py]=dd.position,ax=dd.axis;
   const box=new T.Mesh(new T.BoxGeometry(dd.width,dd.height,dd.depth),new T.MeshStandardMaterial({color:DIST,roughness:0.4,metalness:0.4}));
   box.position.set(px,dd.z+dd.height/2,py);box.rotation.y=-Math.atan2(ax[1],ax[0]);add(group,pick,box,{kind:'wh_dist',x});
   if(x.duct){const [rx,ry,rw,rh]=x.duct.rect,h=s.height||2.4;
    const col=new T.Mesh(new T.BoxGeometry(rw,h,rh),new T.MeshStandardMaterial({color:DUCT,roughness:0.9,transparent:true,opacity:0.35}));
    col.position.set(rx+rw/2,x.duct.z0+h/2,ry+rh/2);add(group,pick,col,{kind:'wh_duct',x})}})}
 function tip(u){const x=u.x,est=x.estimated?' (geschätzt)':'';
  if(u.kind==='wh_panel'){const p=u.p;return [['Platte Typ '+p.type+': '+(p.name||p.component),(u.c.name||u.f.circuit)+' – '+(u.f.name||u.f.id),
   (p.width*100).toFixed(1).replace('.0','')+' × '+(p.height*100).toFixed(1).replace('.0','')+' cm, Rohr '+(p.pipe_direction==='vertical'?'senkrecht':'waagerecht'),
   'Rohr ca. '+m(p.pipe_length)+(p.estimated?' (geschätzt)':'')],BOARD]}
  if(u.kind==='wh_pipe'||u.kind==='wh_feed'){const c=u.c;return [[(c.name||u.f.circuit)+est,u.kind==='wh_feed'?'Anbindung '+u.part+' – '+(u.f.name||u.f.id):'Rohr in Platte Typ '+u.p.type,
   c.panel_count+' Platten, '+m2(c.area)+(c.design_output!=null?', '+Math.round(c.design_output)+' W':''),
   'Rohr Platten '+m(c.pipe_length)+', Anbindung '+m(c.feed_length)],PIPE]}
  if(u.kind==='wh_link'){const f=u.f,k=u.k,a=f.panels.find(p=>p.index===k.from)||{},b=f.panels.find(p=>p.index===k.to)||{};
   return [['Presskupplung 11,6/11,6',(u.c.name||f.circuit)+' – '+(f.name||f.id),'Platte '+k.from+' ('+a.type+') → '+k.to+' ('+b.type+')',
    'Verbindung '+(k.length*100).toFixed(0)+' cm'+est],DIST]}
  if(u.kind==='wh_dist'){const d=x.distributor;return [[d.name||'Verteiler Wandheizung',x.name||'',x.circuits.length+' Heizkreise'+(d.outlets?' von '+d.outlets+' Abgängen':'')+est,
   x.supply_temperature!=null?'Auslegung '+x.supply_temperature+'/'+x.return_temperature+' °C':''],DIST]}
  if(u.kind==='wh_duct')return [[x.duct.name||'Leitungskanal',x.name||'']];
  return null}
 return {build,tip,KINDS:['wh_panel','wh_pipe','wh_link','wh_feed','wh_dist','wh_duct'],
  COMP_OF:{wh_panel:u=>u.p.component,wh_link:u=>u.k.coupling,wh_dist:u=>u.x.distributor.component,wh_pipe:u=>u.x.pipe,wh_feed:u=>u.x.pipe}}})();
