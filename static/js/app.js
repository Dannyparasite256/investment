/**
 * CryptoInvest — premium UI interactions
 * Theme · charts · counters · ripple · toasts · WebSocket
 */
(function () {
  'use strict';

  var EASE = 'cubic-bezier(0.4, 0, 0.2, 1)';

  // HTMX CSRF
  document.body.addEventListener('htmx:configRequest', function (event) {
    var csrf = document.querySelector('[name=csrfmiddlewaretoken]');
    if (csrf) event.detail.headers['X-CSRFToken'] = csrf.value;
    var cookie = document.cookie.split(';').map(function (c) { return c.trim(); })
      .find(function (c) { return c.startsWith('csrftoken='); });
    if (cookie) event.detail.headers['X-CSRFToken'] = cookie.split('=')[1];
  });

  // Theme
  window.setTheme = function (theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    var form = document.getElementById('theme-form');
    if (form) {
      var input = form.querySelector('[name=theme]');
      if (input) input.value = theme;
      if (window.htmx) {
        htmx.ajax('POST', form.action, { source: form, values: { theme: theme }, swap: 'none' });
      }
    }
    document.querySelectorAll('[data-theme-icon]').forEach(function (el) {
      el.className = theme === 'dark' ? 'bi bi-moon-stars-fill' : 'bi bi-sun-fill';
    });
  };

  window.toggleTheme = function () {
    var current = document.documentElement.getAttribute('data-theme') || 'dark';
    setTheme(current === 'dark' ? 'light' : 'dark');
  };

  (function initTheme() {
    var match = document.cookie.match(/(?:^|;\s*)theme=([^;]+)/);
    var stored = (match && match[1]) || localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', stored);
  })();

  window.toggleSidebar = function () {
    var sb = document.getElementById('sidebar');
    var ov = document.getElementById('sidebar-overlay');
    if (sb) sb.classList.toggle('show');
    if (ov) ov.classList.toggle('show');
  };

  window.copyText = async function (text, btn) {
    try {
      await navigator.clipboard.writeText(text);
      if (btn) {
        var original = btn.innerHTML;
        btn.innerHTML = '<i class="bi bi-check2"></i> Copied';
        setTimeout(function () { btn.innerHTML = original; }, 1500);
      }
    } catch (e) { console.warn('Copy failed', e); }
  };

  window.formatMoney = function (value, decimals) {
    decimals = decimals == null ? 2 : decimals;
    var n = Number(value);
    if (isNaN(n)) return decimals === 0 ? '0' : '0.00';
    return n.toLocaleString(undefined, {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  };

  /** Parse "1,234.56" / "5.05" / "137.07142857" into a number. */
  function parseAmount(str) {
    if (str == null || str === '') return NaN;
    var s = String(str).trim().replace(/[^\d.\-eE+]/g, '');
    // keep last dot as decimal if multiple (strip thousands commas already)
    return parseFloat(s);
  }

  /**
   * Infer decimal places from a formatted sample or target number.
   * UGX-style integers → 0; USD → 2; crypto → up to 8.
   */
  function inferDecimals(target, formatSample, explicit) {
    if (explicit != null && explicit !== '') {
      var d = parseInt(explicit, 10);
      if (!isNaN(d)) return Math.max(0, Math.min(8, d));
    }
    if (formatSample) {
      var sample = String(formatSample).replace(/,/g, '');
      if (sample.indexOf('.') === -1) return 0;
      var frac = sample.split('.')[1] || '';
      return Math.min(8, frac.length);
    }
    var t = String(target);
    if (t.indexOf('.') === -1) return 0;
    return Math.min(8, (t.split('.')[1] || '').replace(/0+$/, '').length || 2);
  }

  /**
   * Count from 0 (or `from`) up to target on an element.
   * Uses ease-out cubic; final text matches data-count-format when possible.
   */
  window.countUp = function (el, target, opts) {
    opts = opts || {};
    if (!el) return;
    var reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var to = typeof target === 'number' ? target : parseAmount(target);
    if (isNaN(to)) {
      if (opts.finalText != null) el.textContent = opts.finalText;
      return;
    }
    var from = opts.from != null ? opts.from : 0;
    var duration = opts.duration != null ? opts.duration : (Math.abs(to) > 100000 ? 1600 : 1200);
    var decimals = inferDecimals(to, opts.formatSample || el.getAttribute('data-count-format'), opts.decimals);
    var finalText = opts.finalText;

    if (reduce) {
      el.textContent = finalText != null ? finalText : formatMoney(to, decimals);
      return;
    }

    // Cancel any in-flight count on this element
    if (el._countUpRaf) cancelAnimationFrame(el._countUpRaf);
    el.classList.add('is-counting');
    var start = performance.now();

    function tick(now) {
      var p = Math.min(1, (now - start) / duration);
      // easeOutExpo-ish for a premium cash-register feel
      var eased = p === 1 ? 1 : 1 - Math.pow(2, -10 * p);
      var val = from + (to - from) * eased;
      el.textContent = formatMoney(val, decimals);
      if (p < 1) {
        el._countUpRaf = requestAnimationFrame(tick);
      } else {
        el.textContent = finalText != null ? finalText : formatMoney(to, decimals);
        el.classList.remove('is-counting');
        el._countUpRaf = null;
      }
    }
    el._countUpRaf = requestAnimationFrame(tick);
  };

  /** Run count-up on every [data-count-up] element (page load / refresh). */
  window.runPageCountUps = function () {
    var nodes = document.querySelectorAll('[data-count-up]');
    nodes.forEach(function (el, i) {
      var raw = el.getAttribute('data-count-to');
      if (raw == null || raw === '') {
        raw = el.getAttribute('data-count-format') || el.textContent;
      }
      var formatSample = el.getAttribute('data-count-format') || '';
      var decimalsAttr = el.getAttribute('data-count-decimals');
      var finalText = formatSample || null;
      // Stagger slightly so the hero leads, then stats follow
      var delay = Math.min(i * 60, 360);
      setTimeout(function () {
        countUp(el, raw, {
          duration: el.closest('.balance-hero, .display-5') ? 1400 : 1100,
          formatSample: formatSample,
          decimals: decimalsAttr,
          finalText: finalText,
        });
      }, delay);
    });
  };

  // Legacy [data-count-to] without data-count-up
  document.querySelectorAll('[data-count-to]:not([data-count-up])').forEach(function (el) {
    countUp(el, el.getAttribute('data-count-to'), {
      decimals: el.getAttribute('data-count-decimals'),
    });
  });

  // Primary: count balances up on every refresh
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      runPageCountUps();
    });
  } else {
    runPageCountUps();
  }

  // Button ripple (visual burst)
  document.addEventListener('click', function (e) {
    var btn = e.target.closest('.btn');
    if (!btn || btn.disabled) return;
    var rect = btn.getBoundingClientRect();
    var x = e.clientX - rect.left;
    var y = e.clientY - rect.top;
    btn.style.setProperty('--ripple-x', ((x / rect.width) * 100) + '%');
    btn.style.setProperty('--ripple-y', ((y / rect.height) * 100) + '%');
    var ripple = document.createElement('span');
    ripple.className = 'ci-ripple';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    btn.appendChild(ripple);
    setTimeout(function () { ripple.remove(); }, 650);
  });

  // Password visibility toggle
  window.togglePassword = function (inputId, btn) {
    var input = document.getElementById(inputId) || document.querySelector(inputId);
    if (!input) return;
    var show = input.type === 'password';
    input.type = show ? 'text' : 'password';
    if (btn) {
      var icon = btn.querySelector('i') || btn;
      if (icon.classList) {
        icon.className = show ? 'bi bi-eye-slash' : 'bi bi-eye';
      }
    }
  };

  // Chart defaults
  function chartColors() {
    var muted = getComputedStyle(document.documentElement).getPropertyValue('--ci-text-muted').trim() || '#9CA3AF';
    return {
      muted: muted,
      grid: 'rgba(255,255,255,0.05)',
      purple: '#8B5CF6',
      blue: '#3B82F6',
      green: '#22C55E',
    };
  }

  if (window.Chart) {
    Chart.defaults.color = chartColors().muted;
    Chart.defaults.borderColor = 'rgba(255,255,255,0.05)';
    Chart.defaults.font.family = "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif";
  }

  window.initEarningsChart = function (canvasId, labels, values) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    var ctx = canvas.getContext('2d');
    var gradient = ctx.createLinearGradient(0, 0, 0, 260);
    gradient.addColorStop(0, 'rgba(139, 92, 246, 0.45)');
    gradient.addColorStop(0.6, 'rgba(59, 130, 246, 0.12)');
    gradient.addColorStop(1, 'rgba(59, 130, 246, 0)');
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Earnings',
          data: values,
          borderColor: '#8B5CF6',
          backgroundColor: gradient,
          fill: true,
          tension: 0.45,
          pointRadius: 0,
          pointHoverRadius: 6,
          pointHoverBackgroundColor: '#8B5CF6',
          pointHoverBorderColor: '#fff',
          pointHoverBorderWidth: 2,
          borderWidth: 2.5,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { intersect: false, mode: 'index' },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(17, 24, 39, 0.95)',
            titleColor: '#fff',
            bodyColor: '#C4B5FD',
            padding: 14,
            cornerRadius: 12,
            borderColor: 'rgba(139,92,246,0.35)',
            borderWidth: 1,
            displayColors: false,
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { maxRotation: 0, autoSkipPadding: 12 },
          },
          y: {
            grid: { color: 'rgba(255,255,255,0.04)' },
            border: { display: false },
            ticks: {
              callback: function (v) { return '$' + v; },
              padding: 8,
            },
          },
        },
        animation: { duration: 1200, easing: 'easeOutQuart' },
      },
    });
  };

  window.initPortfolioChart = function (canvasId, labels, values) {
    var canvas = document.getElementById(canvasId);
    if (!canvas || !window.Chart) return;
    new Chart(canvas.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: labels,
        datasets: [{
          data: values,
          backgroundColor: ['#8B5CF6', '#22C55E', '#3B82F6'],
          borderWidth: 0,
          hoverOffset: 8,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '74%',
        plugins: {
          legend: {
            position: 'bottom',
            labels: {
              boxWidth: 10,
              padding: 18,
              usePointStyle: true,
              pointStyle: 'circle',
              font: { size: 12, weight: '500' },
            },
          },
        },
        animation: { animateRotate: true, duration: 1100 },
      },
    });
  };

  window.updateInvestPreview = function (rate, amountEl, resultEl, periods) {
    var amount = parseFloat(amountEl.value) || 0;
    var profit = amount * (parseFloat(rate) / 100) * (parseFloat(periods) || 1);
    if (resultEl) resultEl.textContent = formatMoney(profit, 4);
  };

  // Auto-dismiss bootstrap alerts
  setTimeout(function () {
    document.querySelectorAll('.alert-dismissible').forEach(function (el) {
      try { bootstrap.Alert.getOrCreateInstance(el).close(); } catch (e) { /* ignore */ }
    });
  }, 6500);

  // Toasts
  window.showToast = function (title, message, level) {
    level = level || 'info';
    var container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      container.className = 'toast-container position-fixed top-0 end-0 p-3';
      container.style.zIndex = '1090';
      document.body.appendChild(container);
    }
    var id = 't' + Date.now();
    var colors = {
      success: 'text-profit',
      danger: 'text-loss',
      warning: 'text-warning',
      info: '',
    };
    container.insertAdjacentHTML(
      'beforeend',
      '<div id="' + id + '" class="toast glass-card border-ci show mb-2" role="alert">' +
        '<div class="toast-header bg-transparent border-0">' +
        '<strong class="me-auto ' + (colors[level] || '') + '">' + (title || 'Notification') + '</strong>' +
        '<button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button></div>' +
        '<div class="toast-body small text-soft">' + (message || '') + '</div></div>'
    );
    setTimeout(function () {
      var el = document.getElementById(id);
      if (el) {
        el.style.opacity = '0';
        el.style.transform = 'translateX(20px)';
        el.style.transition = 'all 0.3s ' + EASE;
        setTimeout(function () { el.remove(); }, 300);
      }
    }, 5500);
  };

  // WebSocket notifications
  (function initNotificationSocket() {
    if (!document.body || !document.body.dataset.userAuthenticated) return;
    var proto = location.protocol === 'https:' ? 'wss' : 'ws';
    var ws;
    try {
      ws = new WebSocket(proto + '://' + location.host + '/ws/notifications/');
    } catch (e) { return; }
    ws.onmessage = function (ev) {
      try {
        var data = JSON.parse(ev.data);
        if (data.type === 'notification' && data.data) {
          showToast(data.data.title, data.data.message, data.data.level);
        }
      } catch (e) { /* ignore */ }
    };
    ws.onclose = function () { setTimeout(initNotificationSocket, 5000); };
  })();

  // Stagger entrance for stat grids (skipped if reduced motion)
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    document.querySelectorAll('.stagger-children > *').forEach(function (el, i) {
      el.style.opacity = '0';
      el.style.animation = 'slideUpSoft 0.55s ' + EASE + ' forwards';
      el.style.animationDelay = (i * 0.07) + 's';
    });
  }

  // ── Live display currency / balance API ──────────────────────────────
  function csrfToken() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    var cookie = document.cookie.split(';').map(function (c) { return c.trim(); })
      .find(function (c) { return c.startsWith('csrftoken='); });
    return cookie ? decodeURIComponent(cookie.split('=')[1]) : '';
  }

  function dig(obj, path) {
    return path.split('.').reduce(function (acc, key) {
      return acc == null ? undefined : acc[key];
    }, obj);
  }

  function pulse(el) {
    if (!el) return;
    el.style.transition = 'opacity 0.15s ' + EASE + ', transform 0.2s ' + EASE;
    el.style.opacity = '0.45';
    el.style.transform = 'translateY(2px)';
    requestAnimationFrame(function () {
      setTimeout(function () {
        el.style.opacity = '1';
        el.style.transform = 'none';
      }, 40);
    });
  }

  function applyBalancePayload(data) {
    if (!data || !data.ok) return;
    document.querySelectorAll('[data-balance-root], .balance-hero').forEach(function (root) {
      root.classList.add('is-updating');
      setTimeout(function () { root.classList.remove('is-updating'); }, 480);
    });
    document.querySelectorAll('[data-balance]').forEach(function (el) {
      var path = el.getAttribute('data-balance');
      var val = dig(data, path);
      if (val == null && path === 'symbol') val = data.symbol;
      if (val == null && path === 'currency') val = data.currency;
      if (val == null) return;

      // Numeric balance fields: count up from 0 on currency switch
      if (el.hasAttribute('data-count-up') || /\.formatted$|\.value$|count$|usd_equivalent/.test(path)) {
        var numPath = path.replace(/\.formatted$/, '.value');
        var raw = dig(data, numPath);
        if (raw == null) raw = val;
        var finalText = (typeof val === 'string' && /[a-zA-Z,]/.test(val) === false) || path.indexOf('formatted') !== -1
          ? String(val)
          : null;
        // Prefer formatted string as final text when available
        if (path.indexOf('formatted') !== -1) finalText = String(val);
        el.setAttribute('data-count-to', String(raw));
        if (finalText) el.setAttribute('data-count-format', finalText);
        countUp(el, raw, {
          duration: 900,
          formatSample: finalText || String(val),
          finalText: path.indexOf('formatted') !== -1 ? String(val) : null,
          decimals: el.getAttribute('data-count-decimals'),
        });
      } else {
        el.textContent = String(val);
        pulse(el);
      }
    });
    // Keep every currency select in sync
    document.querySelectorAll('[data-currency-select]').forEach(function (sel) {
      if (data.currency && sel.value !== data.currency) {
        sel.value = data.currency;
      }
    });
  }

  function setBalanceStatus(msg, isError) {
    document.querySelectorAll('[data-balance-status]').forEach(function (el) {
      el.textContent = msg || '';
      el.classList.toggle('text-loss', !!isError);
      el.classList.toggle('text-profit', !isError && !!msg);
    });
  }

  window.fetchBalances = async function (currency) {
    var url = '/api/balances/';
    if (currency) url += '?currency=' + encodeURIComponent(currency);
    var res = await fetch(url, {
      headers: { Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
      credentials: 'same-origin',
    });
    var data = await res.json();
    if (!res.ok || !data.ok) {
      throw new Error((data && data.error) || 'Could not load balances');
    }
    applyBalancePayload(data);
    return data;
  };

  window.setDisplayCurrency = async function (currency) {
    var body = new URLSearchParams();
    body.set('currency', currency);
    body.set('format', 'json');
    var token = csrfToken();
    var res = await fetch('/display-currency/', {
      method: 'POST',
      headers: {
        Accept: 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRFToken': token,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      credentials: 'same-origin',
      body: body.toString(),
    });
    var data = null;
    try { data = await res.json(); } catch (e) { data = null; }
    if (!res.ok || !data || !data.ok) {
      var msg = (data && data.error) || ('Could not update currency (' + res.status + ')');
      throw new Error(msg);
    }
    applyBalancePayload(data);
    if (data.message && window.showToast) {
      showToast('Currency', data.message, 'success');
    }
    return data;
  };

  function fallbackCurrencyFormSubmit(sel) {
    // Full page POST — works even if fetch/API fails (e.g. CSRF, static issues)
    var form = sel && sel.closest('form');
    if (!form) {
      form = document.querySelector('form[data-currency-form]');
    }
    if (!form) {
      window.location.href = '/dashboard/?currency=' + encodeURIComponent(sel.value);
      return;
    }
    // Allow native submit (do not preventDefault)
    if (sel && form.querySelector('[name=currency]') && form.querySelector('[name=currency]') !== sel) {
      form.querySelector('[name=currency]').value = sel.value;
    }
    HTMLFormElement.prototype.submit.call(form);
  }

  (function bindCurrencySelects() {
    document.querySelectorAll('[data-currency-select]').forEach(function (sel) {
      if (sel.dataset.boundCurrency === '1') return;
      sel.dataset.boundCurrency = '1';
      sel.addEventListener('change', function () {
        var currency = sel.value;
        setBalanceStatus('Updating…');
        sel.disabled = true;
        window.setDisplayCurrency(currency)
          .then(function () {
            setBalanceStatus('Updated');
            setTimeout(function () { setBalanceStatus(''); }, 1600);
          })
          .catch(function (err) {
            console.warn('Live currency update failed, falling back to page reload', err);
            setBalanceStatus('Reloading…');
            fallbackCurrencyFormSubmit(sel);
          })
          .finally(function () {
            sel.disabled = false;
          });
      });
    });

    // Prefer live update; fall back to full submit on error
    document.querySelectorAll('form[data-currency-form]').forEach(function (form) {
      form.addEventListener('submit', function (e) {
        var sel = form.querySelector('[data-currency-select], [name=currency]');
        if (!sel || !sel.value) return;
        // If JS live API exists, use it; otherwise allow normal POST
        if (typeof window.setDisplayCurrency !== 'function') return;
        e.preventDefault();
        setBalanceStatus('Updating…');
        window.setDisplayCurrency(sel.value)
          .then(function () {
            setBalanceStatus('Updated');
            setTimeout(function () { setBalanceStatus(''); }, 1600);
          })
          .catch(function () {
            fallbackCurrencyFormSubmit(sel);
          });
      });
    });
  })();

  // ── Motion / interactivity layer ─────────────────────────────────────
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var finePointer = window.matchMedia('(pointer: fine)').matches;

  // Scroll reveal
  (function initReveal() {
    if (reduceMotion || !('IntersectionObserver' in window)) {
      document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
        el.classList.add('is-visible');
      });
      return;
    }
    // Auto-tag common dashboard blocks if not already marked
    document.querySelectorAll(
      '.main-content .glass-card:not(.reveal):not(.balance-hero), ' +
      '.page-content > .row, .page-content > .glass-card'
    ).forEach(function (el, i) {
      if (el.closest('.sidebar') || el.closest('.topbar')) return;
      if (!el.classList.contains('animate-in') && !el.closest('.stagger-children')) {
        el.classList.add('reveal');
        if (i % 3 === 1) el.classList.add('reveal-scale');
      }
    });
    document.querySelectorAll('.table-ci').forEach(function (t) {
      t.classList.add('animate-rows');
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

    document.querySelectorAll('.reveal, .reveal-stagger').forEach(function (el) {
      io.observe(el);
    });
  })();

  // Pointer spotlight on body + glass cards
  (function initPointerGlow() {
    if (reduceMotion || !finePointer) return;
    document.body.classList.add('pointer-glow');
    var raf = null;
    var mx = 50, my = 30;
    window.addEventListener('pointermove', function (e) {
      mx = (e.clientX / window.innerWidth) * 100;
      my = (e.clientY / window.innerHeight) * 100;
      if (raf) return;
      raf = requestAnimationFrame(function () {
        document.body.style.setProperty('--mx', mx + '%');
        document.body.style.setProperty('--my', my + '%');
        raf = null;
      });
    }, { passive: true });

    document.querySelectorAll('.glass-card, .balance-hero, .stat-card').forEach(function (card) {
      card.classList.add('has-spotlight');
      card.addEventListener('pointermove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = ((e.clientX - rect.left) / rect.width) * 100;
        var y = ((e.clientY - rect.top) / rect.height) * 100;
        card.style.setProperty('--spot-x', x + '%');
        card.style.setProperty('--spot-y', y + '%');
      }, { passive: true });
    });
  })();

  // 3D tilt on interactive cards (desktop)
  (function initTilt() {
    if (reduceMotion || !finePointer) return;
    var maxTilt = 7;
    document.querySelectorAll('.stat-card.interactive, .glass-card.interactive, .balance-hero').forEach(function (card) {
      card.addEventListener('pointermove', function (e) {
        var rect = card.getBoundingClientRect();
        var px = (e.clientX - rect.left) / rect.width;
        var py = (e.clientY - rect.top) / rect.height;
        var rx = (0.5 - py) * maxTilt;
        var ry = (px - 0.5) * maxTilt;
        card.classList.add('is-tilting');
        card.style.transform =
          'perspective(900px) rotateX(' + rx.toFixed(2) + 'deg) rotateY(' + ry.toFixed(2) +
          'deg) translateY(-4px) scale(1.01)';
      });
      card.addEventListener('pointerleave', function () {
        card.classList.remove('is-tilting');
        card.style.transform = '';
      });
    });
  })();

  // Magnetic buttons
  (function initMagnetic() {
    if (reduceMotion || !finePointer) return;
    document.querySelectorAll('.btn-ci, .btn-outline-ci, .quick-actions .btn').forEach(function (btn) {
      btn.classList.add('is-magnetic');
      btn.addEventListener('pointermove', function (e) {
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left - rect.width / 2;
        var y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform =
          'translate(' + (x * 0.18).toFixed(1) + 'px, ' + (y * 0.22).toFixed(1) + 'px) scale(1.03)';
      });
      btn.addEventListener('pointerleave', function () {
        btn.style.transform = '';
      });
    });
  })();

  // Topbar scroll shadow
  (function initTopbarScroll() {
    var topbar = document.querySelector('.topbar');
    if (!topbar) return;
    var main = document.querySelector('.main-content, .page-content') || window;
    function onScroll() {
      var y = main === window ? window.scrollY : main.scrollTop;
      topbar.classList.toggle('is-scrolled', y > 8);
    }
    (main === window ? window : main).addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  })();

  // Smooth number morph helper (optional use)
  window.animateNumber = function (el, to, opts) {
    opts = opts || {};
    if (!el) return;
    var duration = opts.duration || 700;
    var from = parseFloat(String(el.textContent).replace(/,/g, '')) || 0;
    var decimals = opts.decimals != null ? opts.decimals : 2;
    var start = performance.now();
    function tick(now) {
      var p = Math.min(1, (now - start) / duration);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = from + (to - from) * eased;
      el.textContent = formatMoney(val, decimals);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  };

  // Subtle parallax on balance hero
  (function initHeroParallax() {
    if (reduceMotion || !finePointer) return;
    var hero = document.querySelector('.balance-hero');
    if (!hero) return;
    window.addEventListener('pointermove', function (e) {
      var cx = (e.clientX / window.innerWidth - 0.5) * 8;
      var cy = (e.clientY / window.innerHeight - 0.5) * 6;
      hero.style.setProperty('--parallax-x', cx.toFixed(2) + 'px');
      hero.style.setProperty('--parallax-y', cy.toFixed(2) + 'px');
    }, { passive: true });
  })();
})();
