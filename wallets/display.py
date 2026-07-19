"""Display currency conversion — crypto + fiat (USD, UGX, …)."""
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP

from core.utils import format_money, quantize_amount
from transactions.models import Deposit
from wallets.models import Cryptocurrency, Wallet

# Built-in fiat so UGX/USD always appear even before seed.
# rate_to_usd = USD value of 1 unit (same as CurrencyRate model).
# 1 USD ≈ 3,700 UGX → 1 UGX ≈ 1/3700 USD
FIAT_DEFAULTS = {
    'USD': {
        'name': 'US Dollar',
        'label': 'USD (US Dollar)',
        'rate_to_usd': Decimal('1'),
        'symbol': 'USD',
        'decimals': 2,
    },
    'UGX': {
        'name': 'Ugandan Shilling',
        'label': 'UGX (Ugandan Shilling)',
        'rate_to_usd': Decimal('1') / Decimal('3700'),
        'symbol': 'UGX',
        'decimals': 0,
    },
}


def _fiat_rate(code: str):
    """
    Return (rate_to_usd Decimal, meta dict) for a fiat code, or None.
    Prefers active CurrencyRate rows; falls back to FIAT_DEFAULTS.
    """
    code = (code or '').strip().upper()
    if not code:
        return None
    try:
        from core.models import CurrencyRate
        row = CurrencyRate.objects.filter(code__iexact=code, is_active=True).first()
        if row and row.rate_to_usd and Decimal(str(row.rate_to_usd)) > 0:
            meta = {
                'name': row.name or code,
                'label': f'{code} ({row.name})' if row.name else code,
                'rate_to_usd': Decimal(str(row.rate_to_usd)),
                'symbol': (row.symbol or code).strip() or code,
                'decimals': 0 if code == 'UGX' else 2,
            }
            return meta['rate_to_usd'], meta
    except Exception:
        pass
    if code in FIAT_DEFAULTS:
        meta = dict(FIAT_DEFAULTS[code])
        return meta['rate_to_usd'], meta
    return None


def is_fiat_code(code: str) -> bool:
    code = (code or '').strip().upper()
    if not code:
        return False
    if code in FIAT_DEFAULTS:
        return True
    try:
        from core.models import CurrencyRate
        return CurrencyRate.objects.filter(code__iexact=code, is_active=True).exists()
    except Exception:
        return False


def _normalize_display_code(code: str) -> str | None:
    """
    Return a canonical display currency code if recognized, else None.
    Never invent a different currency — callers decide fallbacks.
    """
    code = (code or '').strip()
    if not code:
        return None
    upper = code.upper()
    if upper == 'USD':
        return 'USD'
    if is_fiat_code(upper):
        if _fiat_rate(upper):
            try:
                from core.models import CurrencyRate
                row = CurrencyRate.objects.filter(code__iexact=upper, is_active=True).first()
                if row:
                    return row.code
            except Exception:
                pass
            return upper
    crypto = Cryptocurrency.objects.filter(symbol__iexact=code, is_active=True).first()
    if crypto:
        return crypto.symbol
    # Inactive crypto still stored as preference — keep symbol so it stays permanent
    crypto_any = Cryptocurrency.objects.filter(symbol__iexact=code).first()
    if crypto_any:
        return crypto_any.symbol
    return None


def get_default_display_code(user, request=None) -> str:
    """
    Resolve which currency to show balances / investment limits in.

    Permanent order (never silently discard an explicit choice):
    1. User.preferred_currency (DB — primary permanent store)
    2. Session `display_currency` (same browser session)
    3. Cookie `display_currency` (survives browser restarts)
    4. Last approved deposit crypto (only if user never chose)
    5. First active crypto / USD
    """
    candidates = []

    pref = (getattr(user, 'preferred_currency', None) or '').strip()
    if pref:
        candidates.append(pref)

    if request is not None:
        try:
            sess = (request.session.get('display_currency') or '').strip()
            if sess:
                candidates.append(sess)
        except Exception:
            pass
        cookie = (request.COOKIES.get('display_currency') or '').strip()
        if cookie:
            candidates.append(cookie)

    for raw in candidates:
        resolved = _normalize_display_code(raw)
        if resolved:
            return resolved

    # No permanent preference — derive a sensible default (do not treat as user choice yet)
    last = (
        Deposit.objects.filter(user=user, status=Deposit.Status.APPROVED)
        .select_related('cryptocurrency')
        .order_by('-reviewed_at', '-created_at')
        .first()
    )
    if last and last.cryptocurrency_id:
        return last.cryptocurrency.symbol
    first = Cryptocurrency.objects.filter(is_active=True).order_by('sort_order').first()
    if first:
        return first.symbol
    return 'USD'


