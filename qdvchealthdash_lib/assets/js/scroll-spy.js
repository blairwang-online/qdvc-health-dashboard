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

