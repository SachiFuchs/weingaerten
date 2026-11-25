
// front view of a window/door/passage; draws into group g; x,y = top-left in px, s = px per metre
function drawFront(g,geo,p,color,x,y,s,mirror){
 const W=(+p.width||1)*s,Hh=(+p.height||1)*s,fw=(+p.frame_width||0.06)*s;const fc=color('frame'),dark='#555';
 const R=(a,b,w,hh,fill,extra)=>{const r=sv('rect',Object.assign({x:a,y:b,width:Math.max(w,0.1),height:Math.max(hh,0.1),fill,stroke:dark,'stroke-width':0.6},extra||{}));g.appendChild(r);return r};
 const L=(a,b,c,d,extra)=>g.appendChild(sv('line',Object.assign({x1:a,y1:b,x2:c,y2:d,stroke:dark,'stroke-width':0.6},extra||{})));
 if(geo==='passage'){R(x,y,W,Hh,'#E6E6E6',{'stroke-dasharray':'4 3'});return}
 if(geo==='door'){R(x,y,W,Hh,fc);R(x+fw,y+fw,W-2*fw,Hh-fw,color('leaf'));
  let hingeLeft=(p.swing||'left')==='left';if(mirror)hingeLeft=!hingeLeft;
  const hx=hingeLeft?x+W-fw-0.12*s:x+fw+0.05*s;R(hx,y+Hh-1.05*s,0.07*s,0.025*s,'#999');
  const ax=hingeLeft?x+fw:x+W-fw,bx=hingeLeft?x+W-fw:x+fw;L(bx,y+fw,ax,y+fw+(Hh-fw)/2,{'stroke-dasharray':'4 3'});L(bx,y+Hh,ax,y+fw+(Hh-fw)/2,{'stroke-dasharray':'4 3'});return}
 if(geo!=='window'){R(x,y,W,Hh,fc);return}
 R(x,y,W,Hh,fc);const ia=x+fw,iw=W-2*fw,iy=y+fw,ih=Hh-2*fw;const sashes=+p.sashes||0;
 const n=Math.max(sashes,1),pw=(iw-(n-1)*fw)/n;
 const ops=[];for(let i=0;i<n;i++){ops.push(sashes<1?'fixed':(p['opening_'+(i+1)]||((n>1&&i===n-1)?'tilt_turn_right':'tilt_turn_left')))}
 for(let i=0;i<n;i++){
  const k=mirror?n-1-i:i,pa=ia+k*(pw+fw),op=ops[i];if(i<n-1){const mk=mirror?n-1-i-1:i;R(ia+mk*(pw+fw)+pw,iy,fw,ih,fc)}
  if(op==='fixed'){R(pa,iy,pw,ih,color('glazing'),{opacity:0.9});continue}
  const sw=0.6*fw;R(pa,iy,pw,ih,fc);R(pa+sw,iy+sw,pw-2*sw,ih-2*sw,color('glazing'),{opacity:0.9});
  const xl=pa+sw,xr=pa+pw-sw,yt=iy+sw,yb=iy+ih-sw,ym=(yt+yb)/2,xm=(xl+xr)/2,dash={'stroke-dasharray':'4 3'};
  if(op==='pivot'){L(xl,ym,xm,yt,dash);L(xr,ym,xm,yt,dash);L(xl,ym,xm,yb,dash);L(xr,ym,xm,yb,dash)}
  if(op.indexOf('turn')>=0){let hl=op.endsWith('left');if(mirror)hl=!hl;const hx=hl?xl:xr,ox=hl?xr:xl;L(ox,yt,hx,ym,dash);L(ox,yb,hx,ym,dash)}
  if(op.indexOf('tilt')>=0){L(xl,yt,xm,yb,dash);L(xr,yt,xm,yb,dash)}}}
function frontSVG(geo,p,color,maxW,maxH){const w=+p.width||1,hh=+p.height||1;const s=Math.min((maxW-4)/w,(maxH-4)/hh);
 const svg=sv('svg',{width:maxW,height:maxH,viewBox:'0 0 '+maxW+' '+maxH});const g=sv('g',{});svg.appendChild(g);
 drawFront(g,geo,p,color,(maxW-w*s)/2,(maxH-hh*s)/2,s,false);return svg}
