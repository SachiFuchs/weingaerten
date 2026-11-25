// /haus3d: three.js scene of the house  walls, floors, roof, stairs, coverings, heating and the other TGA layers, tooltips.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/OrbitControls.js';
const H=JSON.parse(document.getElementById('house').textContent);
const box=document.getElementById('scene3d');
const hk='weingaerten.scene3d.height';
box.style.height=(localStorage.getItem(hk)||Math.max(320,Math.round(innerHeight*0.6)))+'px';
const renderer=new THREE.WebGLRenderer({antialias:true});renderer.shadowMap.enabled=true;renderer.localClippingEnabled=true;
renderer.setPixelRatio(devicePixelRatio);box.appendChild(renderer.domElement);
const labels=document.createElement('div');labels.style.cssText='position:absolute;inset:0;pointer-events:none';box.appendChild(labels);
const scene=new THREE.Scene();scene.background=new THREE.Color('#EEF2F6');
const bb=H.bbox||[0,0,10,10];const cx=(bb[0]+bb[2])/2,cz=(bb[1]+bb[3])/2;
const st=(H.storeys||[])[0]||{walls:[],rooms:[],elevation:0,height:2.75};
// every storey is drawn (checkbox per storey); walls, structure and ceilings carry absolute z, floors their storey elevation
const ALL=H.storeys||[];const allOf=k=>ALL.flatMap(s=>(s[k]||[]).map(e=>Object.assign(e,{_sid:s.id})));
const WALLS=allOf('walls'),STRUCT=allOf('structure'),CEILS=allOf('ceilings');
const ROOF=ALL.flatMap(s=>s.roof_structure?s.roof_structure.members.map(m=>Object.assign(m,{_sid:s.id,_est:s.roof_structure.estimated})):[]);
// roof covering: per storey its faces (layers between bottom and top plane) with holes for the openings
const COVER=ALL.filter(s=>s.roof_covering).map(s=>Object.assign(s.roof_covering,{_sid:s.id,_axis:s.roof&&s.roof.ridge_direction==='west_east'?1:0}));
const planXY=(c,a,b)=>c._axis===0?[a,b]:[b,a];
const rectOf=(c,o)=>[planXY(c,o.across[0],o.along[0]),planXY(c,o.across[1],o.along[0]),planXY(c,o.across[1],o.along[1]),planXY(c,o.across[0],o.along[1])];
const zAt=(pl,pts,f)=>f(...pts.map(p=>pl[0]*p[0]+pl[1]*p[1]+pl[2]));
const STAIRS=ALL.flatMap(s=>(s.stairs||[]).flatMap(t=>t.parts.map(p=>Object.assign(p,{_sid:s.id,_stair:t}))));
// light wells in front of basement windows: concrete parts and the grating as prisms
const WELLS=ALL.flatMap(s=>(s.light_wells||[]).flatMap(w=>w.parts.map(p=>Object.assign(p,{_sid:s.id,_well:w}))));
const FACADE=ALL.filter(s=>s.facade).flatMap(s=>s.facade.parts.map(p=>Object.assign(p,{_sid:s.id,_f:s.facade})));
// interior linings (Innendämmung) in front of wall faces: one prism per layer and piece
const LININGS=ALL.flatMap(s=>(s.linings||[]).flatMap(l=>l.parts.map(p=>Object.assign(p,{_sid:s.id,_lin:l}))));
// walls clad with boards: their outer layers up to the board layer are drawn as the board rows instead of slabs
const CLAD=new Map(FACADE.map(p=>[p._sid+'/'+p.wall,p.layer||0]));
// floor build-ups (layers per room rect) and floor heating (pipes as lines in the heated layer)
const FLOORS=allOf('floors');const HEAT=ALL.filter(s=>s.heating).map(s=>Object.assign(s.heating,{_sid:s.id}));
// every heating pipe is drawn in one orange, whatever the circuit
const PIPE_COLOR='#FF7A00';
const floorOf=(s,name)=>(s.floors||[]).find(f=>f.rooms.some(x=>x.name===name));
const storeyBox=id=>document.getElementById('geschoss3d-'+id);
const shown=id=>{const b=storeyBox(id);return !b||b.checked};
const span=Math.max(bb[2]-bb[0],bb[3]-bb[1]);
const camera=new THREE.PerspectiveCamera(45,1,0.05,500);
const target=new THREE.Vector3(cx,st.elevation+st.height/2,cz);
const dist=span*1.6+4;const pol=35*Math.PI/180;
camera.position.set(cx+dist*Math.sin(pol)*0.7071,target.y+dist*Math.cos(pol),cz+dist*Math.sin(pol)*0.7071);
const controls=new OrbitControls(camera,renderer.domElement);controls.target.copy(target);controls.enableDamping=true;
controls.maxPolarAngle=85*Math.PI/180;controls.minDistance=1;controls.maxDistance=80;
// wheel: every notch changes the camera distance by exactly 10 %
controls.enableZoom=false;
renderer.domElement.addEventListener('wheel',e=>{e.preventDefault();if(!e.deltaY)return;
 // Ctrl + wheel: move camera and target together along the view direction (0.5 m per notch)
 if(e.ctrlKey){const dir=new THREE.Vector3();camera.getWorldDirection(dir);
  const mv=dir.multiplyScalar(e.deltaY>0?-0.5:0.5);camera.position.add(mv);controls.target.add(mv);controls.update();return}
 const off=camera.position.clone().sub(controls.target);const d=off.length();
 const nd=Math.min(controls.maxDistance,Math.max(controls.minDistance,d*(e.deltaY>0?1.1:1/1.1)));
 camera.position.copy(controls.target).add(off.multiplyScalar(nd/d));controls.update()},{passive:false});
