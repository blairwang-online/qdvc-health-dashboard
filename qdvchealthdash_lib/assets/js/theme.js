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

