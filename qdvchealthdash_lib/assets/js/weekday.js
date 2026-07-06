// ---- Weekday chart ------------------------------------------------------ //
(function(){
  const names=['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], w=A.weekday_avg;
  const W=460,H=260,mL=34,mR=12,mT=12,mB=40;
  const iw=W-mL-mR, ih=H-mT-mB;
  const max=Math.max(10,...w.filter(v=>v!=null));
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`});
  const bw=iw/7*0.6, gap=iw/7;
  // target line at 8h
  const y8=mT+ih-(8/max)*ih;
  svg.appendChild(el('line',{x1:mL,y1:y8,x2:W-mR,y2:y8,
    stroke:css('--good'),'stroke-dasharray':'4 4','stroke-width':1.5,opacity:.6}));
  names.forEach((nm,i)=>{
    const cx=mL+i*gap+gap/2, v=w[i];
    if(v!=null){
      const h=v/max*ih;
      svg.appendChild(el('rect',{x:cx-bw/2,y:mT+ih-h,width:bw,height:h,rx:3,
        fill:i>=5?css('--dawn3'):css('--dawn1'),opacity:.8}));
      const val=el('text',{x:cx,y:mT+ih-h-6,'text-anchor':'middle'});
      val.setAttribute('class','axis'); val.textContent=v.toFixed(1); svg.appendChild(val);
    }
    const lab=el('text',{x:cx,y:H-14,'text-anchor':'middle'});
    lab.setAttribute('class','axis'); lab.textContent=nm; svg.appendChild(lab);
  });
  svg.appendChild(el('line',{x1:mL,y1:mT+ih,x2:W-mR,y2:mT+ih,stroke:css('--line')}));
  document.getElementById('weekday').appendChild(svg);
})();