// Alt + left drag: look around from the camera position (target turns around the camera, camera stays)
(function(){const el=renderer.domElement,host=el.parentElement||el;let last=null;
 host.addEventListener('pointerdown',e=>{if(!e.altKey||e.button!==0||e.target!==el)return;
  e.preventDefault();e.stopPropagation();last=[e.clientX,e.clientY];controls.enabled=false;el.setPointerCapture(e.pointerId)},true);
 el.addEventListener('pointermove',e=>{if(!last)return;const dx=e.clientX-last[0],dy=e.clientY-last[1];last=[e.clientX,e.clientY];
  const off=controls.target.clone().sub(camera.position);const s=new THREE.Spherical().setFromVector3(off);
  s.theta-=dx*0.005;s.phi=Math.min(Math.PI-controls.minPolarAngle,Math.max(Math.PI-controls.maxPolarAngle,s.phi+dy*0.005));
  controls.target.copy(camera.position).add(new THREE.Vector3().setFromSpherical(s))});
 const end=e=>{if(!last)return;last=null;controls.enabled=true;controls.update();try{el.releasePointerCapture(e.pointerId)}catch(_){}};
 el.addEventListener('pointerup',end);el.addEventListener('pointercancel',end)})();
scene.add(new THREE.HemisphereLight('#FFFFFF','#B9C4AE',0.9));
const sun=new THREE.DirectionalLight('#FFFFFF',1.4);
sun.position.set(cx-span,span*1.2,cz+span);sun.target.position.set(cx,0,cz);scene.add(sun.target);
sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);const sc=sun.shadow.camera;sc.left=sc.bottom=-span*1.2;sc.right=sc.top=span*1.2;sc.far=span*5;scene.add(sun);
const M=H.materials||{};const col=r=>(M[r]&&M[r].appearance&&M[r].appearance.color)||'#cccccc';
const rough=r=>(M[r]&&M[r].appearance&&M[r].appearance.roughness!=null)?M[r].appearance.roughness:0.9;
const mname=r=>(M[r]&&M[r].name)||r||'–';
const cmf=t=>{let s=(t*100).toFixed(2).replace(/0+$/,'').replace(/\.$/,'');return s.replace('.',',')+' cm'};
const F=H.foundation;const groundY=F?Math.min(...F.layers.map(l=>l.z0))-0.01:-0.3;
const g=new THREE.Mesh(new THREE.PlaneGeometry(span*8,span*8),new THREE.MeshStandardMaterial({color:'#DDE8D0',roughness:1}));
g.rotation.x=-Math.PI/2;g.position.set(cx,groundY,cz);g.receiveShadow=true;scene.add(g);
// a shown storey below the foundation top (basement) is seen through a transparent ground
const below=ALL.filter(s=>s.elevation<(F?F.top:0)-1e-6);
// the foundation slab (ceiling of the basement) is hidden when no storey on top of it is shown
const foundMeshes=[];const above=ALL.filter(s=>!below.includes(s));
function updateGround(){const see=below.some(s=>shown(s.id));const fv=!below.length||above.some(s=>shown(s.id));foundMeshes.forEach(m=>m.visible=fv);g.material.transparent=see;g.material.opacity=see?0.35:1;g.material.depthWrite=!see;g.material.needsUpdate=true}
const pick=[];
if(F){const fp=F.polygon||(()=>{const [x,y,w,h]=F.rect;return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]})();F.layers.forEach(l=>{const m=new THREE.Mesh(prism(fp,l.z0,l.z1-l.z0,null,null,F.cutouts),
 new THREE.MeshStandardMaterial({color:col(l.material),roughness:rough(l.material)}));
 m.receiveShadow=true;m.userData={kind:'found',l};scene.add(m);pick.push(m);foundMeshes.push(m)})}
const floors=ALL.flatMap(s=>[...(s.rooms||[]),...(s.outdoor_areas||[])].map(r=>{const fl=!r.polygon&&r.rect&&floorOf(s,r.name);
 return Object.assign(r,{_z:r.polygon?r.floor_top:(fl?fl.z_top:s.elevation),_sid:s.id,_heated:!!(s.heating&&(s.floors||[]).some(f=>f.id===s.heating.floor&&f.rooms.some(x=>x.name===r.name)))})}));
// rooms are polygons: plane = the polygon, label in its largest rect (inside L-shaped rooms)
floors.forEach(r=>{const pl=r.polygon||(()=>{const [x,y,w,h]=r.rect;return [[x,y],[x+w,y],[x+w,y+h],[x,y+h]]})();
 const [x,y,w,h]=r.rects?r.rects.reduce((a,b)=>b[2]*b[3]>a[2]*a[3]?b:a):r.rect;
 const m=new THREE.Mesh(prism(pl,r._z+0.001,0.002),new THREE.MeshStandardMaterial({color:'#E9DCC3',roughness:0.8}));
 m.receiveShadow=true;m.userData={kind:'room',r};r._mesh=m;scene.add(m);pick.push(m);
 const d=document.createElement('div');d.style.cssText='position:absolute;transform:translate(-50%,-50%);font-size:12px;background:rgba(255,255,255,.75);padding:2px 6px;border-radius:3px;white-space:nowrap';
 const b=document.createElement('b');b.textContent=(r.number?r.number+' ':'')+r.name;d.appendChild(b);d.appendChild(document.createTextNode(' '+r.area.toFixed(2).replace('.',',')+' m²'));
 labels.appendChild(d);r._label=d;r._pos=new THREE.Vector3(x+w/2,r._z+0.05,y+h/2)});
