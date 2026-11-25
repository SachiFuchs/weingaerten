
// /haus3d: detail panel (iframe, splitter drag, <|> collapse) and the links in the hover tooltip
const Detail3d=(function(){
 const main=document.querySelector('main'),split=document.getElementById('split3d'),panel=document.getElementById('detail3d');
 const frame=document.getElementById('detailframe'),toggle=document.getElementById('detailtoggle'),box=document.getElementById('details3d');
 // #tip comes after main in the page frame, so it is looked up on first use
 let tipEl=null;const T=()=>{if(!tipEl){tipEl=document.getElementById('tip');tipEl.addEventListener('pointerleave',()=>idle())}return tipEl};let frozen=false,timer=0;
 // nothing is stored: hidden at start, 40 % of main wide
 let width=Math.round(main.clientWidth*0.4),collapsed=false;
 const clamp=w=>Math.max(280,Math.min(w,main.clientWidth*0.7));
 function apply(){const on=box.checked;split.style.display=on?'block':'none';panel.style.display=on?'block':'none';
  panel.style.width=(collapsed?0:clamp(width))+'px'}
 box.onchange=apply;
 toggle.onclick=e=>{e.stopPropagation();collapsed=!collapsed;apply()};
 split.addEventListener('pointerdown',e=>{if(e.target===toggle)return;split.setPointerCapture(e.pointerId);frame.style.pointerEvents='none';
  const move=ev=>{collapsed=false;width=clamp(main.getBoundingClientRect().right-ev.clientX);apply()};
  const up=()=>{split.removeEventListener('pointermove',move);split.removeEventListener('pointerup',up);frame.style.pointerEvents=''};
  split.addEventListener('pointermove',move);split.addEventListener('pointerup',up)});
 function open(url){frame.removeAttribute('srcdoc');frame.src=url;box.checked=true;collapsed=false;apply();idle()}
 function unfreeze(){clearTimeout(timer);frozen=false;T().classList.remove('live')}
 function idle(){unfreeze();hideTip()}
 // after showTip: append the links [[label,url],...]; the tooltip freezes when the pointer rests 300 ms
 function live(links){unfreeze();const tip=T();if(links.length){const d=document.createElement('div');d.className='tiplinks';
   links.forEach(([label,url])=>{const a=document.createElement('a');a.textContent=label;a.href=url;a.onclick=e=>{e.preventDefault();open(url)};d.appendChild(a)});tip.appendChild(d)}
  timer=setTimeout(()=>{if(tip.style.display==='block'){frozen=true;tip.classList.add('live')}},300)}
 // true while frozen and the pointer is near the box (the scene must not update the tooltip then)
 function held(e){if(!frozen)return false;const r=T().getBoundingClientRect();
  const dx=Math.max(r.left-e.clientX,0,e.clientX-r.right),dy=Math.max(r.top-e.clientY,0,e.clientY-r.bottom);
  if(Math.hypot(dx,dy)<=40)return true;unfreeze();return false}
 const inTip=n=>!!(n&&T().contains(n));
 addEventListener('keydown',e=>{if(e.key==='Escape')idle()});
 apply();
 return {open,live,held,idle,inTip}})();
