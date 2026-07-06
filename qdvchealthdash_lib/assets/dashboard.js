const A = __DATA_JSON__;
const PERSONA_CARDS = __PERSONA_CARDS_JSON__;

// Animate the score arc.
(function(){
  const r=50, circ=2*Math.PI*r, arc=document.getElementById('scoreArc');
  const frac=Math.max(0,Math.min(1,A.score/100));
  arc.style.setProperty('--circ', circ);
  arc.setAttribute('stroke-dasharray', circ);
  arc.setAttribute('stroke-dashoffset', circ*(1-frac));
})();

const SVGNS='http://www.w3.org/2000/svg';
function el(tag,attrs){const e=document.createElementNS(SVGNS,tag);
  for(const k in attrs)e.setAttribute(k,attrs[k]);return e;}
function css(v){return getComputedStyle(document.documentElement).getPropertyValue(v).trim();}

// Band scale: each item gets an equal-width slot; bars are centred in their
// slot and never exceed it. Endpoints stay fully inside the plot area (unlike
// point spacing, which pins the first/last item to the margins and lets wide
// bars bleed out when there are few items).
function bandScale(n, mL, iw){
  const slot = iw / Math.max(1, n);
  return {
    slot,
    center: i => mL + slot * (i + 0.5),
    barWidth: Math.max(2, Math.min(slot * 0.62, 64)),  // capped so 1–2 items look sane
  };
}

// Two-line x-axis tick: weekday/"Week of" on top, date beneath.
function twoLineLabel(svg, cx, yBase, top, bottom){
  const t1 = el('text', {x:cx, y:yBase, 'text-anchor':'middle'});
  t1.setAttribute('class','axis axis-top'); t1.textContent = top;
  svg.appendChild(t1);
  const t2 = el('text', {x:cx, y:yBase + 13, 'text-anchor':'middle'});
  t2.setAttribute('class','axis axis-date'); t2.textContent = bottom;
  svg.appendChild(t2);
}

// Vertical band scale for horizontal bar charts: each item gets an equal-height
// row slot; bars are centred within their slot.
function bandScaleY(n, mT, ih){
  const slot = ih / Math.max(1, n);
  return {
    slot,
    center: i => mT + slot * (i + 0.5),
    barHeight: Math.max(6, Math.min(slot * 0.62, 26)),
  };
}

// Two-line row label (left of a horizontal chart), right-aligned to the axis.
function rowLabel(svg, xRight, yMid, top, bottom){
  const t1 = el('text', {x:xRight, y:yMid-2, 'text-anchor':'end'});
  t1.setAttribute('class','axis axis-top'); t1.textContent = top;
  svg.appendChild(t1);
  const t2 = el('text', {x:xRight, y:yMid+11, 'text-anchor':'end'});
  t2.setAttribute('class','axis axis-date'); t2.textContent = bottom;
  svg.appendChild(t2);
}

// ---- Clock helpers (minutes-since-noon -> "HH:MM") ---------------------- //
function clockFromNoon(mins){
  let total=Math.round(mins)+720; total=((total%1440)+1440)%1440;
  return String(Math.floor(total/60)).padStart(2,'0')+':'+String(total%60).padStart(2,'0');
}

// Time-of-day colour: mirrors the Python _tod_rgb. Anchors come from A.tod_anchors
// (minute-of-day on a 20:00-based axis -> [r,g,b]). Input is minute-of-day 0–1440.
function todRgb(minuteOfDay){
  const A0=A.tod_anchors;
  let m=((minuteOfDay%1440)+1440)%1440;
  if(m < 20*60) m+=1440;
  for(let i=0;i<A0.length-1;i++){
    const [m0,c0]=A0[i], [m1,c1]=A0[i+1];
    if(m>=m0 && m<=m1){
      const t=(m-m0)/(m1-m0);
      return [0,1,2].map(k=>Math.round(c0[k]+(c1[k]-c0[k])*t));
    }
  }
  return A0[A0.length-1][1];
}
function todHex(minuteOfDay){
  const c=todRgb(minuteOfDay);
  return '#'+c.map(x=>x.toString(16).padStart(2,'0')).join('');
}
// Axis value is minutes-since-noon; convert to minute-of-day for the palette.
function todHexFromNoon(minsSinceNoon){
  return todHex(((Math.round(minsSinceNoon)+720)%1440+1440)%1440);
}