// labels toggle (Beschriftungen): shows / hides all room and outdoor labels
const beschr=document.getElementById('beschr3d');beschr.checked=localStorage.getItem('weingaerten.beschriftung')!=='0';
const applyBeschr=()=>{labels.style.display=beschr.checked?'block':'none';localStorage.setItem('weingaerten.beschriftung',beschr.checked?'1':'0')};
beschr.addEventListener('change',applyBeschr);applyBeschr();
function prism(pts,z0,h,plane,bottom,holes){const s=new THREE.Shape();pts.forEach((p,i)=>i?s.lineTo(p[0],-p[1]):s.moveTo(p[0],-p[1]));s.closePath();
 (holes||[]).forEach(hp=>{const hl=new THREE.Path();hp.forEach((p,i)=>i?hl.lineTo(p[0],-p[1]):hl.moveTo(p[0],-p[1]));hl.closePath();s.holes.push(hl)});
 const geo=new THREE.ExtrudeGeometry(s,{depth:h,bevelEnabled:false});geo.rotateX(-Math.PI/2);geo.translate(0,z0,0);
 // sloped top / bottom (roof wall, rafter): move the top / bottom vertices onto the plane z = a*x + b*y + c (three.js y = height, z = plan y)
 if(plane||bottom){const pos=geo.attributes.position;for(let i=0;i<pos.count;i++){const y=pos.getY(i),pl=y>z0+h-1e-6?plane:(y<z0+1e-6?bottom:null);
  if(pl)pos.setY(i,pl[0]*pos.getX(i)+pl[1]*pos.getZ(i)+pl[2])}
  pos.needsUpdate=true;geo.computeVertexNormals()}
 return geo}
