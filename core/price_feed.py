"""
Free live price feeds (no API key required for basic use).

Crypto: CoinGecko public API (fallback: Binance public ticker)
Fiat:   open.er-api.com (USD base) for EUR, GBP, UGX, etc.

Prices are stored on Cryptocurrency.usd_price and CurrencyRate.rate_to_usd.
"""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation
from typing import Any

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('core.price_feed')

# Cache key / freshness
CACHE_KEY = 'price_feed:last_ok'
CACHE_TTL_SECONDS = 120  # don't hit free APIs more often than this
STALE_SECONDS = 300  # auto-refresh if older than 5 minutes

# Map platform symbols → CoinGecko ids
COINGECKO_IDS = {
    'BTC': 'bitcoin',
    'ETH': 'ethereum',
    'BNB': 'binancecoin',
    'LTC': 'litecoin',
    'USDT_TRC20': 'tether',
    'USDT_ERC20': 'tether',
    'USDT_BEP20': 'tether',
}

# Binance fallback symbols
BINANCE_SYMBOLS = {
    'BTC': 'BTCUSDT',
    'ETH': 'ETHUSDT',
    'BNB': 'BNBUSDT',
    'LTC': 'LTCUSDT',
    # USDT ≈ 1 USD
}

# Fiat codes we update (rate_to_usd = USD value of 1 unit of that currency)
FIAT_CODES = ('EUR', 'GBP', 'UGX', 'USD')


