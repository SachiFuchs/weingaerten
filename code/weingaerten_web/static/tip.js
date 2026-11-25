// Floating tooltip of all pages: showTip(event, lines, colour) and hideTip().
function showTip(e,lines,color){const tip=document.getElementById('tip');tip.textContent='';lines.forEach((l,i)=>{const el=document.createElement(i==0?'b':'div');el.textContent=l;tip.appendChild(el)});
 if(color){const s=document.createElement('span');s.className='sw';s.style.background=color;tip.appendChild(s)}
 tip.style.display='block';tip.style.left=(e.clientX+14)+'px';tip.style.top=(e.clientY+14)+'px'}
function hideTip(){const tip=document.getElementById('tip');if(tip)tip.style.display='none'}