const PART_DE={frame:'Rahmen',mullion:'Pfosten',sash:'Flügel',glass:'Glas',leaf:'Türblatt'};
const STRUCT_DE={beam:'Unterzug',post:'Stütze'};
let wallGroup=null;const opMeshes={};
const transp=document.getElementById('transp3d'),decke=document.getElementById('decke3d');
transp.checked=localStorage.getItem('weingaerten.transp')==='1';decke.checked=localStorage.getItem('weingaerten.decke')!=='0';
const stuhl=document.getElementById('dachstuhl3d');if(stuhl)stuhl.checked=localStorage.getItem('weingaerten.dachstuhl')!=='0';
const dach=document.getElementById('dach3d');if(dach)dach.checked=localStorage.getItem('weingaerten.dach')!=='0';
const heiz=document.getElementById('heizung3d');if(heiz)heiz.checked=localStorage.getItem('weingaerten.heizung')!=='0';
const heizOn=()=>!!(heiz&&heiz.checked);const abw=document.getElementById('abwasser3d');if(abw)abw.checked=localStorage.getItem('weingaerten.abwasser')!=='0';const zuw=document.getElementById('zuwasser3d');if(zuw)zuw.checked=localStorage.getItem('weingaerten.zuwasser')!=='0';const elk=document.getElementById('elektrik3d');if(elk)elk.checked=localStorage.getItem('weingaerten.elektrik')!=='0';const ein=document.getElementById('einbau3d');if(ein)ein.checked=localStorage.getItem('weingaerten.einbau')!=='0';const whz=document.getElementById('wandheizung3d');if(whz)whz.checked=localStorage.getItem('weingaerten.wandheizung')!=='0';
const daemm=document.getElementById('daemmung3d');if(daemm)daemm.checked=localStorage.getItem('weingaerten.daemmung')!=='0';
const belag=document.getElementById('belag3d');if(belag)belag.checked=localStorage.getItem('weingaerten.belag')!=='0';
const schacht=document.getElementById('schacht3d');if(schacht)schacht.checked=localStorage.getItem('weingaerten.schacht')!=='0';
ALL.forEach(s=>{const b=storeyBox(s.id);if(b)b.checked=localStorage.getItem('weingaerten.geschoss.'+s.id)!=='0'});
function buildWalls(){if(wallGroup){scene.remove(wallGroup);wallGroup.traverse(o=>{if(o.geometry)o.geometry.dispose()});
 for(let i=pick.length-1;i>=0;i--)if(['layer','part','reveal','ceil','joist','struct','roofm','roofc','roofo','stair','well','facade','lining','floor','pipe','manifold',...Waste3d.KINDS,...Water3d.KINDS,...Electric3d.KINDS,...Parts3d.KINDS,...Room3d.KINDS,...WallHeat3d.KINDS].includes(pick[i].userData.kind))pick.splice(i,1)}
 for(const k in opMeshes)delete opMeshes[k];updateGround();
 floors.forEach(r=>{r._mesh.visible=shown(r._sid)&&!(heizOn()&&r._heated)});
 wallGroup=new THREE.Group();const op=transp.checked;
 WALLS.filter(w=>shown(w._sid)).forEach(w=>{const nL=w.layers.length;
  w.layers.forEach((l,i)=>{if(CLAD.has(w._sid+'/'+w.id)&&i<=CLAD.get(w._sid+'/'+w.id))return;(l.pieces||[]).forEach(pc=>{const z1=pc.z1,tp=pc.top_plane;
   const mat=new THREE.MeshStandardMaterial({color:col(l.material),roughness:rough(l.material),metalness:0,transparent:op,opacity:op?0.3:1});
   const m=new THREE.Mesh(prism(pc.footprint,pc.z0,z1-pc.z0,tp),mat);m.castShadow=!op;m.receiveShadow=true;
   m.userData={kind:'layer',w,l,i,n:nL};wallGroup.add(m);pick.push(m);
   if(i===0||i===nL-1){wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(prism(pc.footprint,pc.z0,z1-pc.z0,tp)),
    new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.35})))}})});
  (w.openings||[]).forEach(o=>{opMeshes[o.id]=[];
   (o.reveals||[]).forEach(rv=>rv.quads.forEach(q=>{const geo=new THREE.BufferGeometry();const p=q.map(v=>[v[0],v[2],v[1]]);
    geo.setAttribute('position',new THREE.Float32BufferAttribute([...p[0],...p[1],...p[2],...p[0],...p[2],...p[3]],3));geo.computeVertexNormals();
    const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:col(rv.material),side:THREE.DoubleSide,roughness:0.9,polygonOffset:true,polygonOffsetFactor:-1}));
    m.userData={kind:'reveal',w,o,rv};wallGroup.add(m);pick.push(m)}));
   (o.parts||[]).forEach(p=>{const glass=p.kind==='glass';
    const mat=new THREE.MeshStandardMaterial({color:col(p.material),roughness:rough(p.material),metalness:glass?0.1:0,transparent:glass,opacity:glass?0.35:1});
    const m=new THREE.Mesh(new THREE.BoxGeometry(Math.max(p.size[0],1e-4),Math.max(p.size[2],1e-4),Math.max(p.size[1],1e-4)),mat);
    m.position.set(p.center[0],p.center[2],p.center[1]);m.rotation.y=-p.direction*Math.PI/180;m.castShadow=!glass;
    m.userData={kind:'part',w,o,p};wallGroup.add(m);pick.push(m);opMeshes[o.id].push(m)})})});
 STRUCT.filter(s=>shown(s._sid)).forEach(s=>{const z1=s.z1;
  const m=new THREE.Mesh(prism(s.footprint,s.z0,z1-s.z0),new THREE.MeshStandardMaterial({color:s.color||col(s.material),roughness:rough(s.material),transparent:op,opacity:op?0.3:1}));
  m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'struct',s};wallGroup.add(m);pick.push(m)});
 if(decke.checked)CEILS.filter(c=>shown(c._sid)).forEach(c=>{
  c.layers.forEach((l,i)=>{const m=new THREE.Mesh(prism(c.polygon,l.z0,l.z1-l.z0,null,null,Room3d.ceilingHoles(H,'storey:'+c._sid,c.polygon)),new THREE.MeshStandardMaterial({color:col(l.material),roughness:rough(l.material),transparent:op,opacity:op?0.3:1}));
   m.receiveShadow=true;m.castShadow=!op;m.userData={kind:'ceil',c,l,i,n:c.layers.length};wallGroup.add(m);pick.push(m)});
  const j=c.joists;if(j)j.beams.forEach((b,i)=>{const m=new THREE.Mesh(prism(b.polygon,j.z0,j.z1-j.z0),new THREE.MeshStandardMaterial({color:col(j.material),roughness:rough(j.material),transparent:op,opacity:op?0.3:1}));
   m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'joist',c,j,b,i};wallGroup.add(m);pick.push(m)})});
 if(stuhl&&stuhl.checked)ROOF.filter(r=>shown(r._sid)).forEach(r=>{
  const geo=prism(r.footprint,r.z0,r.z1-r.z0,r.top_plane,r.bottom_plane);
  const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:col(r.material),roughness:rough(r.material),transparent:op,opacity:op?0.3:1}));
  m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'roofm',r};wallGroup.add(m);pick.push(m);
  wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.35})))});
 if(dach&&dach.checked)COVER.filter(c=>shown(c._sid)).forEach(c=>{
  c.faces.forEach(f=>{const holes=c.openings.filter(o=>o.slope===f.id).map(o=>rectOf(c,o));
   f.layers.forEach((l,i)=>{const z0=zAt(l.bottom_plane,f.polygon,Math.min),z1=zAt(l.top_plane,f.polygon,Math.max);
    const geo=prism(f.polygon,z0,z1-z0,l.top_plane,l.bottom_plane,holes);
    const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:col(l.material),roughness:rough(l.material),transparent:op,opacity:op?0.3:1}));
    m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'roofc',c,f,l,i,n:f.layers.length};wallGroup.add(m);pick.push(m);
    if(i===0)wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.35})))})});
  c.openings.forEach(o=>{const pts=rectOf(c,o),f=c.faces.find(x=>x.id===o.slope);let geo,mat;
   if(o.kind==='chimney'){geo=prism(pts,o.z0,o.z1-o.z0);mat=new THREE.MeshStandardMaterial({color:'#9B4A3A',roughness:0.9})}
   else{const top=f.layers[0].top_plane,base=f.base_plane;const z0=zAt(base,pts,Math.min),z1=zAt(top,pts,Math.max)+0.02;
    geo=prism(pts,z0,z1-z0,[top[0],top[1],top[2]+0.02],base);mat=new THREE.MeshStandardMaterial({color:col('material:glass'),roughness:0.1,metalness:0.1,transparent:true,opacity:0.45})}
   const m=new THREE.Mesh(geo,mat);m.userData={kind:'roofo',c,o};wallGroup.add(m);pick.push(m)})});
 STAIRS.filter(p=>shown(p._sid)).forEach(p=>{const geo=prism(p.footprint,p.z0,p.z1-p.z0,p.top_plane,p.bottom_plane);
  const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:p.color||col(p.material),roughness:rough(p.material),transparent:op,opacity:op?0.3:1}));
  m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'stair',p};wallGroup.add(m);pick.push(m);
  wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.3})))});
 WELLS.filter(p=>shown(p._sid)).forEach(p=>{const grate=p.kind==='grating';const geo=prism(p.footprint,p.z0,p.z1-p.z0);
  const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:p.color||col(p.material),roughness:rough(p.material),metalness:grate?0.4:0,transparent:op||grate,opacity:op?0.3:(grate?0.6:1)}));
  m.castShadow=!op&&!grate;m.receiveShadow=true;m.userData={kind:'well',p};wallGroup.add(m);pick.push(m);
  wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.3})))});
 FACADE.filter(p=>shown(p._sid)).forEach(p=>{const geo=prism(p.footprint,p.z0,p.z1-p.z0,p.top_plane);
  const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:p.color||col(p.material),roughness:0.75,transparent:op,opacity:op?0.3:1}));
  m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'facade',p};wallGroup.add(m);pick.push(m);
  wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#2E3A4A',transparent:true,opacity:0.35})))});
 if(daemm&&daemm.checked)LININGS.filter(p=>shown(p._sid)).forEach(p=>{const geo=prism(p.footprint,p.z0,p.z1-p.z0,p.top_plane);
  const m=new THREE.Mesh(geo,new THREE.MeshStandardMaterial({color:p.color||col(p.material),roughness:rough(p.material),transparent:op,opacity:op?0.3:1}));
  m.castShadow=!op;m.receiveShadow=true;m.userData={kind:'lining',p};wallGroup.add(m);pick.push(m);
  if(p.layer===p._lin.layers.length-1)wallGroup.add(new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:'#333333',transparent:true,opacity:0.3})))});
 buildFloors(op);buildHeating();if(abw&&abw.checked)Waste3d.build(THREE,wallGroup,pick,H.waste_water);if(zuw&&zuw.checked)Water3d.build(THREE,wallGroup,pick,H.water_supply);if(elk&&elk.checked)Electric3d.build(THREE,wallGroup,pick,H.electrical);if(ein&&ein.checked)Parts3d.build(THREE,wallGroup,pick,H.installation);if(whz&&whz.checked)WallHeat3d.build(THREE,wallGroup,pick,ALL,shown);
 Room3d.build(THREE,wallGroup,pick,H,prism,shown,{col,transparent:op,coverings:!!(belag&&belag.checked),shafts:!!(schacht&&schacht.checked)});
 scene.add(wallGroup)}