def persist_display_currency(user, code: str, request=None, response=None) -> str:
    """
    Permanently save display currency on the user, session, and cookie.
    Returns the normalized code actually stored.
    """
    from django.contrib.auth import get_user_model

    resolved = _normalize_display_code(code) or resolve_currency_code(user, code)
    if not resolved:
        raise ValueError('Invalid display currency')

    User = get_user_model()
    User.objects.filter(pk=user.pk).update(preferred_currency=resolved)
    user.preferred_currency = resolved

    if request is not None:
        try:
            request.session['display_currency'] = resolved
            request.session.modified = True
        except Exception:
            pass

    if response is not None:
        response.set_cookie(
            'display_currency',
            resolved,
            max_age=60 * 60 * 24 * 400,  # ~13 months
            samesite='Lax',
            httponly=False,
            path='/',
        )
    return resolved


def get_display_currencies_for_user(user):
    """
    Crypto options (deposited first), then fiat (UGX, USD, and other CurrencyRate).
    """
    options = []
    seen = set()
    deposited_ids = list(
        Deposit.objects.filter(user=user, status=Deposit.Status.APPROVED)
        .values_list('cryptocurrency_id', flat=True)
        .distinct()
    )
    deposited = list(
        Cryptocurrency.objects.filter(id__in=deposited_ids, is_active=True).order_by('sort_order', 'symbol')
    ) if deposited_ids else []
    others = list(
        Cryptocurrency.objects.filter(is_active=True)
        .exclude(id__in=deposited_ids or [])
        .order_by('sort_order', 'symbol')
    )

    for c in deposited + others:
        if c.symbol in seen:
            continue
        seen.add(c.symbol)
        options.append({
            'code': c.symbol,
            'label': f'{c.name} ({c.symbol})',
            'symbol': c.symbol,
            'usd_price': c.usd_price or Decimal('1'),
            'network': getattr(c, 'network', ''),
            'kind': 'crypto',
        })

    # Fiat: always include UGX + USD, plus any other active CurrencyRate rows
    fiat_codes = []
    try:
        from core.models import CurrencyRate
        for row in CurrencyRate.objects.filter(is_active=True).order_by('code'):
            fiat_codes.append(row.code.upper())
    except Exception:
        pass
    for extra in ('UGX', 'USD'):
        if extra not in fiat_codes:
            fiat_codes.append(extra)

    # Preferred order: UGX near top of fiat, USD last
    def fiat_sort_key(c):
        if c == 'UGX':
            return (0, c)
        if c == 'USD':
            return (2, c)
        return (1, c)

    for fcode in sorted(set(fiat_codes), key=fiat_sort_key):
        if fcode in seen:
            continue
        rate_info = _fiat_rate(fcode)
        if not rate_info:
            continue
        rate, meta = rate_info
        seen.add(fcode)
        options.append({
            'code': fcode,
            'label': meta.get('label') or fcode,
            'symbol': meta.get('symbol') or fcode,
            'usd_price': rate,
            'kind': 'fiat',
        })

    return options


def resolve_display_crypto(code: str):
    if not code or is_fiat_code(code):
        return None
    return Cryptocurrency.objects.filter(symbol__iexact=code, is_active=True).first()


def convert_from_usd(amount_usd, currency_code: str) -> Decimal:
    """Convert platform USD-equivalent balance into display units (crypto or fiat)."""
    amount = Decimal(str(amount_usd or 0))
    code = (currency_code or 'USD').strip()
    if not code or code.upper() == 'USD':
        return quantize_amount(amount, 2)

    # Fiat (UGX, EUR, …): units = USD / rate_to_usd
    fiat = _fiat_rate(code)
    if fiat:
        rate, meta = fiat
        if rate <= 0:
            return quantize_amount(amount, 2)
        units = amount / rate
        places = int(meta.get('decimals', 2))
        return quantize_amount(units, places)

    crypto = resolve_display_crypto(code)
    if not crypto or not crypto.usd_price or crypto.usd_price <= 0:
        return quantize_amount(amount, 2)
    coins = amount / Decimal(str(crypto.usd_price))
    places = min(8, crypto.decimals or 8)
    return quantize_amount(coins, places)


