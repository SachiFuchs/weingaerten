
// /waende four-pane layout: nav | wall list | wall view over parts table | installation tree over 3D preview, five splitters.
const WaendeLayout=(()=>{
 const $=id=>document.getElementById(id),PRE='weingaerten.waende.';
 const clamp=(v,lo,hi)=>Math.max(lo,Math.min(v,Math.max(lo,hi)));
 // one pane size: el gets width/height from localStorage key (default d), limits from lim() = [min, max]
 function pane(bar,el,key,prop,d,lim,value){
  const set=v=>{const [lo,hi]=lim();el.style[prop]=Math.round(clamp(v,lo,hi))+'px'};
  set(+localStorage.getItem(PRE+key)||d);
  KatLayout.drag(bar,e=>set(value(e)),()=>localStorage.setItem(PRE+key,String(parseInt(el.style[prop]))));
  return ()=>set(parseInt(el.style[prop]))}
 function init(){const grid=$('katgrid'),side=$('katside'),main=$('katmain'),right=$('wright'),bottom=$('wbottom'),prev=$('prev3dbox');
  const nav=document.querySelector('nav'),panes=[];
  if(nav){const bar=document.createElement('div');bar.id='navsplit';bar.title='Breite ändern';nav.after(bar);
   panes.push(pane(bar,nav,'nav','width',200,()=>[120,320],e=>e.clientX-nav.getBoundingClientRect().left))}
  panes.push(pane($('katsplit'),side,'side','width',300,()=>[200,grid.clientWidth*0.4],e=>e.clientX-grid.getBoundingClientRect().left));
  panes.push(pane($('wrsplit'),right,'right','width',340,()=>[220,grid.clientWidth*0.45],e=>grid.getBoundingClientRect().right-e.clientX));
  panes.push(pane($('wcsplit'),bottom,'bottom','height',200,()=>[80,main.clientHeight*0.7],e=>main.getBoundingClientRect().bottom-e.clientY));
  panes.push(pane($('prevsplit'),prev,'preview','height',300,()=>[80,right.clientHeight*0.7],e=>right.getBoundingClientRect().bottom-e.clientY));
  window.addEventListener('resize',()=>panes.forEach(f=>f()))}
 return {init}})();
