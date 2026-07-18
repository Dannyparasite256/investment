"""VIP tier resolution and fee helpers."""
from decimal import Decimal

from django.db.models import Sum

from core.platform_models import VIPTier
from core.utils import quantize_amount
from wallets.models import Wallet


def user_total_invested(user) -> Decimal:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    # Prefer lifetime invested; fall back to sum of active investments
    total = wallet.total_invested or Decimal('0')
    if total <= 0:
        from investments.models import Investment
        total = Investment.objects.filter(user=user).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    return Decimal(str(total))


def get_user_tier(user):
    return VIPTier.for_amount(user_total_invested(user))


def apply_deposit_fee(user, amount) -> tuple:
    """Return (net_credit, fee_amount, fee_percent)."""
    amount = Decimal(str(amount))
    tier = get_user_tier(user)
    pct = tier.deposit_fee_percent if tier else Decimal('0')
    fee = quantize_amount(amount * pct / Decimal('100'))
    return quantize_amount(amount - fee), fee, pct


def apply_withdrawal_fee(user, amount, crypto_fee=None) -> tuple:
    """Return (fee_total, fee_percent) combining crypto fee + VIP %."""
    amount = Decimal(str(amount))
    crypto_fee = Decimal(str(crypto_fee or 0))
    tier = get_user_tier(user)
    pct = tier.withdrawal_fee_percent if tier else Decimal('0')
    pct_fee = quantize_amount(amount * pct / Decimal('100'))
    return quantize_amount(crypto_fee + pct_fee), pct


def refresh_user_vip_context(user):
    from core.platform_models import VIPTier
    tier = get_user_tier(user)
    total = user_total_invested(user)
    next_tier = (
        VIPTier.objects.filter(is_active=True, min_total_invested__gt=total)
        .order_by('min_total_invested')
        .first()
    )
    progress_pct = 100
    remaining = Decimal('0')
    if next_tier:
        floor = Decimal(str(tier.min_total_invested)) if tier else Decimal('0')
        span = Decimal(str(next_tier.min_total_invested)) - floor
        done = total - floor
        progress_pct = int(max(0, min(100, float(done / span * 100) if span > 0 else 0)))
        remaining = max(Decimal('0'), Decimal(str(next_tier.min_total_invested)) - total)
    return {
        'tier': tier,
        'total_invested': total,
        'next_tier': next_tier,
        'vip_progress_pct': progress_pct,
        'vip_remaining': remaining,
    }
