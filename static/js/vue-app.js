/**
 * CryptoInvest — Vue 3 progressive UI layer
 * Cleaner interactions, toasts, progress, scroll, reveals.
 * Does NOT replace Django templates/forms — enhances them.
 */
(function () {
  'use strict';

  if (typeof Vue === 'undefined') {
    console.warn('[VueUI] Vue not loaded — progressive layer skipped');
    return;
  }

  var createApp = Vue.createApp;
  var ref = Vue.ref;
  var computed = Vue.computed;
  var onMounted = Vue.onMounted;
  var onBeforeUnmount = Vue.onBeforeUnmount;
  var nextTick = Vue.nextTick;
  var watch = Vue.watch;

  function prefersReducedMotion() {
    return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  }

  function csrfToken() {
    var el = document.querySelector('[name=csrfmiddlewaretoken]');
    if (el && el.value) return el.value;
    var m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : '';
  }

  // ---------------------------------------------------------------------------
  // Public API used by legacy code + templates
  // ---------------------------------------------------------------------------
  var toastApi = {
    push: function () {},
  };
  var progressApi = {
    start: function () {},
    stop: function () {},
  };

  window.VueUI = {
    toast: function (title, message, level) {
      toastApi.push({
        title: title || 'Notification',
        message: message || '',
        level: level || 'info',
      });
    },
    startProgress: function () { progressApi.start(); },
    stopProgress: function () { progressApi.stop(); },
    version: '1.0.0',
  };

  // Bridge legacy showToast → Vue toasts when available
  var prevShowToast = window.showToast;
  window.showToast = function (title, message, level) {
    if (toastApi.push && document.getElementById('vue-toast-root')) {
      window.VueUI.toast(title, message, level);
      return;
    }
    if (typeof prevShowToast === 'function') prevShowToast(title, message, level);
  };

  // ---------------------------------------------------------------------------
  // Toast app
  // ---------------------------------------------------------------------------
  function mountToasts() {
    var el = document.getElementById('vue-toast-root');
    if (!el) return;

    var app = createApp({
      setup: function () {
        var toasts = ref([]);
        var idSeq = 1;

        function push(payload) {
          var id = idSeq++;
          var item = {
            id: id,
            title: payload.title || 'Notification',
            message: payload.message || '',
            level: payload.level || 'info',
            leaving: false,
          };
          toasts.value = [item].concat(toasts.value).slice(0, 5);
          setTimeout(function () { dismiss(id); }, 5200);
        }

        function dismiss(id) {
          var t = toasts.value.find(function (x) { return x.id === id; });
          if (!t) return;
          t.leaving = true;
          setTimeout(function () {
            toasts.value = toasts.value.filter(function (x) { return x.id !== id; });
          }, 260);
        }

        function iconFor(level) {
          if (level === 'success') return 'bi-check-circle-fill';
          if (level === 'danger') return 'bi-exclamation-triangle-fill';
          if (level === 'warning') return 'bi-exclamation-circle-fill';
          return 'bi-info-circle-fill';
        }

        toastApi.push = push;

        // Convert Django messages already on page into toasts (once)
        onMounted(function () {
          document.querySelectorAll('.page-content > .mb-3 > .alert, .page-content > .alert').forEach(function (alert, i) {
            if (alert.dataset.vueToasted) return;
            alert.dataset.vueToasted = '1';
            var level = 'info';
            if (alert.classList.contains('alert-success')) level = 'success';
            else if (alert.classList.contains('alert-danger')) level = 'danger';
            else if (alert.classList.contains('alert-warning')) level = 'warning';
            var text = (alert.textContent || '').replace(/\s+/g, ' ').trim();
            if (!text) return;
            setTimeout(function () {
              push({ title: level === 'danger' ? 'Error' : 'Notice', message: text.slice(0, 180), level: level });
            }, 80 + i * 60);
          });
        });

        return { toasts: toasts, dismiss: dismiss, iconFor: iconFor };
      },
      template:
        '<div class="vue-toasts" aria-live="polite" aria-relevant="additions">' +
          '<div v-for="t in toasts" :key="t.id" class="vue-toast" :class="[t.level, { \'is-leaving\': t.leaving }]">' +
            '<div class="icon"><i class="bi" :class="iconFor(t.level)"></i></div>' +
            '<div class="body">' +
              '<div class="title">{{ t.title }}</div>' +
              '<div class="msg" v-if="t.message">{{ t.message }}</div>' +
            '</div>' +
            '<button type="button" class="x" @click="dismiss(t.id)" aria-label="Dismiss">&times;</button>' +
          '</div>' +
        '</div>',
    });
    app.mount(el);
  }

  // ---------------------------------------------------------------------------
  // Progress + scroll-to-top + theme switcher shell
  // ---------------------------------------------------------------------------
  function mountChrome() {
    var el = document.getElementById('vue-chrome-root');
    if (!el) return;

    var app = createApp({
      setup: function () {
        var loading = ref(false);
        var showTop = ref(false);
        var colorMode = ref(document.documentElement.getAttribute('data-theme') || 'dark');
        var uiTheme = ref(document.documentElement.getAttribute('data-ui-theme') || 'classic');
        var timer = null;

        function start() {
          loading.value = true;
          clearTimeout(timer);
          timer = setTimeout(function () { loading.value = false; }, 8000);
        }
        function stop() {
          clearTimeout(timer);
          // slight delay so bar is visible on fast navigations
          setTimeout(function () { loading.value = false; }, 180);
        }
        progressApi.start = start;
        progressApi.stop = stop;

        function onScroll() {
          var y = window.scrollY || document.documentElement.scrollTop || 0;
          showTop.value = y > 420;
        }

        function scrollTop() {
          window.scrollTo({ top: 0, behavior: prefersReducedMotion() ? 'auto' : 'smooth' });
        }

        function setColor(mode) {
          colorMode.value = mode;
          if (typeof window.setTheme === 'function') window.setTheme(mode);
          else document.documentElement.setAttribute('data-theme', mode);
        }

        function setUi(mode) {
          uiTheme.value = mode;
          if (typeof window.setUiTheme === 'function') window.setUiTheme(mode);
          else document.documentElement.setAttribute('data-ui-theme', mode);
        }

        function onNavClick(e) {
          var a = e.target.closest && e.target.closest('a[href]');
          if (!a) return;
          var href = a.getAttribute('href') || '';
          if (!href || href.charAt(0) === '#' || href.indexOf('javascript:') === 0) return;
          if (a.target === '_blank' || a.hasAttribute('download')) return;
          if (a.origin && a.origin !== window.location.origin) return;
          // same-page anchors / hash only
          if (href.indexOf('#') === 0) return;
          start();
        }

        var mo = null;
        onMounted(function () {
          window.addEventListener('scroll', onScroll, { passive: true });
          onScroll();
          document.addEventListener('click', onNavClick, true);
          window.addEventListener('pageshow', stop);
          mo = new MutationObserver(function () {
            colorMode.value = document.documentElement.getAttribute('data-theme') || 'dark';
            uiTheme.value = document.documentElement.getAttribute('data-ui-theme') || 'classic';
          });
          mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme', 'data-ui-theme'] });
        });
        onBeforeUnmount(function () {
          window.removeEventListener('scroll', onScroll);
          document.removeEventListener('click', onNavClick, true);
          window.removeEventListener('pageshow', stop);
          if (mo) mo.disconnect();
        });

        return {
          loading: loading,
          showTop: showTop,
          scrollTop: scrollTop,
          colorMode: colorMode,
          uiTheme: uiTheme,
          setColor: setColor,
          setUi: setUi,
        };
      },
      template:
        '<div>' +
          '<div class="vue-progress" :class="{ \'is-active\': loading }" aria-hidden="true"><div class="bar"></div></div>' +
          '<button type="button" class="vue-scroll-top" :class="{ \'is-visible\': showTop }" @click="scrollTop" aria-label="Back to top">' +
            '<i class="bi bi-arrow-up"></i>' +
          '</button>' +
        '</div>',
    });
    app.mount(el);
  }

  // ---------------------------------------------------------------------------
  // Compact theme switcher (optional mount in topbar)
  // ---------------------------------------------------------------------------
  function mountThemeSwitch() {
    var el = document.getElementById('vue-theme-switch');
    if (!el) return;

    createApp({
      setup: function () {
        var mode = ref(document.documentElement.getAttribute('data-theme') || 'dark');
        function setMode(m) {
          mode.value = m;
          if (typeof window.setTheme === 'function') window.setTheme(m);
        }
        onMounted(function () {
          var mo = new MutationObserver(function () {
            mode.value = document.documentElement.getAttribute('data-theme') || 'dark';
          });
          mo.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
        });
        return { mode: mode, setMode: setMode };
      },
      template:
        '<div class="vue-theme-switch" role="group" aria-label="Color mode">' +
          '<button type="button" :class="{ \'is-active\': mode === \'dark\' }" @click="setMode(\'dark\')" title="Dark" aria-label="Dark mode">' +
            '<i class="bi bi-moon-stars-fill"></i>' +
          '</button>' +
          '<button type="button" :class="{ \'is-active\': mode === \'light\' }" @click="setMode(\'light\')" title="Light" aria-label="Light mode">' +
            '<i class="bi bi-sun-fill"></i>' +
          '</button>' +
        '</div>',
    }).mount(el);
  }

  // ---------------------------------------------------------------------------
  // DOM polish (no full-page Vue rewrite)
  // ---------------------------------------------------------------------------
  function enhanceDom() {
    var page = document.querySelector('.page-content, .auth-layout, .hero');
    if (page) {
      page.classList.add('vue-ui-ready');
      if (!prefersReducedMotion()) page.classList.add('vue-page-enter');
    }

    // Smooth reveal for main cards
    if (!prefersReducedMotion() && 'IntersectionObserver' in window) {
      var nodes = document.querySelectorAll(
        '.page-content > .glass-card, .page-content > .row, .page-content > .mb-3, .page-content > .mb-4, .stat-card, .plan-card, .balance-hero'
      );
      var io = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-in');
            io.unobserve(entry.target);
          }
        });
      }, { threshold: 0.08, rootMargin: '0px 0px -24px 0px' });

      nodes.forEach(function (el, i) {
        if (el.classList.contains('reveal') || el.classList.contains('vue-reveal')) return;
        el.classList.add('vue-reveal');
        el.style.transitionDelay = Math.min(i * 0.04, 0.28) + 's';
        io.observe(el);
      });
    } else {
      document.querySelectorAll('.vue-reveal').forEach(function (el) {
        el.classList.add('is-in');
      });
    }

    // Card press feedback
    document.querySelectorAll('.stat-card, .plan-card, .glass-card.interactive').forEach(function (el) {
      el.classList.add('vue-card-press');
    });

    // Forms: mark empty labels for better autofill UX
    document.querySelectorAll('form').forEach(function (form) {
      form.addEventListener('submit', function () {
        if (progressApi.start) progressApi.start();
      });
    });

    // Improve table empty readability
    document.querySelectorAll('.table-ci').forEach(function (table) {
      table.classList.add('animate-rows');
    });

    // Keyboard: Escape closes sidebar
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        var sb = document.getElementById('sidebar');
        var ov = document.getElementById('sidebar-overlay');
        if (sb && sb.classList.contains('show')) {
          sb.classList.remove('show');
          if (ov) ov.classList.remove('show');
        }
      }
    });
  }

  // ---------------------------------------------------------------------------
  // Animated counters (works with existing data-count-up)
  // ---------------------------------------------------------------------------
  function enhanceCounters() {
    if (typeof window.runPageCountUps === 'function') {
      // already handled by app.js — just ensure delay feels smoother
      return;
    }
  }

  // ---------------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------------
  function boot() {
    mountToasts();
    mountChrome();
    mountThemeSwitch();
    enhanceDom();
    enhanceCounters();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
