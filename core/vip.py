"""VIP tier resolution and fee helpers."""
from decimal import Decimal

from django.db.models import Sum

from core.platform_models import VIPTier
from core.utils import quantize_amount
from wallets.models import Wallet

# Animated sticker assets (SVG with SMIL animation — plays like a sticker/gif)
TIER_STICKERS = {
    'starter': 'img/vip/starter.svg',
    'bronze': 'img/vip/bronze.svg',
    'silver': 'img/vip/silver.svg',
    'gold': 'img/vip/gold.svg',
    'platinum': 'img/vip/platinum.svg',
    'diamond': 'img/vip/diamond.svg',
    'elite': 'img/vip/diamond.svg',
    'legend': 'img/vip/diamond.svg',
}

TIER_EMOJIS = {
    'starter': '⭐',
    'bronze': '🥉',
    'silver': '🥈',
    'gold': '🥇',
    'platinum': '💎',
    'diamond': '👑',
    'elite': '👑',
    'legend': '👑',
}

TIER_TAGLINES = {
    'starter': 'Begin your climb',
    'bronze': 'Solid foundation',
    'silver': 'Rising star',
    'gold': 'Premium member',
    'platinum': 'Elite status',
    'diamond': 'Legendary',
}


def tier_sticker_key(tier) -> str:
    """Map a VIPTier (or name/slug string) to a sticker key."""
    if tier is None:
        return 'starter'
    slug = (getattr(tier, 'slug', None) or '').strip().lower()
    name = (getattr(tier, 'name', None) or str(tier) or '').strip().lower()
    for key in TIER_STICKERS:
        if key in slug or key in name:
            return key
    # Heuristic by sort / invest floor
    try:
        m = Decimal(str(getattr(tier, 'min_total_invested', 0) or 0))
        if m >= 50000:
            return 'platinum'
        if m >= 10000:
            return 'gold'
        if m >= 1000:
            return 'silver'
        if m > 0:
            return 'bronze'
    except Exception:
        pass
    return 'bronze'


def tier_sticker_static(tier) -> str:
    """Relative static path for the animated tier sticker."""
    return TIER_STICKERS.get(tier_sticker_key(tier), TIER_STICKERS['starter'])


def tier_emoji(tier) -> str:
    return TIER_EMOJIS.get(tier_sticker_key(tier), '⭐')


def tier_tagline(tier) -> str:
    return TIER_TAGLINES.get(tier_sticker_key(tier), 'VIP member')


def decorate_tier(tier):
    """Attach sticker metadata on a VIPTier instance for templates."""
    if tier is None:
        return None
    key = tier_sticker_key(tier)
    tier.sticker_key = key
    tier.sticker_path = TIER_STICKERS.get(key, TIER_STICKERS['starter'])
    tier.sticker_emoji = TIER_EMOJIS.get(key, '⭐')
    tier.sticker_tagline = TIER_TAGLINES.get(key, 'VIP member')
    return tier


def user_total_invested(user) -> Decimal:
    wallet, _ = Wallet.objects.get_or_create(user=user)
    # Prefer lifetime invested; fall back to sum of active investments
    total = wallet.total_invested or Decimal('0')
    if total <= 0:
        from investments.models import Investment
        total = Investment.objects.filter(user=user).aggregate(t=Sum('amount'))['t'] or Decimal('0')
    return Decimal(str(total))


def get_user_tier(user):
    return decorate_tier(VIPTier.for_amount(user_total_invested(user)))


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
    next_tier = decorate_tier(
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
        'sticker_path': tier_sticker_static(tier) if tier else TIER_STICKERS['starter'],
        'sticker_emoji': tier_emoji(tier) if tier else '⭐',
        'sticker_key': tier_sticker_key(tier) if tier else 'starter',
    }