// with the heating shown, the layers above the pipe level are left out so the pipes can be seen from above
function buildFloors(op){FLOORS.filter(f=>shown(f._sid)).forEach(f=>{const heated=f.layers.findIndex(l=>l.heated);
 const cut=heizOn()&&HEAT.some(x=>x._sid===f._sid&&x.floor===f.id)&&heated>=0?heated+1:0;
 f.rooms.forEach(room=>Room3d.minus(room.rects,Room3d.shaftRects(H,'storey:'+f._sid,'floor')).forEach(([x,y,w,h])=>f.layers.forEach((l,i)=>{if(i<cut)return;
  const m=new THREE.Mesh(prism([[x,y],[x+w,y],[x+w,y+h],[x,y+h]],l.z0,l.z1-l.z0),new THREE.MeshStandardMaterial({color:l.color||col(l.material),roughness:rough(l.material),transparent:op,opacity:op?0.3:1}));
  m.receiveShadow=true;m.userData={kind:'floor',f,l,i,n:f.layers.length,room};wallGroup.add(m);pick.push(m)})))})}
function pipeLine(pts,z,color,data){const geo=new THREE.BufferGeometry().setFromPoints(pts.map(p=>new THREE.Vector3(p[0],z,p[1])));
 const m=new THREE.Line(geo,new THREE.LineBasicMaterial({color}));m.userData=data;wallGroup.add(m);pick.push(m)}
function buildHeating(){if(!heizOn())return;HEAT.filter(x=>shown(x._sid)).forEach(x=>{
 x.circuits.forEach(c=>{const color=PIPE_COLOR;pipeLine(c.field,x.z,color,{kind:'pipe',x,c,part:'Verlegefläche'});
  pipeLine(c.feed_supply,x.z,color,{kind:'pipe',x,c,part:'Anbindung Vorlauf'});pipeLine(c.feed_return,x.z,color,{kind:'pipe',x,c,part:'Anbindung Rücklauf'})});
 const mf=x.manifold,[px,py]=mf.position,w=mf.width;
 const m=new THREE.Mesh(prism([[px-w/2,py-0.04],[px+w/2,py-0.04],[px+w/2,py+0.04],[px-w/2,py+0.04]],x.z,0.45),new THREE.MeshStandardMaterial({color:'#B8BEC6',roughness:0.4,metalness:0.4}));
 m.castShadow=true;m.userData={kind:'manifold',x};wallGroup.add(m);pick.push(m)})}