def convert_to_usd(amount, currency_code: str) -> Decimal:
    """
    Convert display/crypto units → platform USD-equivalent.
    Uses higher precision (8 dp) so UGX/crypto rounds accurately into the wallet.
    """
    amount = Decimal(str(amount or 0))
    code = (currency_code or 'USD').strip()
    if not code or code.upper() == 'USD':
        return quantize_amount(amount, 8)

    fiat = _fiat_rate(code)
    if fiat:
        rate, _meta = fiat
        if rate <= 0:
            return quantize_amount(amount, 8)
        return quantize_amount(amount * rate, 8)

    crypto = resolve_display_crypto(code)
    if not crypto or not crypto.usd_price:
        return quantize_amount(amount, 8)
    return quantize_amount(amount * Decimal(str(crypto.usd_price)), 8)


def crypto_units_to_usd(units, crypto) -> Decimal:
    """Convert on-chain crypto units → platform USD using live usd_price."""
    units = Decimal(str(units or 0))
    price = Decimal(str(getattr(crypto, 'usd_price', None) or 0))
    if price <= 0:
        price = Decimal('1')
    return quantize_amount(units * price, 8)


def usd_to_crypto_units(amount_usd, crypto) -> Decimal:
    """Convert platform USD → crypto units using live usd_price."""
    amount_usd = Decimal(str(amount_usd or 0))
    price = Decimal(str(getattr(crypto, 'usd_price', None) or 0))
    if price <= 0:
        raise ValueError(f'No live USD price for {getattr(crypto, "symbol", "crypto")}. Try again shortly.')
    places = min(8, int(getattr(crypto, 'decimals', 8) or 8))
    return quantize_amount(amount_usd / price, places)


def _format_amount(amount_usd, code: str) -> dict:
    """Format a USD-equivalent amount into a display-currency payload."""
    code = (code or 'USD').strip() or 'USD'
    upper = code.upper()
    if upper == 'USD':
        code = 'USD'
        upper = 'USD'

    value = convert_from_usd(amount_usd, code)
    crypto = resolve_display_crypto(code)
    fiat = _fiat_rate(code) if not crypto else None

    if crypto:
        symbol = crypto.symbol
        places = min(8, getattr(crypto, 'decimals', 8) or 8)
        usd_price = float(crypto.usd_price) if crypto.usd_price else 1.0
        code_out = crypto.symbol
    elif fiat:
        _rate, meta = fiat
        symbol = meta.get('symbol') or upper
        places = int(meta.get('decimals', 2))
        usd_price = float(_rate)
        code_out = upper
    else:
        symbol = 'USD'
        places = 2
        usd_price = 1.0
        code_out = 'USD'

    q = Decimal('1').scaleb(-places) if places > 0 else Decimal('1')
    rounding = ROUND_HALF_UP if places == 0 else ROUND_DOWN
    value = value.quantize(q, rounding=rounding)
    # Always use thousands separators (commas) in UI
    if places == 0:
        formatted = format_money(value, 0)
    elif places > 2:
        formatted = format_money(value, places, strip_trailing_zeros=True)
    else:
        formatted = format_money(value, 2)

    usd_eq = quantize_amount(amount_usd, 2)
    return {
        'value': str(value),
        'symbol': symbol,
        'code': code_out,
        'formatted': formatted,
        'usd_price': usd_price,
        'usd_equivalent': format_money(usd_eq, 2),
        'label': f'{formatted} {symbol}',
    }


def format_display(amount_usd, user, request=None) -> dict:
    """Return display payload for templates — uses user's permanent preferred currency."""
    return _format_amount(amount_usd, get_default_display_code(user, request=request))


def format_amount_for_code(amount_usd, currency_code: str) -> dict:
    """Format a platform USD-equivalent amount in an explicit currency code."""
    code = (currency_code or 'USD').strip() or 'USD'
    return _format_amount(amount_usd, code)


