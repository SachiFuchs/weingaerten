// Electrical (Elektrik) in /haus3d: conduits as translucent light grey tubes with the cable inside (red 3 cores,
// violet 5 cores), push-fit bends as sleeves, clamps as small rings, boxes as flat grey boxes, open ends as coils.
// window.Electric3d.build(THREE, group, pick, el) adds meshes; tip(u) returns tooltip lines for kinds el_*.
window.Electric3d=(function(){
 const PEN_COLOR='#E5332A',BOX_COLOR='#9EA3A8';
 const PART_DE={bend:'Steckbogen',sleeve:'Steckmuffe',clamp:'Klemmschelle'};
 const cm=t=>(t*100).toFixed(1).replace('.0','').replace('.',',')+' cm';
 const m2=t=>t.toFixed(2).replace('.',',')+' m';
 const v3=(T,p)=>new T.Vector3(p[0],p[2],p[1]);
 function cylinder(T,a,b,radius,color,opacity){const A=v3(T,a),B=v3(T,b),len=A.distanceTo(B);if(len<1e-4)return null;
  const mat=new T.MeshStandardMaterial({color,roughness:0.5,metalness:0.05,transparent:opacity<1,opacity:opacity,depthWrite:opacity>=1});
  const m=new T.Mesh(new T.CylinderGeometry(radius,radius,len,18,1,false),mat);
  m.position.copy(A).add(B).multiplyScalar(0.5);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),B.clone().sub(A).normalize());return m}
 function add(group,pick,m,data){if(!m)return;m.userData=data;group.add(m);pick.push(m)}
 function build(T,group,pick,el){if(!el)return;
  el.runs.forEach(r=>r.segments.forEach((s,i)=>{
   add(group,pick,cylinder(T,s.from,s.to,r.cable_diameter/2,r.color,1),{kind:'el_cable',r,s,i});
   if(r.conduit)add(group,pick,cylinder(T,s.from,s.to,r.outer_diameter/2,r.conduit_color,0.45),{kind:'el_cable',r,s,i})}));
  (el.parts||[]).forEach(p=>{if(!p.position)return;const dir=p.direction||[0,0,1];const h=p.fitting_type==='clamp'?0.006:0.02;
   const a=p.position.map((v,i)=>v-dir[i]*h),b=p.position.map((v,i)=>v+dir[i]*h);
   const r=(p.outer_diameter||0.02)/2*(p.fitting_type==='clamp'?1.25:1.3);
   add(group,pick,cylinder(T,a,b,r,p.fitting_type==='clamp'?'#6E7378':'#B8BDC2',1),{kind:'el_part',p})});
  el.penetrations.filter(p=>p.kind==='through').forEach(p=>{const m=new T.Mesh(new T.TorusGeometry(p.core_drill/2,0.004,8,24),
   new T.MeshStandardMaterial({color:PEN_COLOR,roughness:0.6}));m.position.copy(v3(T,p.position));if(p.direction==='vertical')m.rotation.x=Math.PI/2;
   add(group,pick,m,{kind:'el_pen',p})});
  el.terminals.forEach(t=>{if(!t.position)return;const s=(t.size||'').match(/^(\d+)x(\d+)(?:x(\d+))?/);
   const w=s?s[1]/1000:0.085,hgt=s?s[2]/1000:0.085,d=s&&s[3]?s[3]/1000:0.037;
   const run=el.runs.find(r=>r.to===t.ref||r.from===t.ref);
   // box flat on its wall: thin side along the wall normal (from the run's last horizontal segment)
   const seg=run?run.segments.filter(x=>!x.vertical).slice(-1)[0]:null;const alongX=seg?Math.abs(seg.to[0]-seg.from[0])>Math.abs(seg.to[1]-seg.from[1]):false;
   const g=alongX?new T.BoxGeometry(w,hgt,d):new T.BoxGeometry(d,hgt,w);
   const m=new T.Mesh(g,new T.MeshStandardMaterial({color:BOX_COLOR,roughness:0.6}));m.position.copy(v3(T,t.position));
   add(group,pick,m,{kind:'el_box',t,run})});
  el.runs.filter(r=>r.open_end).forEach(r=>{const p=r.points[0];
   const m=new T.Mesh(new T.TorusGeometry(0.06,r.cable_diameter/2,8,24),new T.MeshStandardMaterial({color:r.color,roughness:0.5}));
   m.position.copy(v3(T,[p[0],p[1],p[2]-0.06]));add(group,pick,m,{kind:'el_open',r})})}
 function tip(u){const est=x=>x?' (geschätzt)':'';
  if(u.kind==='el_cable'){const r=u.r;return [[r.name+est(r.estimated),r.label+(r.conduit?' im Schutzrohr '+(r.conduit.size||''):''),
   'Abschnitt '+(u.i+1)+'/'+r.segments.length+': '+m2(u.s.length),'Rohr '+m2(r.length)+', Kabel '+m2(r.cable_length)+' inkl. Vorrat'],r.color]}
  if(u.kind==='el_pen'){const p=u.p;return [['Durchführung '+p.element_name+est(p.estimated),p.run_name,'Bohrung Ø '+cm(p.core_drill)],PEN_COLOR]}
  if(u.kind==='el_part'){const p=u.p;return [[(PART_DE[p.fitting_type]||p.fitting_type)+': '+(p.name||p.component||'–')+est(p.estimated),p.run_name,
   p.angle!=null?'Winkel '+p.angle+'°':'']]}
  if(u.kind==='el_box'){const t=u.t;return [[t.name+est(t.estimated),t.component_name||t.component,u.run?u.run.label:'',
   'Höhe '+m2(t.position[2])],BOX_COLOR]}
  if(u.kind==='el_open'){const r=u.r;return [['Offenes Ende: '+r.name,r.open_end.note||'','Vorrat '+m2(r.open_end.reserve)],r.color]}
  return null}
 // catalog ref of the TGA component behind a pick (tooltip link)
 return {build,tip,KINDS:['el_cable','el_part','el_pen','el_box','el_open'],COMP_OF:{el_cable:u=>u.r.component,el_part:u=>u.p.component,el_box:u=>u.t.component}}})();