// Normalise the active tab into a common item shape.
// Items are returned newest-first (most recent at the top of each chart, to
// match the "past 7 days" archetype table).
function buildView(view){
  if(view==='last7'){
    const s=A.series.slice(-7);
    return {
      hasRolling:true,
      items:s.map(d=>({
        dow:d.dow, dm:d.dm, duration:d.duration, rolling:d.rolling,
        bed_min:d.bed_min, wake_min:d.wake_min, bed:d.bed, wake:d.wake
      })).reverse()
    };
  }
  const stat = (view==='means' || view==='mmeans') ? 'mean' : 'med';
  const src  = (view==='means' || view==='medians') ? A.weekly : A.monthly;
  const agg = { b:stat+'_bed_min', w:stat+'_wake_min', d:stat+'_dur',
                bc:stat+'_bed', wc:stat+'_wake' };
  return {
    hasRolling:false,
    items:src.map(w=>({
      dow:w.dow, dm:w.dm, duration:w[agg.d], rolling:null,
      bed_min:w[agg.b], wake_min:w[agg.w], bed:w[agg.bc], wake:w[agg.wc],
      nights:w.nights
    })).reverse()
  };
}

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

// ---- Tab wiring --------------------------------------------------------- //
function showView(view){
  const v=buildView(view);
  const durWord = view==='last7' ? 'Hours slept & 7-night trend'
    : (view==='means'  ? 'Mean hours slept per week'
    : (view==='medians'? 'Median hours slept per week'
    : (view==='mmeans' ? 'Mean hours slept per month'
    :                    'Median hours slept per month')));
  const clockWord = 'When you slept — ' + (
      view==='last7'  ? 'nightly clock time'
    : (view==='means' ? 'weekly mean clock time'
    : (view==='medians'?'weekly median clock time'
    : (view==='mmeans'? 'monthly mean clock time'
    :                   'monthly median clock time'))));
  document.getElementById('durTitle').textContent = durWord;
  document.getElementById('clockTitle').textContent = clockWord;
  renderDuration(v);
  renderClock(v);
}
document.querySelectorAll('#timingTabs .tab').forEach(btn=>{
  btn.addEventListener('click',()=>{
    document.querySelectorAll('#timingTabs .tab').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    showView(btn.dataset.view);
  });
});
showView('last7');

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

// ---- Archetype table ---------------------------------------------------- //
(function(){
  const tbody=document.querySelector('#archetypeTable tbody');
  if(!A.table7.length){
    tbody.innerHTML='<tr><td colspan="6" class="axis">No recent data.</td></tr>';
    return;
  }
  const pill=(txt,bg,fg)=>
    '<span class="pill" style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  const compPill=(txt,bg,fg,bi,ei)=>
    '<span class="pill persona-open" role="button" tabindex="0" '
    + 'data-bi="'+bi+'" data-ei="'+ei+'" '
    + 'style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  A.table7.forEach(r=>{
    const tr=document.createElement('tr');
    tr.innerHTML =
      '<td class="date">'+r.date+'</td>'+
      '<td class="time">'+r.begin+'</td>'+
      '<td class="time">'+r.end+'</td>'+
      '<td>'+pill(r.begin_type, r.begin_bg, r.begin_fg)+'</td>'+
      '<td>'+pill(r.end_type,   r.end_bg,   r.end_fg)+'</td>'+
      '<td>'+compPill(r.composite, r.comp_bg, r.comp_fg, r.bi, r.ei)+'</td>';
    tbody.appendChild(tr);
  });
})();

