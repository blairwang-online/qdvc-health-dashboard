// ---- Histogram ---------------------------------------------------------- //
(function(){
  const b=A.buckets, keys=Object.keys(b), vals=keys.map(k=>b[k]);
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB, max=Math.max(1,...vals);
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`});
  const bw=iw/keys.length*0.68, gap=iw/keys.length;
  keys.forEach((k,i)=>{
    const h=vals[i]/max*ih, cx=mL+i*gap+gap/2;
    const good=(k==='7–8h'||k==='8–9h');
    svg.appendChild(el('rect',{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
      fill:good?css('--good'):css('--dawn2'),opacity:good?0.9:0.55}));
    const val=el('text',{x:cx,y:mT+ih-h-6,'text-anchor':'middle'});
    val.setAttribute('class','axis'); val.textContent=vals[i]||''; svg.appendChild(val);
    const lab=el('text',{x:cx,y:H-14,'text-anchor':'middle'});
    lab.setAttribute('class','axis'); lab.textContent=k; svg.appendChild(lab);
  });
  svg.appendChild(el('line',{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,
    stroke:css('--line')}));
  document.getElementById('hist').appendChild(svg);
})();

