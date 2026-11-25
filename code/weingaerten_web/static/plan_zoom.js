
// /grundriss layout: toolbar (storey, cut height), resizable plan box, splitter, zoom/pan of the plan SVGs
const PlanZoom=(()=>{const ZF=1.15,ZMIN=0.2,ZMAX=20,LS_SPLIT='weingaerten.grundriss.split';
 const box=document.getElementById('planbox'),split=document.getElementById('plansplit'),panel=document.getElementById('planpanel');
 const states=new Map();let space=false,pan=null;
 // the viewBox always shows the whole drawing; zoom = CSS size (fit size x z), the box scrolls on overflow
 function apply(svg){const s=states.get(svg);svg.setAttribute('viewBox',[0,0,s.bw,s.bh].map(v=>+v.toFixed(2)).join(' '));
  const f=Math.min(box.clientWidth/s.bw,box.clientHeight/s.bh)||1;
  svg.style.width=Math.floor(s.bw*f*s.z)+'px';svg.style.height=Math.floor(s.bh*f*s.z)+'px'}
 // base size (whole drawing); the zoom state is kept when the base is set again
 function base(svg,bw,bh){const s=states.get(svg);if(s){s.bw=bw;s.bh=bh}else states.set(svg,{bw,bh,z:1});apply(svg)}
 function active(){return [...box.querySelectorAll('svg')].find(v=>v.getBoundingClientRect().width>0&&states.has(v))}
 // zoom around the client point (cx, cy): the content point under it stays fixed via the scroll position
 function zoomAt(svg,f,cx,cy){const s=states.get(svg);const nz=Math.min(ZMAX,Math.max(ZMIN,s.z*f));
  const r=box.getBoundingClientRect(),ox=cx-r.left-box.clientLeft,oy=cy-r.top-box.clientTop;
  const px=box.scrollLeft+ox,py=box.scrollTop+oy,k=nz/s.z;s.z=nz;apply(svg);
  box.scrollLeft=px*k-ox;box.scrollTop=py*k-oy}
 function zoomCenter(f){const svg=active();if(!svg)return;const r=box.getBoundingClientRect();zoomAt(svg,f,r.left+box.clientWidth/2,r.top+box.clientHeight/2)}
 function fit(){const svg=active();if(!svg)return;states.get(svg).z=1;apply(svg);box.scrollLeft=0;box.scrollTop=0}
 box.addEventListener('wheel',ev=>{const svg=active();if(!svg)return;ev.preventDefault();zoomAt(svg,ev.deltaY<0?ZF:1/ZF,ev.clientX,ev.clientY)},{passive:false});
 // pan by scrolling: right or middle mouse button, or Space + left button
 box.addEventListener('pointerdown',ev=>{if(!(ev.button===2||ev.button===1||(space&&ev.button===0)))return;
  ev.preventDefault();ev.stopPropagation();pan={x:ev.clientX,y:ev.clientY,sl:box.scrollLeft,st:box.scrollTop};box.style.cursor='grabbing';
  try{box.setPointerCapture(ev.pointerId)}catch(e){}},true);
 box.addEventListener('pointermove',ev=>{if(!pan)return;ev.stopPropagation();
  box.scrollLeft=pan.sl-(ev.clientX-pan.x);box.scrollTop=pan.st-(ev.clientY-pan.y)},true);
 box.addEventListener('pointerup',ev=>{if(pan){pan=null;box.style.cursor=space?'grab':'';ev.stopPropagation()}},true);
 box.addEventListener('contextmenu',ev=>ev.preventDefault());
 const typing=()=>['INPUT','SELECT','TEXTAREA'].includes(document.activeElement.tagName);
 document.addEventListener('keydown',ev=>{if(ev.key===' '&&!typing()){space=true;box.style.cursor='grab';ev.preventDefault()}});
 document.addEventListener('keyup',ev=>{if(ev.key===' '){space=false;box.style.cursor=''}});
 // toolbar
 const sel=document.getElementById('storeysel'),cut=document.getElementById('plancut');
 const go=()=>{location.href='/grundriss?storey='+encodeURIComponent(sel.value)+'&cut='+encodeURIComponent(cut.value)+location.hash};
 if(sel)sel.onchange=go;if(cut)cut.onchange=go;
 document.getElementById('zoomin').onclick=()=>zoomCenter(ZF);document.getElementById('zoomout').onclick=()=>zoomCenter(1/ZF);
 document.getElementById('zoomfit').onclick=fit;
 // plan box: fills the free width next to the panel and the window height below its top (panel same height)
 const fitH=()=>{const top=box.getBoundingClientRect().top+scrollY;const hh=Math.max(200,innerHeight-top-16)+'px';box.style.height=hh;panel.style.maxHeight=hh};
 fitH();addEventListener('resize',fitH);addEventListener('load',fitH);
 new ResizeObserver(()=>states.forEach((s,svg)=>apply(svg))).observe(box);
 const pw=+localStorage.getItem(LS_SPLIT);if(pw)panel.style.width=pw+'px';
 split.addEventListener('pointerdown',ev=>{ev.preventDefault();split.setPointerCapture(ev.pointerId);
  const lay=split.parentElement.getBoundingClientRect();const mv=e=>{const w=Math.min(lay.width*0.6,Math.max(260,lay.right-e.clientX));panel.style.width=w+'px'};
  const up=()=>{split.removeEventListener('pointermove',mv);split.removeEventListener('pointerup',up);localStorage.setItem(LS_SPLIT,parseInt(panel.style.width))};
  split.addEventListener('pointermove',mv);split.addEventListener('pointerup',up)});
 function showPanel(){split.style.display='';panel.style.display=''}
 const view=document.querySelector('#planview svg');if(view){const vb=view.viewBox.baseVal;base(view,vb.width,vb.height)}
 return {base,fit,showPanel}})();