buildWalls();
ALL.forEach(s=>{const b=storeyBox(s.id);if(b)b.onchange=()=>{localStorage.setItem('weingaerten.geschoss.'+s.id,b.checked?'1':'0');buildWalls()}});
transp.onchange=()=>{localStorage.setItem('weingaerten.transp',transp.checked?'1':'0');buildWalls()};
decke.onchange=()=>{localStorage.setItem('weingaerten.decke',decke.checked?'1':'0');buildWalls()};
if(stuhl)stuhl.onchange=()=>{localStorage.setItem('weingaerten.dachstuhl',stuhl.checked?'1':'0');buildWalls()};
if(dach)dach.onchange=()=>{localStorage.setItem('weingaerten.dach',dach.checked?'1':'0');buildWalls()};
if(heiz)heiz.onchange=()=>{localStorage.setItem('weingaerten.heizung',heiz.checked?'1':'0');buildWalls()};if(abw)abw.onchange=()=>{localStorage.setItem('weingaerten.abwasser',abw.checked?'1':'0');buildWalls()};if(zuw)zuw.onchange=()=>{localStorage.setItem('weingaerten.zuwasser',zuw.checked?'1':'0');buildWalls()};if(elk)elk.onchange=()=>{localStorage.setItem('weingaerten.elektrik',elk.checked?'1':'0');buildWalls()};if(ein)ein.onchange=()=>{localStorage.setItem('weingaerten.einbau',ein.checked?'1':'0');buildWalls()};if(whz)whz.onchange=()=>{localStorage.setItem('weingaerten.wandheizung',whz.checked?'1':'0');buildWalls()};
if(daemm)daemm.onchange=()=>{localStorage.setItem('weingaerten.daemmung',daemm.checked?'1':'0');buildWalls()};
if(belag)belag.onchange=()=>{localStorage.setItem('weingaerten.belag',belag.checked?'1':'0');buildWalls()};
if(schacht)schacht.onchange=()=>{localStorage.setItem('weingaerten.schacht',schacht.checked?'1':'0');buildWalls()};
const asm=H.assemblies||{};
const ray=new THREE.Raycaster(),mouse=new THREE.Vector2();let hot=null;ray.params.Line.threshold=0.02;
function unhot(){if(hot){hot.material.emissive.set('#000000');hot=null}}
renderer.domElement.addEventListener('pointermove',e=>{if(Detail3d.held(e))return;const r=renderer.domElement.getBoundingClientRect();
 mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(mouse,camera);
 const hits=ray.intersectObjects(pick,false).filter(h=>h.object.visible);
 const o=hits[0]?hits[0].object:null;
 if(hot&&hot!==o)unhot();
 if(!o){Detail3d.idle();return}
 if(o.userData.kind!=='room'&&o.material.emissive){o.material.emissive.set('#1C69D4');o.material.emissiveIntensity=0.35;hot=o}
 const u=o.userData;
 if(u.kind==='layer')showTip(e,[u.w.name||u.w.id,(asm[u.w.assembly]||{}).name||u.w.assembly,'Schicht '+(u.i+1)+'/'+u.n+': '+mname(u.l.material),'Dicke '+cmf(u.l.thickness)],col(u.l.material));
 else if(u.kind==='part')showTip(e,[u.o.name||u.o.component,'Öffnung '+u.o.id+' in '+(u.w.name||u.w.id),(PART_DE[u.p.kind]||u.p.kind)+': '+mname(u.p.material),
  cmf(u.o.params.width).replace(' cm','')+' × '+cmf(u.o.params.height)],col(u.p.material));
 else if(u.kind==='reveal')showTip(e,['Laibung','Öffnung '+u.o.id+' in '+(u.w.name||u.w.id),mname(u.rv.material)],col(u.rv.material));
 else if(u.kind==='found')showTip(e,['Bodenplatte',mname(u.l.material),'Dicke '+cmf(u.l.thickness)],col(u.l.material));
 else if(u.kind==='ceil')showTip(e,[u.c.name||u.c.id,(asm[u.c.assembly]||{}).name||u.c.assembly,'Schicht '+(u.i+1)+'/'+u.n+': '+mname(u.l.material),'Dicke '+cmf(u.l.thickness)+(u.l.direction?(u.l.direction==='south_north'?', Süd-Nord':', West-Ost'):'')],col(u.l.material));
 else if(u.kind==='joist')showTip(e,['Deckenbalken '+(u.i+1)+'/'+u.j.count+(u.j.estimated?' (geschätzt)':''),mname(u.j.material),cmf(u.j.width).replace(' cm','')+' × '+cmf(u.j.height)+', Abstand '+cmf(u.j.spacing_actual),'Länge '+u.b.length.toFixed(2).replace('.',',')+' m'],col(u.j.material));
 else if(u.kind==='roofm'){const same=ROOF.filter(x=>x._sid===u.r._sid&&x.kind===u.r.kind);
  showTip(e,[u.r.name+' '+(same.indexOf(u.r)+1)+'/'+same.length+(u.r._est?' (geschätzt)':''),mname(u.r.material),cmf(u.r.width).replace(' cm','')+' × '+cmf(u.r.height),'Länge '+u.r.length.toFixed(2).replace('.',',')+' m'],col(u.r.material))}
 else if(u.kind==='roofc')showTip(e,[u.f.name+(u.c.estimated?' (geschätzt)':''),(asm[u.c.assembly]||{}).name||u.c.assembly,'Schicht '+(u.i+1)+'/'+u.n+': '+mname(u.l.material),'Dicke '+cmf(u.l.thickness),'Fläche '+u.f.area_net.toFixed(2).replace('.',',')+' m²'],col(u.l.material));
 else if(u.kind==='roofo')showTip(e,[u.o.name||u.o.id,u.o.kind==='chimney'?'Kamin '+cmf(u.o.size[0]).replace(' cm','')+' × '+cmf(u.o.size[1]):'Dachfenster '+cmf(u.o.size[0]).replace(' cm','')+' × '+cmf(u.o.size[1]),u.o.rafters_cut.length?'Balkenwechsel: '+u.o.rafters_cut.join(', '):'']);
 else if(u.kind==='stair'){const t=u.p._stair;showTip(e,[(t.name||t.id)+(t.estimated?' (geschätzt)':''),u.p.name+' / '+t.counts[u.p.kind],mname(u.p.material)+(u.p.color?', gestrichen':''),'Steigung '+cmf(t.rise)+', Auftritt '+cmf(t.going)],u.p.color||col(u.p.material))}
 else if(u.kind==='facade'){const f=u.p._f;showTip(e,['Fassade Stülpschalung'+(f.estimated?' (geschätzt)':''),mname(f.material),'Wand '+u.p.wall+', Reihe '+u.p.row,'Stück '+u.p.length.toFixed(2).replace('.',',')+' m, Brett '+f.board.length.toFixed(1).replace('.',',')+' m × '+cmf(f.board.width)+' × '+cmf(f.board.thickness),'Überlappung '+cmf(f.overlap)],u.p.color||col(f.material))}
 else if(u.kind==='lining'){const l=u.p._lin,ly=l.layers[u.p.layer];showTip(e,['Innendämmung '+l.id+' – '+(l.wall_name||l.wall),(asm[l.assembly]||{}).name||l.name||l.assembly,'Schicht '+(u.p.layer+1)+'/'+l.layers.length+': '+mname(u.p.material),'Dicke '+cmf(ly.thickness)+', Fläche '+l.area.toFixed(2).replace('.',',')+' m²'],u.p.color||col(u.p.material))}
 else if(u.kind==='well'){const w=u.p._well;showTip(e,[(w.name||w.id)+(w.estimated?' (geschätzt)':''),u.p.name+': '+mname(u.p.material),'lichte Maße '+cmf(w.width).replace(' cm','')+' × '+cmf(w.projection).replace(' cm','')+' × '+cmf(w.depth),'vor Fenster '+w.opening],col(u.p.material))}
 else if(u.kind==='floor')showTip(e,[(u.f.name||u.f.id)+' – '+u.room.name,(asm[u.f.assembly]||{}).name||u.f.assembly,'Schicht '+(u.i+1)+'/'+u.n+': '+mname(u.l.material)+(u.l.heated?' (Rohrebene)':''),'Dicke '+cmf(u.l.thickness)],u.l.color||col(u.l.material));
 else if(u.kind==='pipe')showTip(e,[u.c.name||u.c.id,'Raum '+u.c.room+' – '+u.part,(u.c.pattern==='spiral'?'Schnecke':'Mäander')+', Abstand '+cmf(u.c.spacing)+', Ø '+cmf(u.x.pipe_diameter),'Rohrlänge '+u.c.length.toFixed(1).replace('.',',')+' m'+(u.x.estimated?' (geschätzt)':'')],PIPE_COLOR);
 else if(u.kind==='manifold')showTip(e,[u.x.manifold.name||'Heizkreisverteiler',u.x.name||'',u.x.circuits.length+' Heizkreise, '+u.x.length.toFixed(1).replace('.',',')+' m Rohr'+(u.x.estimated?' (geschätzt)':'')]);else if(Waste3d.KINDS.includes(u.kind)){const t=Waste3d.tip(u);showTip(e,t[0],t[1])}else if(Water3d.KINDS.includes(u.kind)){const t=Water3d.tip(u);showTip(e,t[0],t[1])}else if(Electric3d.KINDS.includes(u.kind)){const t=Electric3d.tip(u);showTip(e,t[0],t[1])}else if(Parts3d.KINDS.includes(u.kind)){const t=Parts3d.tip(u);showTip(e,t[0],t[1])}else if(Room3d.KINDS.includes(u.kind)){const t=Room3d.tip(u);showTip(e,t[0],t[1])}else if(WallHeat3d.KINDS.includes(u.kind)){const t=WallHeat3d.tip(u);showTip(e,t[0],t[1])}
 else if(u.kind==='struct')showTip(e,[(STRUCT_DE[u.s.kind]||u.s.kind)+': '+(u.s.name||u.s.id),mname(u.s.material),cmf(u.s.width).replace(' cm','')+' × '+cmf(u.s.kind==='beam'?u.s.height:Math.max(...u.s.footprint.map(p=>p[1]))-Math.min(...u.s.footprint.map(p=>p[1]))),'Länge '+u.s.length.toFixed(2).replace('.',',')+' m'],col(u.s.material));
 else showTip(e,[(u.r.number?u.r.number+' ':'')+u.r.name,u.r.area.toFixed(2).replace('.',',')+' m²'+(u.r.volume?', '+u.r.volume.toFixed(1).replace('.',',')+' m³':''),u.r.usage?u.r.usage+' '+(u.r.usage_name||''):'']);
 Detail3d.live(linksOf(u))});
