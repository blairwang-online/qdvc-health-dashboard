const A = JSON.parse(document.getElementById('dashboard-data').textContent);
const PERSONA_CARDS = JSON.parse(document.getElementById('persona-cards').textContent);

// Animate the score arc.
(function(){
  const r=50, circ=2*Math.PI*r, arc=document.getElementById('scoreArc');
  const frac=Math.max(0,Math.min(1,A.score/100));
  arc.style.setProperty('--circ', circ);
  arc.setAttribute('stroke-dasharray', circ);
  arc.setAttribute('stroke-dashoffset', circ*(1-frac));
})();