def format_amount_native(amount, currency_code: str) -> dict:
    """
    Format an amount already denominated in `currency_code` (no FX conversion).

    Use for exact user-entered "desired" amounts so receipts match what the user
    typed (e.g. 50,000 UGX stays 50,000 UGX, not a re-converted estimate).
    """
    code = (currency_code or 'USD').strip() or 'USD'
    meta = get_currency_meta(code)
    places = int(meta.get('decimals', 2) or 0)
    symbol = meta.get('symbol') or code
    try:
        raw = Decimal(str(amount).replace(',', '').strip())
    except Exception:
        raw = Decimal('0')
    q = Decimal('1').scaleb(-places) if places > 0 else Decimal('1')
    rounding = ROUND_HALF_UP if places == 0 else ROUND_DOWN
    value = raw.quantize(q, rounding=rounding)
    if places == 0:
        formatted = format_money(value, 0)
    elif places > 2:
        formatted = format_money(value, places, strip_trailing_zeros=True)
    else:
        formatted = format_money(value, 2)
    usd_eq = convert_to_usd(value, code)
    return {
        'value': str(value),
        'symbol': symbol,
        'code': meta.get('code') or code,
        'formatted': formatted,
        'usd_price': float(meta.get('rate_to_usd') or 1),
        'usd_equivalent': format_money(usd_eq, 2),
        'label': f'{formatted} {symbol}',
        'native': True,
    }


def _dec(val, default='0') -> Decimal:
    if val is None or val == '':
        return Decimal(default)
    try:
        return Decimal(str(val).replace(',', '').strip())
    except Exception:
        return Decimal(default)


def platform_usd_from_transaction(tx) -> Decimal:
    """
    Resolve the true platform (USD-equivalent) value of a Transaction row.

    Deposits may store crypto units in `amount`; withdrawals/investments store
    platform USD. Prefer explicit metadata when present.
    """
    md = getattr(tx, 'metadata', None) or {}
    for key in ('platform_usd', 'platform_credit'):
        if md.get(key) is not None and str(md.get(key)).strip() != '':
            return quantize_amount(_dec(md.get(key)), 8)

    tx_type = getattr(tx, 'tx_type', '') or ''
    amount = _dec(getattr(tx, 'amount', 0))
    currency = (getattr(tx, 'currency', '') or '').strip()

    # Crypto deposit rows: amount is on-chain units
    crypto_amt = md.get('crypto_amount')
    rate = md.get('rate_usd')
    if crypto_amt is not None and rate is not None:
        return quantize_amount(_dec(crypto_amt) * _dec(rate, '1'), 8)

    if tx_type == 'deposit' and currency and currency.upper() not in ('USD', ''):
        if rate is not None:
            return quantize_amount(amount * _dec(rate, '1'), 8)
        # Live price fallback by currency symbol
        crypto = resolve_display_crypto(currency)
        if crypto and crypto.usd_price and Decimal(str(crypto.usd_price)) > 0:
            return quantize_amount(amount * Decimal(str(crypto.usd_price)), 8)

    return quantize_amount(amount, 8)


def resolve_transaction_display_amounts(tx, display_code: str) -> dict:
    """
    Build consistent receipt / history amounts for a Transaction.

    Priority for the primary (desired) amount:
      1. metadata.display_amount in the same currency the user is viewing
      2. Platform USD → current display currency (including deposit credits)
    Fees / net always derive from platform USD so wallet math matches.
    """
    md = getattr(tx, 'metadata', None) or {}
    preferred = (display_code or 'USD').strip() or 'USD'
    platform = platform_usd_from_transaction(tx)

    fee_usd = _dec(md.get('fee_usd')) if md.get('fee_usd') is not None else _dec(getattr(tx, 'fee', 0))
    if fee_usd < 0:
        fee_usd = Decimal('0')
    if md.get('net_usd') is not None:
        net_usd = _dec(md.get('net_usd'))
    else:
        net_usd = quantize_amount(platform - fee_usd, 8)

    disp_amt = md.get('display_amount')
    disp_cur = (md.get('display_currency') or '').strip()

    # Exact desired amount when the viewer is on the same currency they entered
    if disp_amt is not None and str(disp_amt).strip() != '' and disp_cur:
        if disp_cur.upper() == preferred.upper():
            amount_display = format_amount_native(disp_amt, preferred)
        else:
            # Different display currency now — convert platform so numbers stay coherent
            amount_display = format_amount_for_code(platform, preferred)
    else:
        amount_display = format_amount_for_code(platform, preferred)

    fee_display = (
        format_amount_for_code(fee_usd, preferred)
        if fee_usd and fee_usd > 0
        else None
    )
    net_display = format_amount_for_code(net_usd, preferred)

    # When fee applies and amount was native desired, recompute net in native
    # space so Amount − Fee ≈ Net on the receipt (avoids FX double-rounding).
    if (
        amount_display.get('native')
        and fee_display
        and fee_display.get('value') is not None
    ):
        try:
            native_net = _dec(amount_display['value']) - _dec(fee_display['value'])
            if native_net < 0:
                native_net = Decimal('0')
            net_display = format_amount_native(native_net, preferred)
        except Exception:
            pass

    crypto_symbol = (
        md.get('crypto_symbol')
        or md.get('symbol')
        or (getattr(tx, 'currency', '') if tx_type_is_crypto_asset(tx) else '')
        or ''
    )
    crypto_amount = md.get('crypto_amount')
    if crypto_amount is None and tx_type_is_crypto_asset(tx) and not md.get('platform_usd'):
        # Deposit without metadata crypto_amount — amount field is crypto units
        if getattr(tx, 'tx_type', '') == 'deposit':
            crypto_amount = str(getattr(tx, 'amount', '') or '')

    return {
        'platform_usd': platform,
        'fee_usd': fee_usd,
        'net_usd': net_usd,
        'amount_display': amount_display,
        'fee_display': fee_display,
        'net_display': net_display,
        'desired_amount': disp_amt,
        'desired_currency': disp_cur,
        'crypto_amount': crypto_amount,
        'crypto_symbol': crypto_symbol,
        'rate_usd': md.get('rate_usd'),
    }