renderer.domElement.addEventListener('pointerleave',e=>{if(Detail3d.inTip(e.relatedTarget))return;Detail3d.idle();unhot()});
renderer.domElement.addEventListener('dblclick',e=>{const r=renderer.domElement.getBoundingClientRect();
 mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);ray.setFromCamera(mouse,camera);
 const hit=ray.intersectObjects(pick,false).find(h=>h.object.visible);
 if(hit&&hit.object.userData.kind==='part'&&hit.object.userData.o.component)location.href='/katalog/bauteile#'+encodeURIComponent(hit.object.userData.o.component)});
// links to Wände / Material / Bauteil in the hover tooltip, opened in the detail panel
const MAT_OF={layer:u=>u.l.material,part:u=>u.p.material,reveal:u=>u.rv.material,found:u=>u.l.material,ceil:u=>u.l.material,
 joist:u=>u.j.material,roofm:u=>u.r.material,roofc:u=>u.l.material,stair:u=>u.p.material,well:u=>u.p.material,floor:u=>u.l.material,struct:u=>u.s.material,lining:u=>u.p.material,facade:u=>u.p._f.material,...Room3d.MAT_OF};
const COMP_OF={...Waste3d.COMP_OF,...Water3d.COMP_OF,...Electric3d.COMP_OF,...Parts3d.COMP_OF,...WallHeat3d.COMP_OF};
function linksOf(u){const links=[],enc=encodeURIComponent;
 if(u.w)links.push(['Wände','/waende?storey='+enc(u.w._sid)+'&embed=1#'+enc(u.w.id)]);
 if(u.kind==='lining')links.push(['Wände','/waende?storey='+enc(u.p._sid)+'&embed=1#'+enc(u.p.wall)]);
 if(Parts3d.KINDS.includes(u.kind)&&u.p.host)links.push(['Wände','/waende?storey='+enc(u.p.storey)+'&embed=1&part='+enc(u.p.id)+'#'+enc(u.p.host.wall)]);
 const m=MAT_OF[u.kind]?MAT_OF[u.kind](u):COMP_OF[u.kind]&&((u.r||u.p||u.t||{}).material);if(m)links.push(['Material','/katalog/materialien?embed=1#'+enc(m)]);
 const c=COMP_OF[u.kind]&&COMP_OF[u.kind](u);if(c)links.push(['TGA-Bauteil','/katalog/tga?embed=1#'+enc(c)]);
 if(u.kind==='part'&&u.o.component)links.push(['Bauteil','/katalog/bauteile?embed=1#'+enc(u.o.component)]);
 return links}