// ---- Decision support (Targeted Asleep Time) ---------------------------- //
(function(){
  const cfg = A.tat_config;
  const PULL = [0.15, 0.30, 0.50];          // gentle / moderate / strong
  const PULL_LABEL = ['gentle', 'moderate', 'strong'];
  const slider = document.getElementById('dsSlider');
  const tl = document.getElementById('dsTimeline');
  const notesEl = document.getElementById('dsNotes');

  // Last up-to-7 nights, oldest→newest, on the minutes-since-noon frame.
  const last7 = A.series.slice(-7);
  const begins = last7.map(d => d.bed_min);
  const wakes  = last7.map(d => d.wake_min);

  function mean(a){ return a.reduce((s,x)=>s+x,0)/a.length; }
  // Recency-weighted average: newest night weighted most (a is oldest→newest,
  // so index i gets weight i+1: 1,2,3,…,n).
  function recencyWeighted(a){
    let num=0, den=0;
    for(let i=0;i<a.length;i++){ const w=i+1; num+=w*a[i]; den+=w; }
    return den ? num/den : 0;
  }
  // Least-squares slope of begin-time vs. day index (min per day).
  function slope(a){
    const n=a.length; if(n<2) return 0;
    const xm=(n-1)/2, ym=mean(a);
    let num=0, den=0;
    for(let i=0;i<n;i++){ num+=(i-xm)*(a[i]-ym); den+=(i-xm)*(i-xm); }
    return den ? num/den : 0;
  }

  function computeTAT(pull){
    // Rule 2 — habit anchor: recency-weighted average of recent begin times
    // (last night counts most, tapering back over the window).
    const habit = recencyWeighted(begins);
    // Rule 3 — follow part of the day-over-day drift.
    const trend = cfg.trend_factor * slope(begins);
    // Rule 4 — earlier-than-usual wake today => earlier TAT (and vice versa).
    const wakeDev = wakes[wakes.length-1] - mean(wakes);
    const wake = cfg.wake_factor * wakeDev;
    let tat = habit + trend + wake;
    // Rule 5 — tilt toward Perfect Asleep Time by the slider fraction.
    tat = tat + pull*(cfg.pat - tat);
    // Rule 1 + clamp — keep within [floor, ceiling], round to 30 min.
    tat = Math.max(cfg.clamp_lo, Math.min(cfg.clamp_hi, tat));
    return { tat: Math.round(tat/30)*30, habit, trend, wake, wakeDev };
  }

  const STEPS = [
    { off:-90, title:'Step 1 — Start winding down',
       body:'Ambient lighting, a soothing beverage, no intense work.' },
    { off:-60, title:'Step 2 — Begin night-time routines',
       body:'Brush teeth, wash up, and settle your space for the night.' },
    { off:-30, title:'Step 3 — Ready for bed!',
       body:'Lights out and settle in. Sweet dreams!' },
  ];

  function render(){
    const pull = PULL[+slider.value];
    const r = computeTAT(pull);

    // Timeline (TAT itself is intentionally NOT shown).
    tl.innerHTML = STEPS.map(s => {
      const t = r.tat + s.off;                        // minutes-since-noon
      const dot = todHexFromNoon(t);
      return '<div class="ds-step">'
        + '<div class="ds-time">'+clockFromNoon(t)+'</div>'
        + '<div><span class="ds-dot" style="background:'+dot+'"></span></div>'
        + '<div><div class="ds-steptitle">'+s.title+'</div>'
        + '<div class="ds-stepbody">'+s.body+'</div></div>'
        + '</div>';
    }).join('');

    // Explanatory notes (right-hand side).
    const trendWord = Math.abs(r.trend) < 3 ? 'has been fairly steady'
      : (r.trend > 0 ? 'has been drifting later' : 'has been drifting earlier');
    const wakeWord = Math.abs(r.wakeDev) < 15 ? 'about your usual time'
      : (r.wakeDev < 0 ? 'earlier than usual' : 'later than usual');
    const wakeEffect = Math.abs(r.wakeDev) < 15 ? 'so it plays no real part today'
      : (r.wakeDev < 0
          ? 'so you may be tired sooner — nudging the plan a little earlier'
          : 'so sleep may come harder — nudging the plan a little later');
    const pat = clockFromNoon(cfg.pat);

    notesEl.innerHTML =
      '<h3>How these times were chosen</h3><ul>'
      + '<li>The plan is anchored to your <b>typical recent bedtime</b> '
        + '(a recency-weighted average of the last '+begins.length+' nights, '
        + 'so last night counts most and older nights taper off).</li>'
      + '<li>Your bedtime <b>'+trendWord+'</b> lately, which is taken into account '
        + '— chasing a sudden change rarely sticks.</li>'
      + '<li>You woke <b>'+wakeWord+'</b> today, '+wakeEffect+'.</li>'
      + '<li>The plan gently tilts toward an ideal of <b>'+pat+'</b>, at a '
        + '<b>'+PULL_LABEL[+slider.value]+'</b> level of ambition '
        + '(adjust with the slider above).</li>'
      + '<li>Each step is spaced to ease you in: wind-down, then routines '
        + '30 min later, then bed 30 min after that.</li>'
      + '</ul>';
  }

  slider.addEventListener('input', render);
  render();
})();

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

