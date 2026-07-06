// ---- Bedtime punctuality (multi-series line chart) ---------------------- //
// Punctuality target colours are derived from the time-of-day palette so each
// line's hue matches the clock time it represents. Because every target clusters
// near one bedtime, the raw palette samples would be near-identical blues, so we
// keep each sample's HUE but override saturation/lightness. Both are spread
// across the ladder by the line's position: the earliest/hardest target is
// darkest and most saturated, the latest/easiest is lightest and softest, so
// adjacent same-hue lines separate strongly. The ranges are bounded so every
// line still reads on both the light and dark themes. See MAINTENANCE.md §5.
const PUNCT_SAT_LO = 0.95;    // saturation of the latest/easiest target (softer)
const PUNCT_SAT_HI = 1.0;     // saturation of the earliest/hardest target (intense)
const PUNCT_SAT_FLOOR = 0.45; // never desaturate a sample below this
const PUNCT_LIGHT_LO = 0.30;  // lightness of the earliest/hardest target (darkest)
const PUNCT_LIGHT_HI = 0.74;  // lightness of the latest/easiest target (lightest)
function _rgbToHsl(r,g,b){
  r/=255; g/=255; b/=255;
  const mx=Math.max(r,g,b), mn=Math.min(r,g,b), d=mx-mn;
  let h=0; const l=(mx+mn)/2;
  const s=d===0?0:d/(1-Math.abs(2*l-1));
  if(d!==0){
    if(mx===r) h=((g-b)/d)%6;
    else if(mx===g) h=(b-r)/d+2;
    else h=(r-g)/d+4;
    h*=60; if(h<0) h+=360;
  }
  return [h,s,l];
}
function _hslToHex(h,s,l){
  const c=(1-Math.abs(2*l-1))*s, x=c*(1-Math.abs((h/60)%2-1)), m=l-c/2;
  let r=0,g=0,b=0;
  if(h<60){r=c;g=x;} else if(h<120){r=x;g=c;} else if(h<180){g=c;b=x;}
  else if(h<240){g=x;b=c;} else if(h<300){r=x;b=c;} else {r=c;b=x;}
  const to=v=>Math.round((v+m)*255).toString(16).padStart(2,'0');
  return '#'+to(r)+to(g)+to(b);
}
// Take a time-of-day colour (as minutes-since-noon), keep its hue, and pick both
// saturation and lightness by the line's position in the ladder: idx of total
// (0-based) maps linearly across the PUNCT_SAT_* / PUNCT_LIGHT_* ranges
// (position 0 = darkest+most saturated). A single line (total<=1) sits at the
// midpoint of both ranges.
function punctColor(minsSinceNoon, idx, total){
  const [r,g,b]=todRgb(((Math.round(minsSinceNoon)+720)%1440+1440)%1440);
  const [h,s]=_rgbToHsl(r,g,b);
  const f = total>1 ? idx/(total-1) : 0.5;
  const sPos = PUNCT_SAT_HI + (PUNCT_SAT_LO - PUNCT_SAT_HI) * f;   // hi at idx 0
  const s2 = Math.min(1, Math.max(PUNCT_SAT_FLOOR, s * sPos));
  const l = PUNCT_LIGHT_LO + (PUNCT_LIGHT_HI - PUNCT_LIGHT_LO) * f;
  return _hslToHex(h, s2, l);
}
// Smooth an SVG polyline through the given points with a Catmull-Rom spline
// (converted to cubic Béziers), for gently curved series lines. Control-point y
// values are clamped to [yMin,yMax] (the plot band) so the curve never bows past
// the 0%/100% edges between data points — the anchors are already in range.
function smoothPath(pts, yMin, yMax){
  if(pts.length<2) return pts.length?('M'+pts[0][0]+' '+pts[0][1]):'';
  const clampY = yMin==null ? (v=>v)
    : (v => Math.max(Math.min(yMin,yMax), Math.min(Math.max(yMin,yMax), v)));
  let d='M'+pts[0][0]+' '+pts[0][1];
  for(let i=0;i<pts.length-1;i++){
    const p0=pts[i>0?i-1:i], p1=pts[i], p2=pts[i+1], p3=pts[i+2<pts.length?i+2:i+1];
    const c1x=p1[0]+(p2[0]-p0[0])/6, c1y=clampY(p1[1]+(p2[1]-p0[1])/6);
    const c2x=p2[0]-(p3[0]-p1[0])/6, c2y=clampY(p2[1]-(p3[1]-p1[1])/6);
    d+='C'+c1x+' '+c1y+' '+c2x+' '+c2y+' '+p2[0]+' '+p2[1];
  }
  return d;
}
function renderPunctuality(pview){
  const P = A.punctuality;
  const isThr = pview.indexOf('_thr') !== -1;
  const isMonthly = pview.indexOf('monthly') === 0;
  const rows = (isThr
      ? (isMonthly ? P.monthly_thr : P.weekly_thr)
      : (isMonthly ? P.monthly : P.weekly)) || [];
  const marks = isThr ? P.thresholds : P.benchmarks;
  const host = document.getElementById('punct');
  const legend = document.getElementById('punctLegend');
  host.innerHTML=''; legend.innerHTML='';
  document.getElementById('punctTitle').textContent =
    (isMonthly ? 'Monthly' : 'Weekly') + ' success rate — '
    + (isThr ? 'archetype thresholds' : 'benchmarks');
  if(rows.length<1){ host.innerHTML='<p class="axis">No data.</p>'; return; }

  const W=980, H=340, mL=44, mR=140, mT=16, mB=52, iw=W-mL-mR, ih=H-mT-mB;
  const svg=el('svg',{viewBox:`0 0 ${W} ${H}`});
  const n=rows.length;
  const x = i => mL + (n===1 ? iw/2 : (i/(n-1))*iw);
  const y = pct => mT + ih - (pct/100)*ih;

  // horizontal gridlines + y labels (0-100%)
  for(let p=0;p<=100;p+=25){
    svg.appendChild(el('line',{x1:mL,y1:y(p),x2:mL+iw,y2:y(p),
      stroke:css('--line'),'stroke-width':1}));
    const t=el('text',{x:mL-8,y:y(p)+3,'text-anchor':'end'});
    t.setAttribute('class','axis'); t.textContent=p+'%'; svg.appendChild(t);
  }
  // x labels (skip some if crowded)
  const step=Math.ceil(n/9);
  rows.forEach((r,i)=>{ if(i%step && i!==n-1) return;
    const t=el('text',{x:x(i),y:H-30,'text-anchor':'middle'});
    t.setAttribute('class','axis'); t.textContent=r.label; svg.appendChild(t);
  });

  marks.forEach((bm,mi)=>{
    const col = punctColor(bm.minutes, mi, marks.length);
    const pts = rows.map((r,i)=>[x(i), y(r.rates[bm.code])]);
    svg.appendChild(el('path',{d:smoothPath(pts, y(100), y(0)),fill:'none',stroke:col,
      'stroke-width':2.5,'stroke-linejoin':'round','stroke-linecap':'round',opacity:0.9}));
    pts.forEach(pt=>{ svg.appendChild(el('circle',{cx:pt[0],cy:pt[1],
      r:2.6,fill:col,opacity:0.9})); });
    // legend row
    const item=document.createElement('div'); item.className='punct-legend-item';
    item.innerHTML='<span class="punct-swatch" style="background:'+col+'"></span>'+bm.label;
    legend.appendChild(item);
  });
  host.appendChild(svg);
}
document.querySelectorAll('#punctTabs .ptab').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('#punctTabs .ptab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    renderPunctuality(btn.dataset.pview);
  });
});
renderPunctuality('weekly');

