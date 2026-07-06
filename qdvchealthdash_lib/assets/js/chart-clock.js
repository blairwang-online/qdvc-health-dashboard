// ---- Clock-time chart (when sleep happened) — horizontal bars ----------- //
function renderClock(v){
  const s=v.items, host=document.getElementById('clock');
  host.innerHTML='';
  if(!s.length){ host.innerHTML='<p class="axis">No data.</p>'; return; }
  const rowH=Math.max(39, Math.min(60, 450/s.length));
  const mL=104, mR=18, mT=10, mB=30;
  const H=mT+mB+rowH*s.length, W=480, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`});
  // x domain from data (minutes-since-noon), padded to whole 2-hour marks.
  let lo=Math.min(...s.map(d=>d.bed_min)), hi=Math.max(...s.map(d=>d.wake_min));
  lo=Math.floor((lo-30)/120)*120; hi=Math.ceil((hi+30)/120)*120;
  const x=m=> mL + ((m-lo)/(hi-lo))*iw;   // earlier -> left, later -> right
  // Gradient anchored to the x-axis in user space, so a given clock time is the
  // same colour on every bar. Colours come from the shared time-of-day palette.
  const defs=el('defs',{});
  const lg=el('linearGradient',{id:'barGrad',gradientUnits:'userSpaceOnUse',
    x1:x(lo),y1:'0',x2:x(hi),y2:'0'});
  const STEP=15;
  for(let m=lo; m<=hi; m+=STEP){
    const off=(x(m)-x(lo))/(x(hi)-x(lo));   // 0 at left (lo), 1 at right (hi)
    lg.appendChild(el('stop',{offset:off.toFixed(4),'stop-color':todHexFromNoon(m)}));
  }
  defs.appendChild(lg); svg.appendChild(defs);
  // vertical gridlines + time labels every 2h
  for(let m=lo;m<=hi;m+=120){
    svg.appendChild(el('line',{x1:x(m),y1:mT,x2:x(m),y2:mT+ih,
      stroke:css('--line'),'stroke-width':1}));
    const t=el('text',{x:x(m),y:H-12,'text-anchor':'middle'});
    t.setAttribute('class','axis'); t.textContent=clockFromNoon(m); svg.appendChild(t);
  }
  const B=bandScaleY(s.length, mT, ih);
  const cy=i=>B.center(i);
  s.forEach((d,i)=>{
    const xL=x(d.bed_min), xR=x(d.wake_min);
    svg.appendChild(el('rect',{x:xL,y:cy(i)-B.barHeight/2,
      width:Math.max(1,xR-xL),height:B.barHeight,rx:3,
      fill:'url(#barGrad)',opacity:0.92}));
  });
  // row labels (left)
  s.forEach((d,i)=>{ rowLabel(svg, mL-10, cy(i), d.dow, d.dm); });
  host.appendChild(svg);
}

