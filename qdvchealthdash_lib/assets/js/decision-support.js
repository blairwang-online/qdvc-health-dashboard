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

