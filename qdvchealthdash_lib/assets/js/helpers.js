
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

