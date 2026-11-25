// Waste water (Abwasser) in /haus3d: pipes as tubes, fittings as short thicker sleeves, penetrations as rings.
// window.Waste3d.build(THREE, group, pick, ww) adds meshes; tip(u) returns tooltip lines for kinds ww_*.
window.Waste3d=(function(){
 const PEN_COLOR='#E5332A';
 const LINE_DE={ht:'HT',kg:'KG'};
 const FIT_DE={bend:'Bogen',branch:'Abzweig',adapter:'Übergang',plug:'Stopfen'};
 const cm=t=>(t*100).toFixed(1).replace('.0','').replace('.',',')+' cm';
 const pct=s=>s==null?'senkrecht':(s*100).toFixed(1).replace('.',',')+' %';
 const v3=(T,p)=>new T.Vector3(p[0],p[2],p[1]);
 function cylinder(T,a,b,radius,color,opacity){const A=v3(T,a),B=v3(T,b),len=A.distanceTo(B);if(len<1e-4)return null;
  const geo=new T.CylinderGeometry(radius,radius,len,20,1,false);const mat=new T.MeshStandardMaterial({color,roughness:0.5,metalness:0.05,transparent:opacity<1,opacity});
  const m=new T.Mesh(geo,mat);m.position.copy(A).add(B).multiplyScalar(0.5);
  m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),B.clone().sub(A).normalize());m.castShadow=true;return m}
 function build(T,group,pick,ww){if(!ww)return;
  ww.runs.forEach(r=>r.segments.forEach((s,i)=>{const m=cylinder(T,s.from,s.to,r.outer_diameter/2,r.color,1);
   if(!m)return;m.userData={kind:'ww_pipe',r,s,i};group.add(m);pick.push(m)}));
  (ww.parts||[]).forEach(p=>{if(!p.position)return;const r=ww.runs.find(x=>x.id===p.run);const rad=(p.outer_diameter||0.1)/2*1.25;
   const dir=p.direction||[0,0,1];const a=p.position.map((v,i)=>v-dir[i]*0.035),b=p.position.map((v,i)=>v+dir[i]*0.035);
   const m=cylinder(T,a,b,rad,p.estimated?'#E0A030':(r?r.color:'#888888'),1);if(!m)return;m.userData={kind:'ww_part',p};group.add(m);pick.push(m)});
  ww.penetrations.filter(p=>p.kind==='through').forEach(p=>{const rad=p.core_drill/2;
   const geo=new T.TorusGeometry(rad,0.008,8,28);const m=new T.Mesh(geo,new T.MeshStandardMaterial({color:PEN_COLOR,roughness:0.6}));
   m.position.copy(v3(T,p.position));
   if(p.direction==='vertical')m.rotation.x=Math.PI/2;else{const r=ww.runs.find(x=>x.id===p.run);const s=r&&r.segments.find(sg=>Math.hypot(sg.to[0]-sg.from[0],sg.to[1]-sg.from[1])>1e-3);
    if(s)m.lookAt(m.position.clone().add(new T.Vector3(s.to[0]-s.from[0],0,s.to[1]-s.from[1])))}
   m.userData={kind:'ww_pen',p};group.add(m);pick.push(m)});
  ww.terminals.forEach(t=>{if(!t.position)return;const geo=new T.SphereGeometry(0.045,16,12);
   const m=new T.Mesh(geo,new T.MeshStandardMaterial({color:'#2B6CB0',roughness:0.4}));m.position.copy(v3(T,t.position));
   m.userData={kind:'ww_term',t};group.add(m);pick.push(m)})}
 function tip(u){const est=x=>x?' (geschätzt)':'';
  if(u.kind==='ww_pipe'){const r=u.r;return [[r.name+est(r.estimated),(r.component_name||r.component),
   LINE_DE[r.line]+' DN '+r.dn+', Ø '+cm(r.outer_diameter),'Abschnitt '+(u.i+1)+'/'+r.segments.length+': '+u.s.length.toFixed(2).replace('.',',')+' m, Gefälle '+pct(u.s.slope),
   'Leitung gesamt '+r.length.toFixed(2).replace('.',',')+' m, min. '+pct(r.min_slope)],r.color]}
  if(u.kind==='ww_pen'){const p=u.p;return [['Durchbruch '+p.element_name+est(p.estimated),p.run_name,
   'Kernbohrung Ø '+cm(p.core_drill)+' für '+LINE_DE[p.line]+' DN '+p.dn,'Länge '+cm(p.length)+', '+({vertical:'senkrecht',horizontal:'waagerecht',oblique:'schräg'})[p.direction]+(p.airtight?', abdichten':'')],PEN_COLOR]}
  if(u.kind==='ww_part'){const p=u.p;return [[(FIT_DE[p.fitting_type]||p.fitting_type)+': '+(p.name||p.component)+est(p.estimated),p.run_name||p.run,
   p.angle!=null?'Winkel '+p.angle+'°'+(p.wanted!=null&&Math.abs(p.wanted-p.angle)>0.5?' (soll '+p.wanted.toFixed(1)+'°)':''):'']]}
  if(u.kind==='ww_term'){const t=u.t;return [[t.name+est(t.estimated),t.component_name||t.component,'Raum '+(t.room||'–')]]}
  return null}
 // catalog ref of the TGA component behind a pick (tooltip link)
 return {build,tip,KINDS:['ww_pipe','ww_part','ww_pen','ww_term'],COMP_OF:{ww_pipe:u=>u.r.component,ww_part:u=>u.p.component,ww_term:u=>u.t.component}}})();
