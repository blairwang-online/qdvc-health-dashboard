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

