
// Katalog master-detail layout: list/detail splitter, detail/photo splitter, photo strip.
const KatLayout=(()=>{
 const $=id=>document.getElementById(id);
 function drag(bar,onMove,onEnd){bar.addEventListener('pointerdown',ev=>{ev.preventDefault();bar.setPointerCapture(ev.pointerId);bar.classList.add('on');
  const mv=e=>onMove(e),up=()=>{bar.classList.remove('on');bar.removeEventListener('pointermove',mv);bar.removeEventListener('pointerup',up);onEnd()};
  bar.addEventListener('pointermove',mv);bar.addEventListener('pointerup',up)})}
 function init(page){const grid=$('katgrid'),side=$('katside'),main=$('katmain'),SK='weingaerten.katalog.split.'+page,PK='weingaerten.katalog.photos.'+page;
  const clampW=w=>Math.max(200,Math.min(w,grid.clientWidth*0.6));
  const setW=w=>{side.style.width=clampW(w)+'px'};setW(+localStorage.getItem(SK)||340);
  drag($('katsplit'),e=>setW(e.clientX-grid.getBoundingClientRect().left),()=>localStorage.setItem(SK,String(parseInt(side.style.width))));
  const strip=$('katphotos');const clampH=v=>Math.max(80,Math.min(v,main.clientHeight*0.7));
  const setH=v=>{strip.style.height=clampH(v)+'px'};setH(+localStorage.getItem(PK)||180);
  drag($('katvsplit'),e=>setH(main.getBoundingClientRect().bottom-e.clientY),()=>localStorage.setItem(PK,String(parseInt(strip.style.height))));
  window.addEventListener('resize',()=>{setW(parseInt(side.style.width));setH(parseInt(strip.style.height))})}
 function photos(e){const strip=$('katphotos'),bar=$('katvsplit');strip.textContent='';
  const list=(e&&Array.isArray(e.photos))?e.photos.filter(x=>typeof x==='string'&&x):[];
  strip.style.display=bar.style.display=list.length?'':'none';
  list.forEach(f=>{const src='/catalog-photo/'+encodeURIComponent(e.id)+'/'+encodeURIComponent(f);
   const img=h('img',{src,alt:f,title:f});img.onclick=()=>window.open(src,'_blank','noopener');strip.appendChild(img)})}
 return {init,photos,drag}})();