// ---- Theme (light/dark) ------------------------------------------------- //
(function(){
  const root = document.documentElement;
  // Default by time of day: dark from 9PM to 6AM, light otherwise.
  const hr = new Date().getHours();
  const auto = (hr >= 21 || hr < 6) ? 'dark' : 'light';
  root.setAttribute('data-theme', auto);
  const btn = document.getElementById('themeToggle');
  function setPressed(){
    btn.setAttribute('aria-pressed', root.getAttribute('data-theme')==='dark');
  }
  setPressed();
  btn.addEventListener('click', () => {
    root.setAttribute('data-theme',
      root.getAttribute('data-theme')==='dark' ? 'light' : 'dark');
    setPressed();
  });
})();

// ---- Sidebar scroll-spy ------------------------------------------------- //
(function(){
  const links = Array.from(document.querySelectorAll('.side-nav a'));
  const byId = Object.fromEntries(links.map(a => [a.dataset.target, a]));
  const sections = links.map(a => document.getElementById(a.dataset.target))
                        .filter(Boolean);
  if(!sections.length) return;

  function setActive(id){
    links.forEach(a => a.classList.toggle('active', a.dataset.target === id));
  }

  // Track how much of each section is visible; highlight the most-visible one.
  const ratios = new Map();
  const obs = new IntersectionObserver((entries) => {
    entries.forEach(e => ratios.set(e.target.id, e.intersectionRatio));
    let best = null, bestR = -1;
    sections.forEach(s => {
      const r = ratios.get(s.id) || 0;
      if(r > bestR) { bestR = r; best = s.id; }
    });
    // If nothing is meaningfully visible (between sections), keep the topmost
    // section that has scrolled past the top of the viewport.
    if(bestR <= 0) {
      for(const s of sections) {
        if(s.getBoundingClientRect().top <= window.innerHeight * 0.3) best = s.id;
      }
    }
    if(best) setActive(best);
  }, { threshold:[0,0.1,0.25,0.5,0.75,1], rootMargin:'-10% 0px -40% 0px' });
  sections.forEach(s => obs.observe(s));

  // Smooth-scroll + immediate highlight on click.
  links.forEach(a => a.addEventListener('click', () => setActive(a.dataset.target)));
})();

