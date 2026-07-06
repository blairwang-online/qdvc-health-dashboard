// ---- Duration chart (hours) — horizontal bars --------------------------- //
function renderDuration(v){
  const s=v.items, host=document.getElementById('trend');
  host.innerHTML='';
  if(!s.length){ host.innerHTML='<p class="axis">No data.</p>'; return; }
  const rowH=Math.max(39, Math.min(60, 450/s.length));
  const mL=104, mR=18, mT=10, mB=30;
  const H=mT+mB+rowH*s.length, W=480, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`});
  const maxD=Math.max(10, Math.ceil(Math.max(...s.map(d=>d.duration))));
  const B=bandScaleY(s.length, mT, ih);
  const cy=i=>B.center(i);
  const x=val=> mL + (val/maxD)*iw;   // hours -> horizontal position
  // target band 7-9h (vertical strip)
  svg.appendChild(el('rect',{x:x(7),y:mT,width:x(9)-x(7),height:ih,
    fill:css('--good'),opacity:0.12}));
  // vertical gridlines every 2h
  for(let h=0;h<=maxD;h+=2){
    svg.appendChild(el('line',{x1:x(h),y1:mT,x2:x(h),y2:mT+ih,
      stroke:css('--line'),'stroke-width':1}));
    const t=el('text',{x:x(h),y:H-12,'text-anchor':'middle'});
    t.setAttribute('class','axis'); t.textContent=h+'h'; svg.appendChild(t);
  }
  // bars (uniform styling across all tabs)
  s.forEach((d,i)=>{
    svg.appendChild(el('rect',{x:mL,y:cy(i)-B.barHeight/2,
      width:Math.max(1,x(d.duration)-mL),height:B.barHeight,
      fill:css('--dawn2'),opacity:0.85,rx:3}));
  });
  // last7 rolling trend line connecting bar ends down the rows
  if(v.hasRolling){
    let path='';
    s.forEach((d,i)=>{ path+=(i?'L':'M')+x(d.rolling)+' '+cy(i); });
    svg.appendChild(el('path',{d:path,fill:'none',stroke:css('--dawn1'),
      'stroke-width':2,'stroke-linejoin':'round',opacity:.9}));
    s.forEach((d,i)=>{ svg.appendChild(el('circle',{cx:x(d.rolling),cy:cy(i),
      r:2.5,fill:css('--dawn1'),opacity:.9})); });
  }
  // row labels (left)
  s.forEach((d,i)=>{ rowLabel(svg, mL-10, cy(i), d.dow, d.dm); });
  host.appendChild(svg);
}

