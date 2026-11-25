// Drinking water (Zuwasser) in /haus3d: PPR pipes in green (cold dark, hot light), fittings as sleeves,
// wall plates as discs, open ends as small spheres, penetrations as rings.
// window.Water3d.build(THREE, group, pick, tw) adds meshes; tip(u) returns tooltip lines for kinds tw_*.
window.Water3d=(function(){
 const PEN_COLOR='#E5332A';
 const FIT_DE={bend:'Bogen',plug:'Endkappe',branch:'T-Stück',adapter:'Übergang'};
 const cm=t=>(t*100).toFixed(1).replace('.0','').replace('.',',')+' cm';
 const m2=t=>t.toFixed(2).replace('.',',')+' m';
 const v3=(T,p)=>new T.Vector3(p[0],p[2],p[1]);
 function cylinder(T,a,b,radius,color){const A=v3(T,a),B=v3(T,b),len=A.distanceTo(B);if(len<1e-4)return null;
  const m=new T.Mesh(new T.CylinderGeometry(radius,radius,len,20,1,false),new T.MeshStandardMaterial({color,roughness:0.45,metalness:0.05}));
  m.position.copy(A).add(B).multiplyScalar(0.5);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),B.clone().sub(A).normalize());m.castShadow=true;return m}
 function add(group,pick,m,data){if(!m)return;m.userData=data;group.add(m);pick.push(m)}
 function build(T,group,pick,tw){if(!tw)return;
  tw.runs.forEach(r=>r.segments.forEach((s,i)=>add(group,pick,cylinder(T,s.from,s.to,r.outer_diameter/2,r.color),{kind:'tw_pipe',r,s,i})));
  (tw.parts||[]).forEach(p=>{if(!p.position)return;const r=tw.runs.find(x=>x.id===p.run);const dir=p.direction||[0,0,1];
   const a=p.position.map((v,i)=>v-dir[i]*0.015),b=p.position.map((v,i)=>v+dir[i]*0.015);
   add(group,pick,cylinder(T,a,b,(p.outer_diameter||0.02)/2*1.4,r?r.color:'#3E8E41'),{kind:'tw_part',p})});
  tw.penetrations.filter(p=>p.kind==='through').forEach(p=>{const m=new T.Mesh(new T.TorusGeometry(p.core_drill/2,0.005,8,24),
   new T.MeshStandardMaterial({color:PEN_COLOR,roughness:0.6}));m.position.copy(v3(T,p.position));if(p.direction==='vertical')m.rotation.x=Math.PI/2;
   add(group,pick,m,{kind:'tw_pen',p})});
  tw.terminals.forEach(t=>{if(!t.position)return;const r=tw.runs.find(x=>x.to===t.ref||x.from===t.ref);const color=r?r.color:'#3E8E41';
   const plate=t.terminal_type==='wall_plate';
   const m=plate?new T.Mesh(new T.CylinderGeometry(0.03,0.03,0.012,24),new T.MeshStandardMaterial({color,roughness:0.4}))
    :new T.Mesh(new T.SphereGeometry(0.02,14,10),new T.MeshStandardMaterial({color,roughness:0.4}));
   m.position.copy(v3(T,t.position));if(plate){m.rotation.z=Math.PI/2;m.position.x+=0.006}add(group,pick,m,{kind:'tw_term',t})})}
 function tip(u){const est=x=>x?' (geschätzt)':'';
  if(u.kind==='tw_pipe'){const r=u.r;return [[r.name+est(r.estimated),(r.component_name||r.component),
   r.medium_name+', PPR DN '+r.dn+', Ø '+cm(r.outer_diameter),'Abschnitt '+(u.i+1)+'/'+r.segments.length+': '+m2(u.s.length),
   'Leitung gesamt '+m2(r.length)],r.color]}
  if(u.kind==='tw_pen'){const p=u.p;return [['Durchbruch '+p.element_name+est(p.estimated),p.run_name,'Kernbohrung Ø '+cm(p.core_drill)],PEN_COLOR]}
  if(u.kind==='tw_part'){const p=u.p;return [[(FIT_DE[p.fitting_type]||p.fitting_type)+': '+(p.name||p.component)+est(p.estimated),p.run_name||p.run,
   p.angle!=null?'Winkel '+p.angle+'°':'']]}
  if(u.kind==='tw_term'){const t=u.t;return [[t.name+est(t.estimated),t.component_name||t.component,'Raum '+(t.room||'–')]]}
  return null}
 // catalog ref of the TGA component behind a pick (tooltip link)
 return {build,tip,KINDS:['tw_pipe','tw_part','tw_pen','tw_term'],COMP_OF:{tw_pipe:u=>u.r.component,tw_part:u=>u.p.component,tw_term:u=>u.t.component}}})();
