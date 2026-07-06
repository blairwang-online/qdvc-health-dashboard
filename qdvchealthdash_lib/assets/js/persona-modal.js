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

