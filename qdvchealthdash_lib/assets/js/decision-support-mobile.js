// ---- Decision support (mobile) — Targeted Asleep Time, moderate only ---- //
// A simplified version of the desktop decision-support module: the ambition is
// fixed at "moderate" (there is no slider on mobile), so the wind-down plan is
// computed once at load. The TAT recipe is otherwise identical to the desktop
// build (see MAINTENANCE.md §6); TAT itself is never displayed.
(function(){
  const cfg = A.tat_config;
  const PULL = 0.30;                 // moderate (matches the desktop midpoint)
  const tl = document.getElementById('dsTimeline');
  const notesEl = document.getElementById('dsNotes');
  if(!tl) return;

  // Last up-to-7 nights, oldest→newest, on the minutes-since-noon frame.
  const last7 = A.series.slice(-7);
  const begins = last7.map(d => d.bed_min);
  const wakes  = last7.map(d => d.wake_min);

  function mean(a){ return a.reduce((s,x)=>s+x,0)/a.length; }
  // Recency-weighted average: newest night weighted most (index i -> weight i+1).
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

  function computeTAT(){
    const habit = recencyWeighted(begins);
    const trend = cfg.trend_factor * slope(begins);
    const wakeDev = wakes[wakes.length-1] - mean(wakes);
    const wake = cfg.wake_factor * wakeDev;
    let tat = habit + trend + wake;
    tat = tat + PULL*(cfg.pat - tat);
    tat = Math.max(cfg.clamp_lo, Math.min(cfg.clamp_hi, tat));
    return { tat: Math.round(tat/30)*30, trend, wakeDev };
  }

  const STEPS = [
    { off:-90, title:'Step 1 — Start winding down',
       body:'Ambient lighting, a soothing beverage, no intense work.' },
    { off:-60, title:'Step 2 — Begin night-time routines',
       body:'Brush teeth, wash up, and settle your space for the night.' },
    { off:-30, title:'Step 3 — Ready for bed!',
       body:'Lights out and settle in. Sweet dreams!' },
  ];

  const r = computeTAT();
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

  if(notesEl){
    const trendWord = Math.abs(r.trend) < 3 ? 'has been fairly steady'
      : (r.trend > 0 ? 'has been drifting later' : 'has been drifting earlier');
    const wakeWord = Math.abs(r.wakeDev) < 15 ? 'about your usual time'
      : (r.wakeDev < 0 ? 'earlier than usual' : 'later than usual');
    const pat = clockFromNoon(cfg.pat);
    notesEl.innerHTML =
      '<h3>How these times were chosen</h3><ul>'
      + '<li>Anchored to your <b>typical recent bedtime</b> (a recency-weighted '
        + 'average of the last '+begins.length+' nights).</li>'
      + '<li>Your bedtime <b>'+trendWord+'</b> lately, and you woke <b>'+wakeWord
        + '</b> today — both are taken into account.</li>'
      + '<li>The plan tilts gently toward an ideal of <b>'+pat+'</b> at a '
        + '<b>moderate</b> level of ambition.</li>'
      + '</ul>';
  }
})();
