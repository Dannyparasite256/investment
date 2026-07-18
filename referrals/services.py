"""Multi-level referral commission calculation and payout."""
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core.utils import quantize_amount
from core.vip import get_user_tier
from notifications.models import Notification
from referrals.models import ReferralCommission, ReferralProgram
from transactions.models import Transaction
from wallets.models import Wallet, WalletLedger

logger = logging.getLogger('referrals')


def _upline_chain(user, max_levels=3):
    """Yield (level, referrer) walking referred_by chain."""
    current = user
    for level in range(1, max_levels + 1):
        parent = getattr(current, 'referred_by', None)
        if not parent:
            break
        yield level, parent
        current = parent


@transaction.atomic
def process_referral_commission(referred_user, base_amount, source='deposit', reference_type='', reference_id=''):
    """
    Credit upline referrers (1–3 levels) based on program settings.
    Level-1 rate may get VIP referral boost.
    """
    if not referred_user.referred_by_id:
        return []

    program = ReferralProgram.get_active()
    if program:
        if program.commission_on != source:
            return []
        min_dep = program.min_deposit_for_commission or Decimal('0')
        max_cap = program.max_commission_per_referral
        max_levels = min(3, max(1, program.max_levels or 1))
        rates = {
            1: program.level1_percent if program.level1_percent is not None else program.commission_percent,
            2: program.level2_percent,
            3: program.level3_percent,
        }
    else:
        min_dep = Decimal('0')
        max_cap = None
        max_levels = 1
        rates = {1: Decimal(str(getattr(settings, 'REFERRAL_BONUS_PERCENT', 5))), 2: Decimal('0'), 3: Decimal('0')}

    base_amount = Decimal(str(base_amount))
    if base_amount < min_dep:
        return []

    created = []
    for level, referrer in _upline_chain(referred_user, max_levels=max_levels):
        rate = Decimal(str(rates.get(level) or 0))
        if rate <= 0:
            continue
        # VIP boost only on level 1
        if level == 1:
            tier = get_user_tier(referrer)
            if tier and tier.referral_bonus_boost:
                rate = rate + Decimal(str(tier.referral_bonus_boost))

        amount = quantize_amount(base_amount * rate / Decimal('100'))
        if max_cap and level == 1 and amount > max_cap:
            amount = max_cap
        if amount <= 0:
            continue

        commission = ReferralCommission.objects.create(
            referrer=referrer,
            referred_user=referred_user,
            amount=amount,
            rate_percent=rate,
            base_amount=base_amount,
            source=source,
            level=level,
            status=ReferralCommission.Status.PAID,
            reference_type=reference_type,
            reference_id=str(reference_id),
            paid_at=timezone.now(),
            notes=f'L{level} commission',
        )
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=referrer)
        wallet.credit(amount)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.filter(pk=referrer.pk).update(referral_earnings=F('referral_earnings') + amount)
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.REFERRAL,
            amount=amount,
            balance_after=wallet.balance,
            description=f'L{level} referral from {referred_user.email}',
            reference_type='referral_commission',
            reference_id=str(commission.id),
        )
        Transaction.objects.create(
            user=referrer,
            tx_type=Transaction.TxType.REFERRAL,
            amount=amount,
            currency='USD',
            status=Transaction.Status.COMPLETED,
            description=f'L{level} referral bonus ({rate}% of {base_amount})',
            reference_type='referral_commission',
            reference_id=str(commission.id),
        )
        try:
            from core.notify_service import alert_user
            alert_user(
                referrer,
                f'Level {level} referral commission',
                f'You earned {amount} (L{level}) from {referred_user.email}.',
                level=Notification.Level.SUCCESS,
                category=Notification.Category.REFERRAL,
                link='/referrals/',
                email=getattr(referrer, 'email_alerts', True),
                event_name='referral.commission',
            )
        except Exception:
            from notifications.models import notify
            notify(
                referrer, f'Level {level} referral commission',
                f'You earned {amount} from {referred_user.email}.',
                level=Notification.Level.SUCCESS, category=Notification.Category.REFERRAL,
            )
        created.append(commission)
        logger.info('L%s commission %s to %s amount=%s', level, commission.id, referrer.email, amount)
    return created
