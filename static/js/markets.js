
(function () {
  'use strict';

  var widget = null;
  var scriptLoading = null;

  function loadTvScript() {
    if (window.TradingView) return Promise.resolve();
    if (scriptLoading) return scriptLoading;
    scriptLoading = new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = 'https://s3.tradingview.com/tv.js';
      s.async = true;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('TradingView script failed to load')); };
      document.head.appendChild(s);
    });
    return scriptLoading;
  }

  function getConfig() {
    var el = document.getElementById('market-chart-config');
    if (!el) return null;
    try {
      return JSON.parse(el.textContent);
    } catch (e) {
      console.error(e);
      return null;
    }
  }

  function chartHeight() {
    var isMobile = window.innerWidth < 768;
    var chrome = isMobile ? 260 : 200;
    var h = window.innerHeight - chrome;
    return Math.max(isMobile ? 520 : 720, h);
  }

  function sizeChartContainer() {
    var container = document.getElementById('tv_chart_container');
    if (!container) return 0;
    var h = chartHeight();
    container.style.height = h + 'px';
    container.style.minHeight = h + 'px';
    return h;
  }

  function buildWidget(cfg) {
    var container = document.getElementById('tv_chart_container');
    if (!container) return;
    container.innerHTML = '';

    var height = sizeChartContainer();

    widget = new TradingView.widget({
      autosize: true,
      width: '100%',
      height: height,
      symbol: cfg.symbol,
      interval: cfg.interval,
      timezone: 'Etc/UTC',
      theme: cfg.theme || 'dark',
      style: String(cfg.style || '1'),
      locale: 'en',
      toolbar_bg: cfg.theme === 'light' ? '#f8fafc' : '#0A1023',
      enable_publishing: false,
      allow_symbol_change: true,
      hide_top_toolbar: false,
      hide_legend: false,
      hide_side_toolbar: false,
      withdateranges: true,
      details: false,
      hotlist: false,
      calendar: false,
      studies: [
        'STD;SMA',
        'STD;RSI',
      ],
      container_id: 'tv_chart_container',
      overrides: {
        'paneProperties.background': cfg.theme === 'light' ? '#ffffff' : '#0A1023',
        'paneProperties.backgroundType': 'solid',
        'mainSeriesProperties.candleStyle.upColor': '#22C55E',
        'mainSeriesProperties.candleStyle.downColor': '#EF4444',
        'mainSeriesProperties.candleStyle.borderUpColor': '#22C55E',
        'mainSeriesProperties.candleStyle.borderDownColor': '#EF4444',
        'mainSeriesProperties.candleStyle.wickUpColor': '#22C55E',
        'mainSeriesProperties.candleStyle.wickDownColor': '#EF4444',
      },
    });
  }

  window.initMarketChart = function () {
    var cfg = getConfig();
    if (!cfg) return;
    var status = document.getElementById('chart-load-status');
    if (status) status.textContent = 'Loading chart…';

    loadTvScript()
      .then(function () {
        buildWidget(cfg);
        if (status) status.textContent = '';
      })
      .catch(function (err) {
        console.error(err);
        if (status) {
          status.innerHTML =
            '<span class="text-danger">Chart could not load. Check your network or disable ad blockers blocking TradingView.</span>';
        }
      });
  };

  window.applyMarketFilters = function () {
    var symbol = document.getElementById('pair-select');
    var style = document.getElementById('style-select');
    var interval = document.getElementById('interval-select');
    var params = new URLSearchParams();
    if (symbol && symbol.value) params.set('symbol', symbol.value);
    if (style && style.value) params.set('style', style.value);
    if (interval && interval.value) params.set('interval', interval.value);
    window.location.href = '/markets/chart/?' + params.toString();
  };
  window.initMarketTickers = function () {
    var nodes = document.querySelectorAll('[data-tv-ticker]');
    if (!nodes.length) return;
    loadTvScript().then(function () {
      nodes.forEach(function (node) {
        var symbol = node.getAttribute('data-tv-ticker');
        if (!symbol) return;
        var h = parseInt(node.getAttribute('data-height') || '360', 10);
        node.style.height = h + 'px';
        node.innerHTML = '';
        var s = document.createElement('script');
        s.type = 'text/javascript';
        s.src = 'https://s3.tradingview.com/external-embedding/embed-widget-symbol-overview.js';
        s.async = true;
        s.innerHTML = JSON.stringify({
          symbols: [[symbol.split(':').pop() || symbol, symbol]],
          chartOnly: false,
          width: '100%',
          height: h,
          locale: 'en',
          colorTheme: (document.documentElement.getAttribute('data-theme') === 'light') ? 'light' : 'dark',
          autosize: true,
          showVolume: true,
          showMA: true,
          hideDateRanges: false,
          hideMarketStatus: false,
          hideSymbolLogo: false,
          scalePosition: 'right',
          scaleMode: 'Normal',
          fontFamily: 'Plus Jakarta Sans, sans-serif',
          fontSize: '12',
          noTimeScale: false,
          valuesTracking: '1',
          changeMode: 'price-and-percent',
          chartType: 'candlesticks',
          maLineColor: '#8B5CF6',
          maLineWidth: 1,
          maLength: 20,
          backgroundColor: 'rgba(10, 16, 35, 0)',
          lineWidth: 2,
          lineType: 0,
          dateRanges: ['1d|1', '1m|30', '3m|60', '12m|1D', '60m|1W', 'all|1M'],
        });
        node.appendChild(s);
      });
    }).catch(function () {  });
  };
  window.filterMarketPairs = function (q) {
    q = (q || '').toLowerCase().trim();
    document.querySelectorAll('[data-pair-card]').forEach(function (card) {
      var hay = (card.getAttribute('data-pair-search') || '').toLowerCase();
      card.style.display = !q || hay.indexOf(q) !== -1 ? '' : 'none';
    });
  };

  var resizeTimer = null;
  window.addEventListener('resize', function () {
    if (!document.getElementById('tv_chart_container')) return;
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(function () {
      initMarketChart();
    }, 400);
  });

  document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('tv_chart_container')) {
      initMarketChart();
    }
    if (document.querySelector('[data-tv-ticker]')) {
      initMarketTickers();
    }
  });
})();