// ---- Colour-palette modal ----------------------------------------------- //
(function(){
  const overlay = document.getElementById('paletteModal');
  const openBtn = document.getElementById('paletteOpen');
  const closeBtn = document.getElementById('paletteClose');
  const rows = document.getElementById('paletteRows');

  // Build one row per hour of the day using the shared time-of-day palette.
  let html='';
  for(let h=0; h<24; h++){
    const hex = todHex(h*60).toUpperCase();
    const label = String(h).padStart(2,'0')+':00';
    html += '<tr>'
      + '<td class="pal-time">'+label+'</td>'
      + '<td><button class="swatch" style="background:'+hex+'" '
        + 'data-hex="'+hex+'" title="Copy '+hex+'" aria-label="Copy '+hex+'"></button></td>'
      + '<td><button class="hexbtn" data-hex="'+hex+'">'+hex+'</button></td>'
      + '</tr>';
  }
  rows.innerHTML = html;

  function copyHex(hex, btn){
    const done = () => {
      if(btn.classList.contains('hexbtn')){
        const orig = btn.textContent; btn.textContent='Copied!'; btn.classList.add('copied');
        setTimeout(()=>{ btn.textContent=orig; btn.classList.remove('copied'); }, 1100);
      } else {
        const hb = btn.closest('tr').querySelector('.hexbtn');
        if(hb){ const o=hb.textContent; hb.textContent='Copied!'; hb.classList.add('copied');
          setTimeout(()=>{ hb.textContent=o; hb.classList.remove('copied'); },1100); }
      }
    };
    if(navigator.clipboard && navigator.clipboard.writeText){
      navigator.clipboard.writeText(hex).then(done).catch(()=>fallback(hex,done));
    } else { fallback(hex, done); }
  }
  function fallback(text, done){
    const ta=document.createElement('textarea'); ta.value=text;
    ta.style.position='fixed'; ta.style.opacity='0'; document.body.appendChild(ta);
    ta.select(); try{ document.execCommand('copy'); }catch(e){}
    document.body.removeChild(ta); done();
  }
  rows.addEventListener('click', (e) => {
    const b = e.target.closest('[data-hex]');
    if(b) copyHex(b.dataset.hex, b);
  });

  function open(){ overlay.hidden=false; document.body.style.overflow='hidden'; }
  function close(){ overlay.hidden=true; document.body.style.overflow=''; }
  openBtn.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if(e.target===overlay) close(); });
  document.addEventListener('keydown', (e) => { if(e.key==='Escape' && !overlay.hidden) close(); });
})();

// ---- Persona cards modal ------------------------------------------------ //
(function(){
  const overlay = document.getElementById('personaModal');
  const head = document.getElementById('personaHead');
  const titleEl = document.getElementById('personaTitle');
  const tagsEl = document.getElementById('personaTags');
  const hoursEl = document.getElementById('personaHours');
  const detailEl = document.getElementById('personaDetail');
  const healthEl = document.getElementById('personaHealth');
  const closeBtn = document.getElementById('personaClose');

  function tag(txt, bg, fg, sub){
    return '<span class="persona-tag" style="background:'+bg+';color:'+fg+'">'
      + txt + (sub ? '<small>'+sub+'</small>' : '') + '</span>';
  }

  function openCard(bi, ei){
    const c = (PERSONA_CARDS[bi]||[])[ei];
    if(!c) return;
    titleEl.textContent = c.name;
    document.getElementById('personaIcon').innerHTML = c.icon || '';
    // Tint the header with the persona's blended colour.
    head.style.background = c.bg;
    head.style.color = c.fg;
    // ensure the eyebrow + close inherit readable colour on the tint
    head.querySelectorAll('.persona-eyebrow, h2, .modal-close')
        .forEach(el => el.style.color = c.fg);
    tagsEl.innerHTML =
      tag(c.begin_label, c.begin_bg, c.begin_fg, c.begin_sub)
      + '<span class="persona-plus">+</span>'
      + tag(c.end_label, c.end_bg, c.end_fg, c.end_sub);
    hoursEl.textContent = c.hours;
    detailEl.textContent = c.detail;
    healthEl.textContent = c.health;
    overlay.hidden = false;
    document.body.style.overflow = 'hidden';
  }
  function close(){ overlay.hidden=true; document.body.style.overflow=''; }

  // Delegate clicks/keys from any persona trigger (reference cells + composite pills).
  function handle(e){
    const t = e.target.closest('.persona-open');
    if(!t) return;
    if(e.type==='keydown' && e.key!=='Enter' && e.key!==' ') return;
    if(e.type==='keydown') e.preventDefault();
    openCard(+t.dataset.bi, +t.dataset.ei);
  }
  document.addEventListener('click', handle);
  document.addEventListener('keydown', handle);

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', (e) => { if(e.target===overlay) close(); });
  document.addEventListener('keydown', (e) => { if(e.key==='Escape' && !overlay.hidden) close(); });
})();