def _http_get_json(url: str, timeout: int = 12) -> Any:
    req = urllib.request.Request(
        url,
        headers={
            'User-Agent': 'CryptoInvestPriceFeed/1.0',
            'Accept': 'application/json',
        },
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    return json.loads(raw)


def _d(val) -> Decimal | None:
    try:
        d = Decimal(str(val))
        if d > 0:
            return d
    except (InvalidOperation, TypeError, ValueError):
        pass
    return None


def fetch_crypto_prices_coingecko(symbols: list[str] | None = None) -> dict[str, Decimal]:
    """Return {BTC: Decimal(...), ETH: ...} from CoinGecko."""
    symbols = symbols or list(COINGECKO_IDS.keys())
    ids = []
    id_to_symbols: dict[str, list[str]] = {}
    for sym in symbols:
        gid = COINGECKO_IDS.get(sym.upper())
        if not gid:
            continue
        if gid not in id_to_symbols:
            ids.append(gid)
            id_to_symbols[gid] = []
        id_to_symbols[gid].append(sym.upper())

    if not ids:
        return {}

    url = (
        'https://api.coingecko.com/api/v3/simple/price'
        f'?ids={",".join(ids)}&vs_currencies=usd'
    )
    data = _http_get_json(url)
    out: dict[str, Decimal] = {}
    for gid, payload in (data or {}).items():
        price = _d((payload or {}).get('usd'))
        if not price:
            continue
        for sym in id_to_symbols.get(gid, []):
            out[sym] = price
    return out


def fetch_crypto_prices_binance(symbols: list[str] | None = None) -> dict[str, Decimal]:
    """Fallback: Binance public tickers."""
    symbols = symbols or list(BINANCE_SYMBOLS.keys())
    out: dict[str, Decimal] = {}
    for sym in symbols:
        pair = BINANCE_SYMBOLS.get(sym.upper())
        if not pair:
            if sym.upper().startswith('USDT'):
                out[sym.upper()] = Decimal('1')
            continue
        try:
            data = _http_get_json(
                f'https://api.binance.com/api/v3/ticker/price?symbol={pair}',
                timeout=10,
            )
            price = _d(data.get('price'))
            if price:
                out[sym.upper()] = price
        except Exception as exc:
            logger.warning('Binance price failed for %s: %s', sym, exc)
    for sym in symbols:
        if sym.upper().startswith('USDT') and sym.upper() not in out:
            out[sym.upper()] = Decimal('1')
    return out


def fetch_fiat_rates_usd() -> dict[str, Decimal]:
    """
    Return rate_to_usd for fiat codes.
    API returns how many units of currency per 1 USD.
    rate_to_usd (USD per 1 unit) = 1 / units_per_usd.
    """
    # Free, no key: https://open.er-api.com/v6/latest/USD
    data = _http_get_json('https://open.er-api.com/v6/latest/USD', timeout=12)
    rates = (data or {}).get('rates') or {}
    out: dict[str, Decimal] = {'USD': Decimal('1')}
    for code in FIAT_CODES:
        if code == 'USD':
            continue
        units_per_usd = _d(rates.get(code))
        if not units_per_usd:
            continue
        # 1 CODE = 1/units_per_usd USD
        out[code] = (Decimal('1') / units_per_usd).quantize(Decimal('0.000000000001'))
    return out


def apply_crypto_prices(prices: dict[str, Decimal]) -> int:
    from wallets.models import Cryptocurrency

    updated = 0
    for sym, price in prices.items():
        n = Cryptocurrency.objects.filter(symbol__iexact=sym).update(usd_price=price)
        updated += n
    return updated


def apply_fiat_rates(rates: dict[str, Decimal]) -> int:
    from core.models import CurrencyRate

    names = {
        'USD': 'US Dollar',
        'EUR': 'Euro',
        'GBP': 'British Pound',
        'UGX': 'Ugandan Shilling',
    }
    updated = 0
    for code, rate in rates.items():
        obj, created = CurrencyRate.objects.update_or_create(
            code=code,
            defaults={
                'name': names.get(code, code),
                'rate_to_usd': rate,
                'symbol': code,
                'is_active': True,
            },
        )
        updated += 1
        if not created:
            CurrencyRate.objects.filter(pk=obj.pk).update(
                rate_to_usd=rate, is_active=True,
            )
    return updated


def refresh_all_prices(force: bool = False) -> dict:
    """
    Fetch and store live prices. Rate-limited via cache unless force=True.
    Returns summary dict.
    """
    if not force:
        last = cache.get(CACHE_KEY)
        if last:
            return {'ok': True, 'skipped': True, 'reason': 'fresh_cache', **last}

    result = {
        'ok': False,
        'crypto_source': None,
        'crypto_updated': 0,
        'fiat_updated': 0,
        'prices': {},
        'fiat': {},
        'errors': [],
        'updated_at': timezone.now().isoformat(),
    }

    crypto_prices: dict[str, Decimal] = {}
    try:
        crypto_prices = fetch_crypto_prices_coingecko()
        if crypto_prices:
            result['crypto_source'] = 'coingecko'
    except Exception as exc:
        result['errors'].append(f'coingecko: {exc}')
        logger.warning('CoinGecko failed: %s', exc)

    if not crypto_prices:
        try:
            crypto_prices = fetch_crypto_prices_binance()
            if crypto_prices:
                result['crypto_source'] = 'binance'
        except Exception as exc:
            result['errors'].append(f'binance: {exc}')
            logger.warning('Binance failed: %s', exc)

    if crypto_prices:
        result['crypto_updated'] = apply_crypto_prices(crypto_prices)
        result['prices'] = {k: str(v) for k, v in crypto_prices.items()}

    try:
        fiat = fetch_fiat_rates_usd()
        if fiat:
            result['fiat_updated'] = apply_fiat_rates(fiat)
            result['fiat'] = {k: str(v) for k, v in fiat.items()}
    except Exception as exc:
        result['errors'].append(f'fiat: {exc}')
        logger.warning('Fiat rates failed: %s', exc)

    result['ok'] = bool(result['crypto_updated'] or result['fiat_updated'])
    cache.set(CACHE_KEY, {
        'ok': result['ok'],
        'crypto_source': result['crypto_source'],
        'prices': result['prices'],
        'fiat': result['fiat'],
        'updated_at': result['updated_at'],
        'crypto_updated': result['crypto_updated'],
        'fiat_updated': result['fiat_updated'],
    }, CACHE_TTL_SECONDS)

    # Also store a simple ticker for the dashboard
    cache.set('price_feed:ticker', {
        'prices': result['prices'],
        'fiat': result['fiat'],
        'source': result['crypto_source'],
        'updated_at': result['updated_at'],
    }, 600)

    return result


def ensure_fresh_prices(max_age_seconds: int = STALE_SECONDS) -> dict | None:
    """
    Refresh if cache is missing/stale. Safe to call from request path
    (skips if recently updated).
    """
    last = cache.get(CACHE_KEY)
    if last and last.get('ok'):
        return last
    try:
        return refresh_all_prices(force=False)
    except Exception as exc:
        logger.warning('ensure_fresh_prices failed: %s', exc)
        return None


def get_ticker_snapshot() -> dict:
    """For dashboard / API — does a soft refresh if needed."""
    ensure_fresh_prices()
    tick = cache.get('price_feed:ticker') or {}
    if not tick.get('prices'):
        # DB fallback
        from wallets.models import Cryptocurrency
        prices = {
            c.symbol: str(c.usd_price)
            for c in Cryptocurrency.objects.filter(is_active=True).only('symbol', 'usd_price')
        }
        tick = {'prices': prices, 'source': 'database', 'updated_at': None}
    return tick
