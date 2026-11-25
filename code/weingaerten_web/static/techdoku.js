// Document tree pages (Benutzerhandbuch, Tech.Doku): tree/page splitter and the remembered open tree nodes.
(()=>{
 const $=id=>document.getElementById(id),grid=$('tdgrid');
 if(!grid)return;
 const tree=$('tdtree'),bar=$('tdsplit'),ST='weingaerten.'+grid.dataset.store,SK=ST+'.split',OK=ST+'.open';
 const clampW=w=>Math.max(180,Math.min(w,grid.clientWidth*0.5));
 const setW=w=>{tree.style.width=clampW(w)+'px'};setW(+localStorage.getItem(SK)||300);
 bar.addEventListener('pointerdown',ev=>{ev.preventDefault();bar.setPointerCapture(ev.pointerId);bar.classList.add('on');
  const mv=e=>setW(e.clientX-grid.getBoundingClientRect().left),
   up=()=>{bar.classList.remove('on');bar.removeEventListener('pointermove',mv);bar.removeEventListener('pointerup',up);localStorage.setItem(SK,String(parseInt(tree.style.width)))};
  bar.addEventListener('pointermove',mv);bar.addEventListener('pointerup',up)});
 let open=[];try{open=JSON.parse(localStorage.getItem(OK)||'[]')}catch(e){open=[]}if(!Array.isArray(open))open=[];
 tree.querySelectorAll('details').forEach(d=>{if(open.includes(d.dataset.node))d.open=true;
  d.addEventListener('toggle',()=>{const id=d.dataset.node,set=new Set(open);d.open?set.add(id):set.delete(id);open=[...set];localStorage.setItem(OK,JSON.stringify(open))})});
 // a click on a summary link navigates instead of toggling the node
 tree.querySelectorAll('summary a').forEach(a=>a.addEventListener('click',e=>e.stopPropagation()));
 const on=tree.querySelector('a.on');if(on)on.scrollIntoView({block:'nearest'});
 // source popup: a link with data-src opens its modal dialog; only the close button and Esc end it
 document.querySelectorAll('[data-src]').forEach(a=>a.addEventListener('click',e=>{e.preventDefault();const d=$(a.dataset.src);if(d&&d.showModal)d.showModal()}));
 // "Alle aufklappen / zuklappen" act on the details of their dialog, else of the page
 document.querySelectorAll('[data-expand]').forEach(b=>b.addEventListener('click',()=>{
  const scope=b.closest('dialog')||$('tdmain'),open=b.dataset.expand==='1';
  scope.querySelectorAll(b.closest('dialog')?'.tdsrcbody details':'.tdlist details').forEach(d=>{d.open=open})}));
 // group diagram: hovering a module box highlights its arrows
 document.querySelectorAll('svg.tdgroup [data-mod]').forEach(g=>{const svg=g.closest('svg'),mod=g.dataset.mod;
  const mark=on=>svg.querySelectorAll('line').forEach(l=>{if(l.dataset.from===mod||l.dataset.to===mod)l.classList.toggle('hl',on)});
  g.addEventListener('mouseenter',()=>mark(true));g.addEventListener('mouseleave',()=>mark(false))});
 window.addEventListener('resize',()=>setW(parseInt(tree.style.width)));
})();
