// Installed parts (Einbauteile) in /haus3d: pipe legs as cylinders, boxes and inserts as flat boxes, ports as
// small spheres (red open, green connected, blue deliberately open / transfer to a neighbouring room).
// window.Parts3d.build(THREE, group, pick, inst) adds meshes; tip(u) returns tooltip lines for kinds ip_*.
window.Parts3d=(function(){
 const PORT={open:'#E53935',connected:'#2E7D32',open_ok:'#1C69D4',transfer:'#1C69D4'};
 const STATUS_DE={open:'offen',connected:'verbunden',open_ok:'bewusst offen',transfer:'Übergabe'};
 const TRANSFER_DE={beside:'Nachbarraum',above:'Geschoss oben',below:'Geschoss unten'};
 const v3=(T,p)=>new T.Vector3(p[0],p[2],p[1]);
 const m2=t=>t.toFixed(2).replace('.',',')+' m';
 function mat(T,color,opacity){return new T.MeshStandardMaterial({color,roughness:0.5,metalness:0.05,transparent:opacity<1,opacity,depthWrite:opacity>=1})}
 function cylinder(T,a,b,radius,color){const A=v3(T,a),B=v3(T,b),len=A.distanceTo(B);if(len<1e-4)return null;
  const m=new T.Mesh(new T.CylinderGeometry(radius,radius,len,18,1,false),mat(T,color,1));
  m.position.copy(A).add(B).multiplyScalar(0.5);m.quaternion.setFromUnitVectors(new T.Vector3(0,1,0),B.clone().sub(A).normalize());return m}
 function add(group,pick,m,data){if(!m)return;m.userData=data;group.add(m);pick.push(m)}
 // box along the part axes: x width, y height, w depth (the body lies behind the front face for boxes)
 function body(T,p){const [w,h,d]=p.size||[0.07,0.07,0.04];const ax=p.axes;
  const m=new T.Mesh(new T.BoxGeometry(w,h,d),mat(T,p.color,p.shape==='box'?0.85:1));
  // the plan -> scene swap of y and z mirrors, so the third axis is rebuilt as a cross product (box is symmetric)
  const X=v3(T,ax.x),Y=v3(T,ax.y),basis=new T.Matrix4().makeBasis(X,Y,X.clone().cross(Y));m.quaternion.setFromRotationMatrix(basis);
  const off=p.shape==='box'?-d/2:d/2;m.position.copy(v3(T,p.origin.map((c,i)=>c+ax.w[i]*off)));return m}
 function build(T,group,pick,inst){if(!inst||!inst.parts)return;
  inst.parts.forEach(p=>{const r=(p.outer_diameter||0.02)/2;
   if(p.shape==='box'||p.shape==='insert')add(group,pick,body(T,p),{kind:'ip_part',p});
   p.legs.forEach(([a,b])=>add(group,pick,cylinder(T,a,b,r,p.color),{kind:'ip_part',p}));
   // socket ends (Muffe) thicker: shows the flow direction of HT pipes (socket upstream)
   p.ports.forEach(q=>{if(q.gender!=='socket')return;const leg=p.legs.find(l=>l.some(x=>Math.hypot(x[0]-q.position[0],x[1]-q.position[1],x[2]-q.position[2])<1e-6));if(!leg)return;
    const o=Math.hypot(leg[0][0]-q.position[0],leg[0][1]-q.position[1],leg[0][2]-q.position[2])<1e-6?leg[1]:leg[0];
    const len=Math.hypot(o[0]-q.position[0],o[1]-q.position[1],o[2]-q.position[2]);if(len<1e-6)return;const k=Math.min(3*r,len/2)/len;
    add(group,pick,cylinder(T,q.position,q.position.map((v,i)=>v+(o[i]-v)*k),r*1.35,p.color),{kind:'ip_part',p})});
   if(p.shape==='valve'){const s=new T.Mesh(new T.SphereGeometry(r*1.8,16,12),mat(T,'#C62828',1));s.position.copy(v3(T,p.origin));add(group,pick,s,{kind:'ip_part',p})}
   p.ports.forEach(q=>{const s=new T.Mesh(new T.SphereGeometry(Math.max(0.008,r*0.6),12,8),mat(T,PORT[q.status],1));
    s.position.copy(v3(T,q.position));add(group,pick,s,{kind:'ip_port',p,q})})})}
 function tip(u){const p=u.p,est=p.estimated?' (geschätzt)':'';
  const lines=[(p.component_name||p.component)+est,'Teil '+p.id+(p.wall_name?' – '+p.wall_name:'')];
  if(p.length!=null)lines.push('Länge '+m2(p.length));
  if(u.kind==='ip_port'){const q=u.q;lines.push('Anschluss '+q.id+': '+STATUS_DE[q.status]+(q.transfer?' ('+TRANSFER_DE[q.transfer]+')':''),
   q.connected_to?'an '+q.connected_to:q.line.toUpperCase()+' DN '+q.dn);return [lines,PORT[q.status]]}
  const open=p.ports.filter(q=>q.status==='open').length;if(open)lines.push(open+' offene Anschlüsse');
  return [lines,p.color]}
 // catalog ref of the TGA component behind a pick (tooltip link)
 return {build,tip,KINDS:['ip_part','ip_port'],COMP_OF:{ip_part:u=>u.p.component,ip_port:u=>u.p.component}}})();
