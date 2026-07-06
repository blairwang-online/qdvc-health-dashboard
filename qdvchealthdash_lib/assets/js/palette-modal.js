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

