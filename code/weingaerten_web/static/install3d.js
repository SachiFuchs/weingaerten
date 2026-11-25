// /waende: embedded 3D preview (right column, below the installation tree) of the shown wall with its installed parts.
// InstallUI calls window.Install3d.update(wall, face, parts, current, materials) after every draw; turn and tilt become visible.
import * as THREE from 'three';
import {OrbitControls} from 'three/addons/OrbitControls.js';
const box=document.getElementById('prev3d'),reset=document.getElementById('prev3dreset');
if(box){
 const renderer=new THREE.WebGLRenderer({antialias:true});renderer.setPixelRatio(devicePixelRatio);box.appendChild(renderer.domElement);
 const scene=new THREE.Scene();scene.background=new THREE.Color('#EEF2F6');
 scene.add(new THREE.AmbientLight(0xffffff,0.75));const sun=new THREE.DirectionalLight(0xffffff,0.8);sun.position.set(3,6,4);scene.add(sun);
 const camera=new THREE.PerspectiveCamera(40,1,0.01,100);const controls=new OrbitControls(camera,renderer.domElement);
 let content=new THREE.Group();scene.add(content);let view=null,frame=0,pending=null;
 const v3=p=>new THREE.Vector3(p[0],p[2],p[1]);
 const render=()=>renderer.render(scene,camera);controls.addEventListener('change',render);
 function size(){const w=box.clientWidth||260,h=box.clientHeight||280;renderer.setSize(w,h,false);renderer.domElement.style.width='100%';renderer.domElement.style.height='100%';camera.aspect=w/h;camera.updateProjectionMatrix();render()}
 new ResizeObserver(size).observe(box);
 // wall layers as translucent prisms in their material colours
 function prism(fp,z0,z1,color){const shape=new THREE.Shape(fp.map(p=>new THREE.Vector2(p[0],-p[1])));
  const g=new THREE.ExtrudeGeometry(shape,{depth:z1-z0,bevelEnabled:false});g.rotateX(-Math.PI/2);g.translate(0,z0,0);
  return new THREE.Mesh(g,new THREE.MeshStandardMaterial({color,transparent:true,opacity:0.22,depthWrite:false,side:THREE.DoubleSide}))}
 function aim(w,face){const d=[w.end[0]-w.start[0],w.end[1]-w.start[1]],l=Math.hypot(...d),n=w.normal_in;const s=['outside','left'].includes(face)?-1:1;
  const c=[(w.start[0]+w.end[0])/2,(w.start[1]+w.end[1])/2,w.z0+w.height/2],dist=Math.max(l,w.height)*1.1+1;
  controls.target.copy(v3(c));camera.position.copy(v3([c[0]+s*n[0]*dist+d[0]/l*0.6,c[1]+s*n[1]*dist+d[1]/l*0.6,c[2]+0.5]));controls.update()}
 // wall layers as translucent prisms in their material colours; the rough openings are cut out: each layer is sliced at
 // every opening u0 / u1 (half-plane clip along the wall), each slice keeps the height intervals outside its openings
 function clip(poly,o,n){const out=[],f=p=>(p[0]-o[0])*n[0]+(p[1]-o[1])*n[1];poly.forEach((p,i)=>{const q=poly[(i+1)%poly.length],a=f(p),b=f(q);
  if(a>=0)out.push(p);if((a<0)!==(b<0)){const t=a/(a-b);out.push([p[0]+(q[0]-p[0])*t,p[1]+(q[1]-p[1])*t])}});return out}
 function pieces(w,fp){const ops=(w.openings||[]).map(o=>o.rough).filter(Boolean);if(!ops.length)return [{fp,z0:w.z0,z1:w.z1}];
  const L=Math.hypot(w.end[0]-w.start[0],w.end[1]-w.start[1]),d=[(w.end[0]-w.start[0])/L,(w.end[1]-w.start[1])/L],at=u=>[w.start[0]+d[0]*u,w.start[1]+d[1]*u];
  const cuts=[...new Set(ops.flatMap(r=>[r.u0,r.u1]))].sort((a,b)=>a-b),b=[-1e9,...cuts,1e9],out=[];
  for(let i=0;i<b.length-1;i++){let s=fp;if(i>0)s=clip(s,at(b[i]),d);if(i<b.length-2&&s.length)s=clip(s,at(b[i+1]),[-d[0],-d[1]]);if(s.length<3)continue;
   const m=i===0?b[1]-1e-6:i===b.length-2?b[i]+1e-6:(b[i]+b[i+1])/2;let z=w.z0;
   ops.filter(r=>r.u0<m&&m<r.u1).map(r=>[w.z0+r.zb,w.z0+r.zt]).sort((x,y)=>x[0]-y[0]).forEach(([lo,hi])=>{if(lo>z+1e-9)out.push({fp:s,z0:z,z1:Math.min(lo,w.z1)});z=Math.max(z,hi)});
   if(z<w.z1-1e-9)out.push({fp:s,z0:z,z1:w.z1})}return out}
 function build(w,face,parts,cur,materials){scene.remove(content);content=new THREE.Group();scene.add(content);
  (w.layers||[]).forEach(l=>{const m=(materials||{})[l.material]||{},c=((m.appearance||{}).color)||'#cccccc';
   pieces(w,l.footprint).forEach(p=>{const pr=prism(p.fp,p.z0,p.z1,c);content.add(pr);content.add(new THREE.LineSegments(new THREE.EdgesGeometry(pr.geometry),new THREE.LineBasicMaterial({color:'#999',transparent:true,opacity:0.5})))})});
  const pick=[];Parts3d.build(THREE,content,pick,{parts});
  pick.forEach(m=>{if(m.userData.p&&m.userData.p.id===cur&&m.userData.kind==='ip_part'){m.material=m.material.clone();m.material.emissive=new THREE.Color('#1C69D4');m.material.emissiveIntensity=0.6}});
  const chosen=parts.find(p=>p.id===cur);if(chosen){const s=['outside','left'].includes(face)?-1:1,d=[w.end[0]-w.start[0],w.end[1]-w.start[1]],l=Math.hypot(...d);
   [[[d[0]/l,d[1]/l,0],'#E53935'],[[0,0,1],'#2E7D32'],[[s*w.normal_in[0],s*w.normal_in[1],0],'#1C69D4']].forEach(([a,c])=>content.add(new THREE.ArrowHelper(v3(a).normalize(),v3(chosen.origin),0.18,c,0.04,0.025)))}
  const key=w.id+'/'+face;if(view!==key){view=key;aim(w,face)}render()}
 window.Install3d={update(w,face,parts,cur,materials){pending=[w,face,parts,cur,materials];if(frame)return;frame=requestAnimationFrame(()=>{frame=0;build(...pending)})}};
 reset.onclick=()=>{if(pending)aim(pending[0],pending[1]);render()};
 size();if(typeof draw==='function')draw()}
