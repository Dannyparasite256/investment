// UX suite: search, command palette, tour, confetti, PWA, lightbox, density
(function () {
  'use strict';
  if (window.__ciUxLoaded) return;
  window.__ciUxLoaded = true;

  function qs(s, r) { return (r || document).querySelector(s); }
  function qsa(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function csrf() {
    var el = qs('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    var m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }
  window.celebrate = function () {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
    var c = document.getElementById('confetti-canvas');
    if (!c) {
      c = document.createElement('canvas');
      c.id = 'confetti-canvas';
      document.body.appendChild(c);
    }
    var ctx = c.getContext('2d');
    c.width = window.innerWidth;
    c.height = window.innerHeight;
    var parts = [];
    var colors = ['#8B5CF6', '#3B82F6', '#22C55E', '#F59E0B', '#EC4899'];
    for (var i = 0; i < 90; i++) {
      parts.push({
        x: Math.random() * c.width,
        y: -20 - Math.random() * 80,
        r: 3 + Math.random() * 5,
        c: colors[i % colors.length],
        vx: -2 + Math.random() * 4,
        vy: 2 + Math.random() * 4,
        a: Math.random() * Math.PI,
      });
    }
    var start = performance.now();
    function frame(now) {
      var t = now - start;
      ctx.clearRect(0, 0, c.width, c.height);
      parts.forEach(function (p) {
        p.x += p.vx;
        p.y += p.vy;
        p.a += 0.1;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.a);
        ctx.fillStyle = p.c;
        ctx.fillRect(-p.r, -p.r, p.r * 2, p.r * 1.2);
        ctx.restore();
      });
      if (t < 1600) requestAnimationFrame(frame);
      else { ctx.clearRect(0, 0, c.width, c.height); }
    }
    requestAnimationFrame(frame);
  };
  if (qs('.alert-success')) {
    setTimeout(function () { celebrate(); }, 200);
  }
  window.toggleDensity = function () {
    var shell = qs('.app-shell');
    if (!shell) return;
    var next = shell.getAttribute('data-density') === 'compact' ? 'comfortable' : 'compact';
    shell.setAttribute('data-density', next);
    document.cookie = 'density=' + next + ';path=/;max-age=31536000;samesite=lax';
  };
  (function () {
    var box = qs('#lightbox');
    var img = qs('#lightbox-img');
    if (!box || !img) return;
    document.addEventListener('click', function (e) {
      var a = e.target.closest('[data-lightbox]');
      if (!a) return;
      e.preventDefault();
      img.src = a.getAttribute('href') || a.getAttribute('src') || (a.querySelector('img') && a.querySelector('img').src);
      box.classList.remove('d-none');
    });
    function close() { box.classList.add('d-none'); img.src = ''; }
    var cl = qs('.lightbox-close', box);
    if (cl) cl.addEventListener('click', close);
    box.addEventListener('click', function (e) { if (e.target === box) close(); });
    document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });
  })();
  (function () {
    var input = qs('#global-search-input');
    var pop = qs('#search-popover');
    if (!input || !pop) return;
    var timer = null;
    function position() {
      var r = input.getBoundingClientRect();
      pop.style.top = (r.bottom + 8) + 'px';
      pop.style.left = Math.max(8, r.left) + 'px';
    }
    function render(results) {
      if (!results.length) {
        pop.innerHTML = '<div class="p-3 small text-muted">No results</div>';
      } else {
        pop.innerHTML = results.map(function (r) {
          return '<a href="' + r.url + '"><i class="bi ' + (r.icon || 'bi-search') + '"></i><span><strong class="d-block small">' +
            (r.title || '') + '</strong><span class="text-muted small">' + (r.subtitle || '') + '</span></span></a>';
        }).join('');
      }
      pop.classList.remove('d-none');
      position();
    }
    function search(q) {
      if (!q || q.length < 2) { pop.classList.add('d-none'); return; }
      fetch('/search/?q=' + encodeURIComponent(q) + '&format=json', {
        headers: { Accept: 'application/json' }, credentials: 'same-origin',
      })
        .then(function (r) { return r.json(); })
        .then(function (d) { render(d.results || []); })
        .catch(function () {});
    }
    input.addEventListener('input', function () {
      clearTimeout(timer);
      timer = setTimeout(function () { search(input.value.trim()); }, 200);
    });
    input.addEventListener('focus', function () {
      if (input.value.trim().length >= 2) search(input.value.trim());
    });
    input.addEventListener('keydown', function (e) {
      if (e.key === 'Enter') {
        e.preventDefault();
        window.location.href = '/search/?q=' + encodeURIComponent(input.value.trim());
      }
    });
    document.addEventListener('click', function (e) {
      if (!pop.contains(e.target) && e.target !== input) pop.classList.add('d-none');
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && !e.metaKey && !e.ctrlKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
        e.preventDefault();
        input.focus();
      }
    });
  })();
  (function () {
    var overlay = qs('#cmdk-overlay');
    var input = qs('#cmdk-input');
    var results = qs('#cmdk-results');
    if (!overlay || !input || !results) return;
    var items = [];
    var filtered = [];
    var active = 0;

    function open() {
      overlay.classList.remove('d-none');
      overlay.setAttribute('aria-hidden', 'false');
      input.value = '';
      input.focus();
      render('');
    }
    function close() {
      overlay.classList.add('d-none');
      overlay.setAttribute('aria-hidden', 'true');
    }
    function ensureData(cb) {
      if (items.length) return cb();
      fetch('/api/command-palette/', { headers: { Accept: 'application/json' }, credentials: 'same-origin' })
        .then(function (r) { return r.json(); })
        .then(function (d) { items = d.items || []; cb(); })
        .catch(function () { items = []; cb(); });
    }
    function render(q) {
      q = (q || '').toLowerCase();
      filtered = items.filter(function (it) {
        var hay = (it.title + ' ' + (it.keywords || '')).toLowerCase();
        return !q || hay.indexOf(q) >= 0;
      }).slice(0, 12);
      active = 0;
      results.innerHTML = filtered.map(function (it, i) {
        return '<button type="button" class="cmdk-item' + (i === 0 ? ' active' : '') + '" data-url="' + it.url + '">' +
          '<i class="bi ' + (it.icon || 'bi-arrow-right') + '"></i><span>' + it.title + '</span></button>';
      }).join('') || '<div class="p-3 small text-muted">No matches</div>';
      qsa('.cmdk-item', results).forEach(function (btn) {
        btn.addEventListener('click', function () { window.location.href = btn.getAttribute('data-url'); });
      });
    }
    document.addEventListener('keydown', function (e) {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        ensureData(function () { open(); });
      }
      if (overlay.classList.contains('d-none')) return;
      if (e.key === 'Escape') close();
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        active = Math.min(active + 1, filtered.length - 1);
        highlight();
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        active = Math.max(active - 1, 0);
        highlight();
      }
      if (e.key === 'Enter' && filtered[active]) {
        e.preventDefault();
        window.location.href = filtered[active].url;
      }
    });
    function highlight() {
      qsa('.cmdk-item', results).forEach(function (el, i) {
        el.classList.toggle('active', i === active);
      });
    }
    input.addEventListener('input', function () { render(input.value); });
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
  })();
  (function () {
    var root = qs('#tour-root');
    if (!root) return;
    var steps = [
      { title: 'Welcome aboard', body: 'Your dashboard shows balances, profit, and quick actions. We’ll walk through the essentials.' },
      { title: 'Fund your wallet', body: 'Use Deposit to send crypto. Always match the network (TRC20 / ERC20 / BEP20).', tour: 'deposit' },
      { title: 'Choose a plan', body: 'Browse Investments, compare plans, then lock an amount to start earning.', tour: 'invest' },
      { title: 'Invite & grow', body: 'Share your referral link and climb VIP tiers for better fees.', tour: 'refer' },
    ];
    var i = 0;
    var title = qs('#tour-title');
    var body = qs('#tour-body');
    var num = qs('#tour-step-num');
    var next = qs('#tour-next');
    var skip = qs('#tour-skip');

    function show() {
      var s = steps[i];
      if (title) title.textContent = s.title;
      if (body) body.textContent = s.body;
      if (num) num.textContent = String(i + 1);
      if (next) next.textContent = i === steps.length - 1 ? 'Finish' : 'Next';
    }
    function complete() {
      root.remove();
      fetch('/tour/complete/', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrf(), 'X-Requested-With': 'XMLHttpRequest' },
        credentials: 'same-origin',
      }).catch(function () {});
    }
    if (next) next.addEventListener('click', function () {
      if (i >= steps.length - 1) { complete(); return; }
      i += 1;
      show();
    });
    if (skip) skip.addEventListener('click', complete);
    show();
  })();
  (function () {
    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(function () {});
    }
    var deferred = null;
    var banner = qs('#pwa-banner');
    window.addEventListener('beforeinstallprompt', function (e) {
      e.preventDefault();
      deferred = e;
      if (banner && !localStorage.getItem('pwaDismissed')) banner.classList.remove('d-none');
    });
    var install = qs('#pwa-install');
    var dismiss = qs('#pwa-dismiss');
    if (install) install.addEventListener('click', function () {
      if (!deferred) return;
      deferred.prompt();
      deferred.userChoice.finally(function () {
        deferred = null;
        if (banner) banner.classList.add('d-none');
      });
    });
    if (dismiss) dismiss.addEventListener('click', function () {
      localStorage.setItem('pwaDismissed', '1');
      if (banner) banner.classList.add('d-none');
    });
  })();
  if (!qs('link[rel=manifest]')) {
    var l = document.createElement('link');
    l.rel = 'manifest';
    l.href = '/manifest.json';
    document.head.appendChild(l);
  }
})();