def tx_type_is_crypto_asset(tx) -> bool:
    """True when the transaction's amount field may be crypto units, not platform USD."""
    if getattr(tx, 'tx_type', '') == 'deposit':
        return True
    md = getattr(tx, 'metadata', None) or {}
    return bool(md.get('crypto_amount') and md.get('rate_usd') and not md.get('platform_usd'))


def get_currency_meta(currency_code: str) -> dict:
    """
    Metadata for a display currency: code, symbol, decimal places, unit rate to USD.
    """
    code = (currency_code or 'USD').strip() or 'USD'
    upper = code.upper()
    if upper == 'USD':
        return {
            'code': 'USD',
            'symbol': 'USD',
            'decimals': 2,
            'rate_to_usd': Decimal('1'),
            'kind': 'fiat',
        }
    fiat = _fiat_rate(code)
    if fiat:
        rate, meta = fiat
        return {
            'code': upper,
            'symbol': meta.get('symbol') or upper,
            'decimals': int(meta.get('decimals', 2)),
            'rate_to_usd': rate,
            'kind': 'fiat',
        }
    crypto = resolve_display_crypto(code)
    if crypto:
        return {
            'code': crypto.symbol,
            'symbol': crypto.symbol,
            'decimals': min(8, crypto.decimals or 8),
            'rate_to_usd': Decimal(str(crypto.usd_price or 1)),
            'kind': 'crypto',
        }
    return {
        'code': 'USD',
        'symbol': 'USD',
        'decimals': 2,
        'rate_to_usd': Decimal('1'),
        'kind': 'fiat',
    }


def resolve_currency_code(user, currency: str | None = None, request=None) -> str | None:
    """
    Validate an optional currency override.
    Returns normalized code, or None if invalid.
    Empty/None → user's permanent default (DB / session / cookie).
    """
    if currency is None or str(currency).strip() == '':
        return get_default_display_code(user, request=request)
    return _normalize_display_code(str(currency).strip()[:20])


