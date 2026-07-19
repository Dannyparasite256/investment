"""Display currency options + live converted balances for the Vue SPA."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from wallets.display import (
    build_balance_api_payload,
    get_currency_meta,
    get_default_display_code,
    get_display_currencies_for_user,
    persist_display_currency,
    resolve_currency_code,
)


def _serialize_option(opt):
    return {
        'code': opt['code'],
        'label': opt['label'],
        'symbol': opt.get('symbol') or opt['code'],
        'kind': opt.get('kind') or 'crypto',
        'usd_price': str(opt.get('usd_price') or 1),
        'network': opt.get('network') or '',
    }


class CurrencyOptionsView(APIView):
    """List crypto + fiat currencies the user can display balances in."""

    def get(self, request):
        try:
            from core.price_feed import ensure_fresh_prices
            ensure_fresh_prices()
        except Exception:
            pass
        options = get_display_currencies_for_user(request.user)
        current = get_default_display_code(request.user, request=request)
        meta = get_currency_meta(current)
        return Response({
            'current': current,
            'meta': {
                'code': meta['code'],
                'symbol': str(meta['symbol']),
                'decimals': int(meta.get('decimals') or 2),
                'kind': meta.get('kind') or 'fiat',
                'rate_to_usd': str(meta.get('rate_to_usd') or 1),
            },
            'options': [_serialize_option(o) for o in options],
        })


class BalancesView(APIView):
    """
    Live balances converted to preferred or override currency.
    GET /api/v1/balances/?currency=UGX
    """

    def get(self, request):
        currency = request.GET.get('currency')
        payload = build_balance_api_payload(request.user, currency)
        status = 200 if payload.get('ok') else 400
        # Ensure JSON-serializable decimals
        return Response(payload, status=status)


class SetDisplayCurrencyView(APIView):
    """Permanently save display currency (DB + session + cookie)."""

    def post(self, request):
        code = (request.data.get('currency') or '').strip()[:20]
        if not code:
            return Response({'ok': False, 'error': 'Please choose a display currency.'}, status=400)
        resolved = resolve_currency_code(request.user, code, request=request)
        if resolved is None:
            return Response({'ok': False, 'error': 'Invalid display currency.'}, status=400)
        try:
            persist_display_currency(request.user, resolved, request=request, response=None)
            payload = build_balance_api_payload(request.user, resolved)
            payload['currency'] = resolved
            payload['message'] = f'Display currency saved as {resolved}.'
            payload['saved'] = True
            payload['permanent'] = True
            response = Response(payload)
            # Cookie on DRF Response
            response.set_cookie(
                'display_currency',
                resolved,
                max_age=60 * 60 * 24 * 400,
                samesite='Lax',
                httponly=False,
                path='/',
            )
            return response
        except ValueError as exc:
            return Response({'ok': False, 'error': str(exc)}, status=400)