renderer.domElement.addEventListener('pointerdown',()=>Detail3d.idle());
const lg=document.getElementById('legend3d');const order=[];

const ln=document.createElement('p');ln.className='note';ln.textContent='Farbfeld = Darstellungsfarbe in der 3D-Ansicht';lg.appendChild(ln);
if(st.walls[0])st.walls[0].layers.forEach(l=>{if(!order.includes(l.material))order.push(l.material)});
Object.keys(M).sort((a,b)=>mname(a).localeCompare(mname(b))).forEach(k=>{if(!order.includes(k))order.push(k)});
const t=document.createElement('table');const hr=t.insertRow();['','Material','Kategorie'].forEach(x=>{const th=document.createElement('th');th.textContent=x;hr.appendChild(th)});
order.forEach(k=>{const tr=t.insertRow();const s=document.createElement('span');s.className='sw';s.style.background=col(k);tr.insertCell().appendChild(s);
 tr.insertCell().textContent=mname(k);tr.insertCell().textContent=(M[k]&&M[k].category)||''});lg.appendChild(t);
function size(){const w=box.clientWidth,h=box.clientHeight;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()}
new ResizeObserver(()=>{size();localStorage.setItem(hk,box.clientHeight)}).observe(box);size();
if(location.hash){const id=decodeURIComponent(location.hash.slice(1));
 WALLS.forEach(w=>(w.openings||[]).forEach(o=>{if(o.id!==id)return;const um=(o.rough.u0+o.rough.u1)/2,zm=(o.rough.zb+o.rough.zt)/2;
  const d=[Math.cos(w.direction*Math.PI/180),Math.sin(w.direction*Math.PI/180)];const n=w.normal_in;const s=w.reference==='outside_face'?0:(w.reference==='center'?w.thickness/2:w.thickness);
  const px=w.start[0]+d[0]*um+n[0]*(-s),py=w.start[1]+d[1]*um+n[1]*(-s);
  controls.target.set(px,w.z0+zm,py);camera.position.set(px-n[0]*4,w.z0+zm+0.8,py-n[1]*4);controls.update();
  (opMeshes[id]||[]).forEach(m=>{m.material.emissive.set('#1C69D4');m.material.emissiveIntensity=0.5});
  setTimeout(()=>(opMeshes[id]||[]).forEach(m=>m.material.emissive.set('#000000')),2000)}))}
const v=new THREE.Vector3();
(function loop(){requestAnimationFrame(loop);controls.update();renderer.render(scene,camera);
 floors.forEach(r=>{v.copy(r._pos).project(camera);const vis=v.z<1&&r._mesh.visible;r._label.style.display=vis?'block':'none';
  r._label.style.left=((v.x+1)/2*box.clientWidth)+'px';r._label.style.top=((1-v.y)/2*box.clientHeight)+'px'})})();
