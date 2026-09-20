// Runs before the page paints so dark mode never flashes light first.
(function () {
  var root = document.documentElement;
  root.classList.add('js');
  var theme = null;
  try {
    theme = localStorage.getItem('ek-theme');
  } catch (e) {}
  if (theme !== 'light' && theme !== 'dark') {
    theme = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }
  root.setAttribute('data-theme', theme);
})();
