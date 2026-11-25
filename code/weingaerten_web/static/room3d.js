// Room coverings (Beläge) and shafts (Schächte) in /haus3d.
// window.Room3d.build(THREE, group, pick, H, prism, shown, opt) adds meshes; minus(rects, holes) cuts axis-parallel
// rects [x, y, w, h] out of rects (floors, coverings, shaft holes); tip(u) returns tooltip lines for its KINDS.
window.Room3d=(function(){
 const SHAFT_COLOR='#8E24AA';
 const cm=t=>(t*100).toFixed(1).replace('.0','').replace('.',',')+' cm';
 const m2=a=>a.toFixed(2).replace('.',',')+' m²';
 // rect minus rect = up to four rects (left, right, top, bottom strips)
 function cut(r,h){const [x,y,w,hh]=r,x1=x+w,y1=y+hh;const hx0=Math.max(x,h[0]),hy0=Math.max(y,h[1]),hx1=Math.min(x1,h[0]+h[2]),hy1=Math.min(y1,h[1]+h[3]);
  if(hx1-hx0<1e-6||hy1-hy0<1e-6)return [r];const out=[];
  if(hx0-x>1e-6)out.push([x,y,hx0-x,hh]);if(x1-hx1>1e-6)out.push([hx1,y,x1-hx1,hh]);
  if(hy0-y>1e-6)out.push([hx0,y,hx1-hx0,hy0-y]);if(y1-hy1>1e-6)out.push([hx0,hy1,hx1-hx0,y1-hy1]);return out}
 function minus(rects,holes){let rs=rects.map(r=>r.slice());(holes||[]).forEach(h=>{rs=rs.flatMap(r=>cut(r,h))});return rs}
 const quad=([x,y,w,h])=>[[x,y],[x+w,y],[x+w,y+h],[x,y+h]];
 // shaft rects through the floor resp. the ceilings of a storey
 function shaftRects(H,ref,kind){return (H.shafts||[]).filter(s=>s[kind+'_storeys'].includes(ref)).flatMap(s=>s.rects)}
 function inside(p,poly){let c=false;for(let i=0,j=poly.length-1;i<poly.length;j=i++){const a=poly[i],b=poly[j];if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])c=!c}return c}
 // ceiling holes: shaft rects shrunk by 2 mm so they stay strictly inside the ceiling outline
 function ceilingHoles(H,ref,poly){return shaftRects(H,ref,'ceiling').map(([x,y,w,h])=>quad([x+0.002,y+0.002,w-0.004,h-0.004]))
  .filter(q=>q.every(p=>inside(p,poly)))}
 function mat(T,color,op){return new T.MeshStandardMaterial({color,roughness:0.8,transparent:op<1,opacity:op})}
 function floorCovering(T,group,pick,prism,s,room,c,col,op){const zones=room.coverings.filter(x=>x.surface==='floor'&&x.scope==='zone').flatMap(x=>x.rects);
  const rects=minus(c.scope==='room'?minus(room.rects,zones):c.rects,shaftRects(H0,s.ref,'floor'));
  c.layers.forEach((l,i)=>rects.forEach(r=>{const m=new T.Mesh(prism(quad(r),c.z0+l.offset,l.thickness),mat(T,l.color||col(l.material),op));
   m.receiveShadow=true;m.userData={kind:'cov_floor',s,room,c,l,i};group.add(m);pick.push(m)}))}
 function wallCovering(T,group,pick,prism,s,room,c,col,op){c.segments.forEach(g=>{const wall=s.walls.find(w=>w.id===g.wall);if(!wall)return;
  const [a,b]=g.line,L=Math.hypot(b[0]-a[0],b[1]-a[1]);if(L<1e-6)return;const d=[(b[0]-a[0])/L,(b[1]-a[1])/L];
  // the covering lies on the room side of the face line
  const mid=[(a[0]+b[0])/2,(a[1]+b[1])/2];let n=[-d[1],d[0]];if(!inside([mid[0]+n[0]*0.05,mid[1]+n[1]*0.05],room.polygon))n=[d[1],-d[0]];
  const holes=(wall.openings||[]).filter(o=>g.openings.includes(o.id)).map(o=>[o.rough.u0,o.rough.zb,o.rough.u1-o.rough.u0,o.rough.zt-o.rough.zb]);
  const pieces=minus([[g.u0,g.z0,g.u1-g.u0,g.z1-g.z0]],holes);const P=u=>[a[0]+d[0]*(u-g.u0),a[1]+d[1]*(u-g.u0)];
  c.layers.forEach((l,i)=>pieces.forEach(([u,z,w,h])=>{const p0=P(u),p1=P(u+w),t0=l.offset,t1=l.offset+l.thickness;
   const fp=[[p0[0]+n[0]*t0,p0[1]+n[1]*t0],[p1[0]+n[0]*t0,p1[1]+n[1]*t0],[p1[0]+n[0]*t1,p1[1]+n[1]*t1],[p0[0]+n[0]*t1,p0[1]+n[1]*t1]];
   const m=new T.Mesh(prism(fp,s.elevation+z,h),mat(T,l.color||col(l.material),op));m.castShadow=op===1;m.receiveShadow=true;
   m.userData={kind:'cov_wall',s,room,c,l,i};group.add(m);pick.push(m)}))})}
 let H0=null;
 function build(T,group,pick,H,prism,shown,opt){H0=H;const col=opt.col,op=opt.transparent?0.3:1;
  if(opt.coverings)(H.storeys||[]).filter(s=>shown(s.id)).forEach(s=>s.rooms.forEach(room=>(room.coverings||[]).forEach(c=>{
   if(c.surface==='floor')floorCovering(T,group,pick,prism,s,room,c,col,op);else wallCovering(T,group,pick,prism,s,room,c,col,op)})));
  if(opt.shafts){const el={};(H.storeys||[]).forEach(s=>el['storey:'+s.id]=s);
   (H.shafts||[]).forEach(sh=>{const top=el[sh.from_storey],bottom=el[sh.to_storey];if(!top||!bottom||!(shown(top.id)||shown(bottom.id)))return;
    const z0=bottom.elevation,z1=top.elevation+0.3;sh.rects.forEach(r=>{const m=new T.Mesh(prism(quad(r),z0,z1-z0),new T.MeshStandardMaterial({color:SHAFT_COLOR,transparent:true,opacity:0.3,depthWrite:false}));
     m.userData={kind:'shaft',sh};group.add(m);pick.push(m);group.add(new T.LineSegments(new T.EdgesGeometry(m.geometry),new T.LineBasicMaterial({color:SHAFT_COLOR})))})})}}
 function tip(u){if(u.kind==='shaft'){const sh=u.sh;return [['Schacht '+(sh.name||sh.id)+(sh.estimated?' (geschätzt)':''),
   'von '+sh.from_storey.replace('storey:','')+' bis '+sh.to_storey.replace('storey:',''),'Querschnitt '+m2(sh.area)+', geschnitten '+m2(sh.cut_area),
   sh.penetrations.length?'Leitungen: '+sh.penetrations.map(p=>p.replace('tga-run:','')).join(', '):''],SHAFT_COLOR]}
  const c=u.c;return [[(c.surface==='floor'?'Bodenbelag ':'Wandbelag ')+(c.name||c.id)+' – '+(u.room.number?u.room.number+' ':'')+u.room.name,c.assembly_name||c.assembly,
   'Schicht '+(u.i+1)+'/'+c.layers.length+', Dicke '+cm(u.l.thickness),c.surface==='floor'?'Fläche '+m2(c.area):'Länge '+c.length.toFixed(2).replace('.',',')+' m, Fläche '+m2(c.area)],u.l.color]}
 return {build,minus,shaftRects,ceilingHoles,tip,KINDS:['cov_floor','cov_wall','shaft'],MAT_OF:{cov_floor:u=>u.l.material,cov_wall:u=>u.l.material}};
})();
