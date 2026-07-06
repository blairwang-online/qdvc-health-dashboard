// ===================================================================== //
// Mobile dashboard glue.
//
// Wires the mobile-only chrome on top of the shared render helpers. The heavy
// lifting is reused from the desktop components that ship in the mobile JS
// bundle (see assets._MOBILE_JS_FILES):
//   * data.js / helpers.js  — A, PERSONA_CARDS, clock + palette helpers, and
//     buildView (normalises last7 / weekly / monthly into one item shape).
//   * chart-clock.js         — renderClock(view) draws the "when you slept"
//     horizontal-bar chart into #clock.
//   * punctuality.js         — renderPunctuality(pview) draws the punctuality
//     line chart into #punct / #punctLegend / #punctTitle.
//   * decision-support-mobile.js — the slider-free "moderate" wind-down plan.
//   * persona-modal.js       — the persona card modal (shared, unchanged).
//   * theme.js               — light/dark toggle (shared, unchanged).
//
// This file adds: the sticky segmented section nav (scroll-spy + tap-to-jump),
// the in-card view toggles for the timing and punctuality charts, the compact
// per-night archetype list, and the reference-table modal.
// ===================================================================== //

// ---- Timing chart: Last 7 / Weekly means / Monthly means ------------- //
// Mobile shows the clock-time chart only (no duration chart, no medians).
(function(){
  const host = document.getElementById('clock');
  if(!host) return;
  const titleEl = document.getElementById('clockTitle');
  const TITLES = {
    last7:  'When you slept — nightly clock time',
    means:  'When you slept — weekly mean clock time',
    mmeans: 'When you slept — monthly mean clock time',
  };
  function show(view){
    if(titleEl) titleEl.textContent = TITLES[view] || TITLES.last7;
    renderClock(buildView(view));
  }
  document.querySelectorAll('#timingToggle .tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#timingToggle .tab')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      show(btn.dataset.view);
    });
  });
  show('last7');
})();

// ---- Punctuality: Weekly / Monthly benchmarks (no thresholds) -------- //
(function(){
  const host = document.getElementById('punct');
  if(!host) return;
  document.querySelectorAll('#punctToggle .tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('#punctToggle .tab')
        .forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderPunctuality(btn.dataset.pview);   // 'weekly' | 'monthly'
    });
  });
  renderPunctuality('weekly');
})();

// ---- Compact per-night archetype list (past 7 days) ------------------ //
(function(){
  const host = document.getElementById('archetypeList');
  if(!host) return;
  if(!A.table7.length){
    host.innerHTML = '<p class="cap">No recent data.</p>';
    return;
  }
  const pill = (txt,bg,fg) =>
    '<span class="pill" style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  const compPill = (txt,bg,fg,bi,ei) =>
    '<span class="pill persona-open" role="button" tabindex="0" '
    + 'data-bi="'+bi+'" data-ei="'+ei+'" '
    + 'style="background:'+bg+';color:'+fg+'">'+txt+'</span>';
  host.innerHTML = A.table7.map(r =>
    '<div class="m-arch-row">'
    + '<span class="m-arch-date">'+r.date+'</span>'
    + '<span class="m-arch-time">'+r.begin+' → '+r.end+'</span>'
    + '<div class="m-arch-pills">'
      + pill(r.begin_type, r.begin_bg, r.begin_fg)
      + pill(r.end_type, r.end_bg, r.end_fg)
      + compPill(r.composite, r.comp_bg, r.comp_fg, r.bi, r.ei)
    + '</div>'
    + '</div>'
  ).join('');
})();

// ---- Reference-table modal ------------------------------------------- //
(function(){
  const overlay = document.getElementById('refModal');
  const openBtn = document.getElementById('refOpen');
  const closeBtn = document.getElementById('refClose');
  if(!overlay || !openBtn) return;
  function open(){ overlay.hidden = false; document.body.style.overflow = 'hidden'; }
  function close(){ overlay.hidden = true; document.body.style.overflow = ''; }
  openBtn.addEventListener('click', open);
  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', e => { if(e.target === overlay) close(); });
  document.addEventListener('keydown', e => {
    if(e.key === 'Escape' && !overlay.hidden) close();
  });
})();

// ---- Sticky segmented nav (scroll-spy + tap-to-jump) ----------------- //
(function(){
  const btns = Array.from(document.querySelectorAll('.m-nav-btn'));
  if(!btns.length) return;
  const track = document.querySelector('.m-nav-track');
  const sections = btns
    .map(b => document.getElementById(b.dataset.target))
    .filter(Boolean);

  function setActive(id){
    btns.forEach(b => {
      const on = b.dataset.target === id;
      b.classList.toggle('active', on);
      // Keep the active chip in view within the horizontally scrolling track.
      if(on && track){
        const bl = b.offsetLeft, br = bl + b.offsetWidth;
        if(bl < track.scrollLeft) track.scrollTo({left:bl-12, behavior:'smooth'});
        else if(br > track.scrollLeft + track.clientWidth)
          track.scrollTo({left:br-track.clientWidth+12, behavior:'smooth'});
      }
    });
  }

  // Tapping a chip jumps to its section (native smooth scroll via CSS).
  btns.forEach(b => b.addEventListener('click', () => {
    const s = document.getElementById(b.dataset.target);
    if(s) s.scrollIntoView({behavior:'smooth', block:'start'});
    setActive(b.dataset.target);
  }));

  // Highlight the section nearest the top of the viewport as the page scrolls.
  // (Tap-to-jump above works regardless; this only adds live highlighting.)
  if(typeof IntersectionObserver === 'undefined') return;
  const ratios = new Map();
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => ratios.set(e.target.id, e.intersectionRatio));
    let best = null, bestR = -1;
    sections.forEach(s => {
      const r = ratios.get(s.id) || 0;
      if(r > bestR){ bestR = r; best = s.id; }
    });
    if(bestR <= 0){
      for(const s of sections){
        if(s.getBoundingClientRect().top <= window.innerHeight * 0.35) best = s.id;
      }
    }
    if(best) setActive(best);
  }, { threshold:[0,0.1,0.25,0.5,0.75,1], rootMargin:'-74px 0px -45% 0px' });
  sections.forEach(s => obs.observe(s));
})();
