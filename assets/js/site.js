// Theme switch, the body tour, card reveals, writing filters and the travel map.
// Every page still reads fine without this file.
(function () {
  'use strict';

  var root = document.documentElement;
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  document.querySelectorAll('[data-year]').forEach(function (el) {
    el.textContent = String(new Date().getFullYear());
  });

  /* ---------------------------------------------------------------- theme */

  var toggle = document.querySelector('[data-theme-toggle]');
  var systemDark = window.matchMedia('(prefers-color-scheme: dark)');

  function savedTheme() {
    try {
      return localStorage.getItem('ek-theme');
    } catch (e) {
      return null;
    }
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    if (toggle) {
      var dark = theme === 'dark';
      toggle.setAttribute('aria-pressed', dark ? 'true' : 'false');
      toggle.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    }
    document.dispatchEvent(new CustomEvent('ek:themechange'));
  }

  applyTheme(root.getAttribute('data-theme') || (systemDark.matches ? 'dark' : 'light'));

  if (toggle) {
    toggle.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
      try {
        localStorage.setItem('ek-theme', next);
      } catch (e) {}
      applyTheme(next);
    });
  }

  if (systemDark.addEventListener) {
    systemDark.addEventListener('change', function (event) {
      if (!savedTheme()) applyTheme(event.matches ? 'dark' : 'light');
    });
  }

  /* ---------------------------------------------------------------- card reveals */

  var revealables = document.querySelectorAll('[data-reveal]');
  if ('IntersectionObserver' in window && !reduceMotion.matches && revealables.length) {
    root.classList.add('reveal-ready');
    var revealer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        entry.target.classList.add('is-in');
        revealer.unobserve(entry.target);
      });
    }, { rootMargin: '0px 0px -12% 0px' });
    revealables.forEach(function (el) {
      revealer.observe(el);
    });
  }

  /* ---------------------------------------------------------------- body tour */

  var stage = document.querySelector('[data-stage]');
  var chapters = Array.prototype.slice.call(document.querySelectorAll('[data-chapter]'));

  if (stage && chapters.length) {
    var tour = stage.closest('.tour');
    var figLabel = stage.querySelector('[data-fig-label]');
    var zoomLabel = stage.querySelector('[data-zoom]');
    var stacked = window.matchMedia('(max-width: 860px)');
    var current = null;
    var queued = false;

    var setPart = function (part, fig, zoom) {
      if (part === current) return;
      current = part;
      stage.setAttribute('data-part', part);
      if (figLabel) figLabel.textContent = fig;
      if (zoomLabel) zoomLabel.textContent = zoom;
    };

    var update = function () {
      queued = false;
      var viewport = window.innerHeight;
      // The reading line: halfway down the screen, or on phones a third of the way
      // into the space under the pinned character.
      var line = viewport * 0.5;
      if (stacked.matches) {
        var stageBottom = stage.getBoundingClientRect().bottom;
        line = stageBottom + (viewport - stageBottom) * 0.33;
      }
      var active = null;
      for (var i = 0; i < chapters.length; i++) {
        if (chapters[i].getBoundingClientRect().top <= line) active = chapters[i];
      }
      if (tour && tour.getBoundingClientRect().bottom < line) active = chapters[chapters.length - 1];
      if (active) {
        setPart(active.getAttribute('data-chapter'), active.getAttribute('data-fig'), active.getAttribute('data-zoom'));
      } else {
        setPart('intro', 'eoin.png', 'x1');
      }
    };

    var queue = function () {
      if (queued) return;
      queued = true;
      window.requestAnimationFrame(update);
    };

    window.addEventListener('scroll', queue, { passive: true });
    window.addEventListener('resize', queue);
    update();
  }

  /* ---------------------------------------------------------------- the character looks around */

  var eyes = Array.prototype.slice.call(document.querySelectorAll('.eyes'));
  if (eyes.length && !reduceMotion.matches) {
    window.addEventListener('pointermove', function (event) {
      var x = (event.clientX / window.innerWidth - 0.5) * 2;
      var y = (event.clientY / window.innerHeight - 0.5) * 2;
      // Roughly one pixel of the sprite grid, so he glances rather than rolls his eyes.
      var shift = 'translate(' + (x * 0.8).toFixed(2) + 'px, ' + (y * 0.6).toFixed(2) + 'px)';
      eyes.forEach(function (pair) {
        pair.style.transform = shift;
      });
    }, { passive: true });
  }

  var heroSprite = document.querySelector('.hero-sprite');
  if (heroSprite && !reduceMotion.matches) {
    heroSprite.addEventListener('click', function () {
      heroSprite.classList.remove('jump');
      void heroSprite.offsetWidth;
      heroSprite.classList.add('jump');
    });
  }

  /* ---------------------------------------------------------------- how far down the page you are */

  var progressBar = document.querySelector('[data-progress]');
  if (progressBar) {
    var drawProgress = function () {
      var height = document.documentElement.scrollHeight - window.innerHeight;
      var done = height > 0 ? Math.min(1, Math.max(0, window.scrollY / height)) : 0;
      progressBar.style.transform = 'scaleX(' + done.toFixed(4) + ')';
    };
    var queuedProgress = false;
    window.addEventListener('scroll', function () {
      if (queuedProgress) return;
      queuedProgress = true;
      window.requestAnimationFrame(function () {
        queuedProgress = false;
        drawProgress();
      });
    }, { passive: true });
    window.addEventListener('resize', drawProgress);
    drawProgress();
  }

  /* ---------------------------------------------------------------- for anyone who still knows the code */

  var code = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
  var typed = 0;
  document.addEventListener('keydown', function (event) {
    var key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
    typed = key === code[typed] ? typed + 1 : (key === code[0] ? 1 : 0);
    if (typed < code.length) return;
    typed = 0;
    document.body.classList.add('cheat');
    var toast = document.createElement('p');
    toast.className = 'toast';
    toast.setAttribute('role', 'status');
    toast.textContent = 'Cheat found. Press it again to stop the colours.';
    document.body.appendChild(toast);
    window.setTimeout(function () {
      toast.remove();
    }, 4000);
    if (document.body.classList.contains('cheat-on')) {
      document.body.classList.remove('cheat', 'cheat-on');
      toast.textContent = 'Back to normal.';
    } else {
      document.body.classList.add('cheat-on');
    }
  });

  /* ---------------------------------------------------------------- writing filters */

  var filters = Array.prototype.slice.call(document.querySelectorAll('[data-filter]'));
  var papers = Array.prototype.slice.call(document.querySelectorAll('.paper[data-type]'));

  filters.forEach(function (button) {
    button.addEventListener('click', function () {
      var type = button.getAttribute('data-filter');
      filters.forEach(function (other) {
        other.setAttribute('aria-pressed', other === button ? 'true' : 'false');
      });
      papers.forEach(function (paper) {
        paper.hidden = type !== 'all' && paper.getAttribute('data-type') !== type;
      });
    });
  });

  /* ---------------------------------------------------------------- the tabbed history */

  document.querySelectorAll('[data-tabs]').forEach(function (group) {
    var tabs = Array.prototype.slice.call(group.querySelectorAll('[role="tab"]'));
    if (!tabs.length) return;

    var show = function (tab, moveFocus) {
      tabs.forEach(function (other) {
        var chosen = other === tab;
        other.setAttribute('aria-selected', chosen ? 'true' : 'false');
        other.tabIndex = chosen ? 0 : -1;
        var panel = document.getElementById(other.getAttribute('aria-controls'));
        if (panel) panel.hidden = !chosen;
      });
      if (moveFocus) tab.focus();
    };

    tabs.forEach(function (tab, index) {
      tab.addEventListener('click', function () {
        show(tab, false);
      });
      tab.addEventListener('keydown', function (event) {
        var step = event.key === 'ArrowRight' ? 1 : event.key === 'ArrowLeft' ? -1 : 0;
        if (step) {
          event.preventDefault();
          show(tabs[(index + step + tabs.length) % tabs.length], true);
        } else if (event.key === 'Home') {
          event.preventDefault();
          show(tabs[0], true);
        } else if (event.key === 'End') {
          event.preventDefault();
          show(tabs[tabs.length - 1], true);
        }
      });
    });
  });

  /* ---------------------------------------------------------------- travel map */

  var world = window.EK_WORLD;
  var travel = window.EK_TRAVEL || { visited: [] };
  var canvas = document.querySelector('[data-map]');
  var list = document.querySelector('[data-country-list]');
  var count = document.querySelector('[data-country-count]');
  var readout = document.querySelector('[data-map-readout]');
  var mapFile = document.querySelector('[data-map-file]');
  var viewButtons = Array.prototype.slice.call(document.querySelectorAll('[data-map-view]'));

  var visited = travel.visited.map(function (entry) {
    return typeof entry === 'string' ? { label: entry } : entry;
  });

  if (list) {
    visited.forEach(function (entry) {
      var li = document.createElement('li');
      li.textContent = entry.label;
      if (entry.note) {
        var note = document.createElement('span');
        note.textContent = entry.note;
        li.appendChild(note);
      }
      list.appendChild(li);
    });
  }

  // Count countries once each, however many labels point at them.
  var visitedNames = {};
  visited.forEach(function (entry) {
    visitedNames[(entry.map || entry.label).toLowerCase()] = true;
  });
  if (count) count.textContent = String(Object.keys(visitedNames).length);

  if (!world || !world.views || !canvas || !canvas.getContext) return;

  var nameIndex = {};
  world.names.forEach(function (name, i) {
    nameIndex[name.toLowerCase()] = i;
  });

  var been = {};
  Object.keys(visitedNames).forEach(function (name) {
    if (nameIndex[name] === undefined) {
      if (window.console) console.warn('Travel map: no country called "' + name + '"');
    } else {
      been[nameIndex[name]] = true;
    }
  });

  var ctx = canvas.getContext('2d');
  var W = 0;
  var H = 0;
  var grid = null;
  var litOrder = {};
  var progress = reduceMotion.matches ? 1 : 0;
  var hovered = -1;
  var colours = {};
  var animation = 0;
  var hasBeenSeen = false;
  var defaultReadout = window.matchMedia('(hover: none)').matches ? 'Tap a country' : 'Point at a country';
  if (readout) readout.textContent = defaultReadout;

  var readColours = function () {
    var style = getComputedStyle(root);
    colours.land = style.getPropertyValue('--map-land').trim();
    colours.visited = style.getPropertyValue('--map-visited').trim();
    colours.hover = style.getPropertyValue('--map-hover').trim();
  };

  var size = function () {
    var box = canvas.parentElement;
    var styles = getComputedStyle(box);
    var available = box.clientWidth - parseFloat(styles.paddingLeft) - parseFloat(styles.paddingRight);
    var maxHeight = window.innerHeight * 0.66;
    var cssWidth = Math.floor(Math.min(available, maxHeight * W / H));
    if (cssWidth <= 0) return;
    var ratio = window.devicePixelRatio || 1;
    canvas.style.width = cssWidth + 'px';
    canvas.width = Math.round(cssWidth * ratio);
    canvas.height = Math.round(cssWidth * ratio * H / W);
  };

  var draw = function () {
    if (!grid) return;
    var cellSize = canvas.width / W;
    var gap = Math.max(1, cellSize * 0.14);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (var y = 0; y < H; y++) {
      for (var x = 0; x < W; x++) {
        var country = grid[y * W + x];
        if (country < 0) continue;
        var lit = litOrder[country] !== undefined && progress >= litOrder[country];
        if (country === hovered) ctx.fillStyle = colours.hover;
        else ctx.fillStyle = lit ? colours.visited : colours.land;
        ctx.fillRect(x * cellSize + gap / 2, y * cellSize + gap / 2, cellSize - gap, cellSize - gap);
      }
    }
  };

  var animate = function () {
    if (reduceMotion.matches) {
      progress = 1;
      draw();
      return;
    }
    var token = ++animation;
    var start = null;
    progress = 0;
    var step = function (time) {
      if (token !== animation) return;
      if (start === null) start = time;
      progress = Math.min(1, (time - start) / 1600);
      draw();
      if (progress < 1) window.requestAnimationFrame(step);
    };
    window.requestAnimationFrame(step);
  };

  var useView = function (name) {
    var view = world.views[name];
    if (!view) return;
    W = view.w;
    H = view.h;
    grid = new Int16Array(W * H).fill(-1);
    view.rows.forEach(function (runs, y) {
      for (var i = 0; i < runs.length; i += 3) {
        for (var x = runs[i]; x < runs[i] + runs[i + 1]; x++) grid[y * W + x] = runs[i + 2];
      }
    });

    // Visited countries in this view light up in turn, west to east.
    var firstColumn = {};
    for (var cell = 0; cell < grid.length; cell++) {
      var c = grid[cell];
      if (c < 0 || !been[c]) continue;
      var col = cell % W;
      if (firstColumn[c] === undefined || col < firstColumn[c]) firstColumn[c] = col;
    }
    var shown = Object.keys(firstColumn).map(Number).sort(function (a, b) {
      return firstColumn[a] - firstColumn[b];
    });
    litOrder = {};
    shown.forEach(function (c, i) {
      litOrder[c] = shown.length > 1 ? i / (shown.length - 1) : 0;
    });

    viewButtons.forEach(function (button) {
      button.setAttribute('aria-pressed', button.getAttribute('data-map-view') === name ? 'true' : 'false');
    });
    if (mapFile) mapFile.textContent = name + '.map';
    hovered = -1;
    if (readout) readout.textContent = defaultReadout;
    size();
  };

  var pointAt = function (event) {
    var rect = canvas.getBoundingClientRect();
    var x = Math.floor((event.clientX - rect.left) / rect.width * W);
    var y = Math.floor((event.clientY - rect.top) / rect.height * H);
    var country = x >= 0 && x < W && y >= 0 && y < H ? grid[y * W + x] : -1;
    if (country === hovered) return;
    hovered = country;
    if (readout) {
      readout.textContent = country < 0 ? defaultReadout : world.names[country];
    }
    draw();
  };

  canvas.addEventListener('pointermove', pointAt);
  canvas.addEventListener('pointerdown', pointAt);
  canvas.addEventListener('pointerleave', function () {
    hovered = -1;
    if (readout) readout.textContent = defaultReadout;
    draw();
  });

  viewButtons.forEach(function (button) {
    button.addEventListener('click', function () {
      useView(button.getAttribute('data-map-view'));
      if (hasBeenSeen) animate();
      else draw();
    });
  });

  document.addEventListener('ek:themechange', function () {
    readColours();
    draw();
  });

  window.addEventListener('resize', function () {
    size();
    draw();
  });

  readColours();
  useView('world');
  draw();

  if (!reduceMotion.matches && 'IntersectionObserver' in window) {
    var mapWatcher = new IntersectionObserver(function (entries) {
      if (!entries[0].isIntersecting) return;
      mapWatcher.disconnect();
      hasBeenSeen = true;
      animate();
    }, { threshold: 0.3 });
    mapWatcher.observe(canvas);
  } else {
    hasBeenSeen = true;
    progress = 1;
    draw();
  }
})();