def build_balance_api_payload(user, currency: str | None = None) -> dict:
    """
    JSON-ready dashboard balance snapshot in the requested (or preferred) currency.
    Does not mutate the user's preference.
    """
    from django.db.models import Count, Sum
    from investments.models import Investment
    from transactions.models import Deposit

    # Soft-refresh free market prices so conversions stay current
    try:
        from core.price_feed import ensure_fresh_prices
        ensure_fresh_prices()
    except Exception:
        pass

    code = resolve_currency_code(user, currency)
    if code is None:
        return {'ok': False, 'error': 'Invalid display currency.'}

    wallet, _ = Wallet.objects.get_or_create(user=user)
    active = Investment.objects.filter(user=user, status=Investment.Status.ACTIVE)
    active_value = active.aggregate(t=Sum('amount'))['t'] or Decimal('0')
    pending = Deposit.objects.filter(
        user=user,
        status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
    ).aggregate(total=Sum('amount'), count=Count('id'))

    available = _format_amount(wallet.available_balance, code)
    balance = _format_amount(wallet.balance, code)
    profit = _format_amount(wallet.total_profit, code)
    locked = _format_amount(wallet.locked_balance, code)
    referral = _format_amount(getattr(user, 'referral_earnings', 0) or 0, code)
    active_capital = _format_amount(active_value, code)

    pending_usd = Decimal('0')
    for dep in Deposit.objects.filter(
        user=user,
        status__in=[Deposit.Status.PENDING, Deposit.Status.WAITING_CONFIRMATION],
    ).select_related('cryptocurrency'):
        if getattr(dep, 'credit_amount', None) is not None:
            pending_usd += Decimal(str(dep.credit_amount))
            continue
        amt = Decimal(str(dep.amount or 0))
        price = getattr(getattr(dep, 'cryptocurrency', None), 'usd_price', None) or Decimal('0')
        if price and price > 0:
            pending_usd += amt * Decimal(str(price))
        else:
            pending_usd += amt
    pending_total = _format_amount(pending_usd, code)

    crypto = resolve_display_crypto(code)
    fiat = _fiat_rate(code) if not crypto else None
    if crypto:
        symbol = crypto.symbol
        usd_price = float(crypto.usd_price) if crypto.usd_price else 1.0
    elif fiat:
        rate, meta = fiat
        symbol = meta.get('symbol') or code
        usd_price = float(rate)
    else:
        symbol = 'USD'
        usd_price = 1.0

    return {
        'ok': True,
        'currency': code,
        'symbol': symbol,
        'usd_price': usd_price,
        'available': available,
        'balance': balance,
        'profit': profit,
        'locked': locked,
        'referral': referral,
        'active_investments': {
            'count': active.count(),
            'capital': active_capital,
        },
        'pending_deposits': {
            'count': pending['count'] or 0,
            'total': pending_total,
        },
        'options': [
            {'code': o['code'], 'label': o['label'], 'symbol': o['symbol']}
            for o in get_display_currencies_for_user(user)
        ],
    }


def user_display_context(user, request=None):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        fresh = User.objects.filter(pk=user.pk).values_list('preferred_currency', flat=True).first()
        if fresh is not None:
            user.preferred_currency = fresh
    except Exception:
        pass

    code = get_default_display_code(user, request=request)

    # If user has an explicit preference, never auto-overwrite it with deposit crypto.
    # Only seed preferred_currency when it is still empty (first visit).
    has_pref = bool((user.preferred_currency or '').strip())
    if not has_pref and code:
        try:
            from django.contrib.auth import get_user_model
            get_user_model().objects.filter(pk=user.pk).update(preferred_currency=code)
            user.preferred_currency = code
            has_pref = True
        except Exception:
            pass

    # Keep session in sync with permanent preference so refresh always hits the same code
    if request is not None and code:
        try:
            if request.session.get('display_currency') != code:
                request.session['display_currency'] = code
                request.session.modified = True
        except Exception:
            pass

    options = get_display_currencies_for_user(user)
    codes = {o['code'] for o in options}
    if code not in codes:
        c = resolve_display_crypto(code)
        if c:
            options.insert(0, {
                'code': c.symbol,
                'label': f'{c.name} ({c.symbol})',
                'symbol': c.symbol,
                'usd_price': c.usd_price or Decimal('1'),
                'kind': 'crypto',
            })
        else:
            fiat = _fiat_rate(code)
            if fiat:
                _rate, meta = fiat
                options.insert(0, {
                    'code': code.upper(),
                    'label': meta.get('label') or code,
                    'symbol': meta.get('symbol') or code,
                    'usd_price': _rate,
                    'kind': 'fiat',
                })
            else:
                options.insert(0, {
                    'code': code,
                    'label': code,
                    'symbol': code,
                    'usd_price': Decimal('1'),
                    'kind': 'other',
                })
    return {
        'display_currency': code,
        'display_options': options,
        'bal_display': format_amount_for_code(wallet.balance, code),
        'available_display': format_amount_for_code(wallet.available_balance, code),
        'profit_display': format_amount_for_code(wallet.total_profit, code),
        'locked_display': format_amount_for_code(wallet.locked_balance, code),
        'referral_display': format_amount_for_code(
            getattr(user, 'referral_earnings', 0) or 0, code
        ),
    }
