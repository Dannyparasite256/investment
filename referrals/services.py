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


def get_program_rates(program=None):
    """
    Live rates from the active program.
    Level 1 always follows commission_percent (what staff edits).
    """
    program = program or ReferralProgram.get_active()
    if not program or not program.is_active:
        pct = Decimal(str(getattr(settings, 'REFERRAL_BONUS_PERCENT', 5)))
        return {
            'program': None,
            'source': 'deposit',
            'min_dep': Decimal('0'),
            'max_cap': None,
            'max_levels': 1,
            'rates': {1: pct, 2: Decimal('0'), 3: Decimal('0')},
        }

    # Master L1 rate = commission_percent (staff-facing field)
    l1 = program.commission_percent
    if l1 is None:
        l1 = program.level1_percent
    if l1 is None:
        l1 = Decimal(str(getattr(settings, 'REFERRAL_BONUS_PERCENT', 5)))

    max_levels = min(3, max(1, int(program.max_levels or 1)))
    rates = {
        1: Decimal(str(l1)),
        2: Decimal(str(program.level2_percent or 0)),
        3: Decimal(str(program.level3_percent or 0)),
    }
    # If max_levels is 1, ignore L2/L3
    if max_levels < 2:
        rates[2] = Decimal('0')
        rates[3] = Decimal('0')
    if max_levels < 3:
        rates[3] = Decimal('0')

    return {
        'program': program,
        'source': program.commission_on or 'deposit',
        'min_dep': Decimal(str(program.min_deposit_for_commission or 0)),
        'max_cap': program.max_commission_per_referral,
        'max_levels': max_levels,
        'rates': rates,
    }


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
def process_referral_commission(
    referred_user,
    base_amount,
    source='deposit',
    reference_type='',
    reference_id='',
):
    """
    Credit upline referrers (1–3 levels) using the *current* active program rates.
    Safe to call multiple times for the same deposit — skips already-paid levels.
    """
    if not referred_user or not getattr(referred_user, 'referred_by_id', None):
        return []

    cfg = get_program_rates()
    # When program says commission_on=investment, only pay on that source, etc.
    # Special case: empty program uses deposit-like behaviour for any matching source flag.
    expected_source = cfg['source']
    if expected_source and expected_source != source:
        logger.info(
            'Skip referral: source=%s but program pays on %s',
            source, expected_source,
        )
        return []

    base_amount = Decimal(str(base_amount or 0))
    if base_amount <= 0:
        return []
    if base_amount < cfg['min_dep']:
        logger.info('Skip referral: base %s < min %s', base_amount, cfg['min_dep'])
        return []

    rates = cfg['rates']
    max_cap = cfg['max_cap']
    max_levels = cfg['max_levels']
    created = []

    for level, referrer in _upline_chain(referred_user, max_levels=max_levels):
        # Idempotent: don't double-pay same deposit/level
        if reference_id:
            already = ReferralCommission.objects.filter(
                referrer=referrer,
                referred_user=referred_user,
                reference_type=reference_type or source,
                reference_id=str(reference_id),
                level=level,
            ).exclude(status=ReferralCommission.Status.CANCELLED).exists()
            if already:
                logger.info(
                    'Skip L%s commission already paid ref=%s',
                    level, reference_id,
                )
                continue

        rate = Decimal(str(rates.get(level) or 0))
        if rate <= 0:
            continue

        # VIP boost only on level 1
        if level == 1:
            try:
                tier = get_user_tier(referrer)
                if tier and tier.referral_bonus_boost:
                    rate = rate + Decimal(str(tier.referral_bonus_boost))
            except Exception:
                pass

        amount = quantize_amount(base_amount * rate / Decimal('100'))
        if max_cap is not None and level == 1:
            cap = Decimal(str(max_cap))
            if cap > 0 and amount > cap:
                amount = quantize_amount(cap)
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
            reference_type=reference_type or source,
            reference_id=str(reference_id) if reference_id else '',
            paid_at=timezone.now(),
            notes=f'L{level} commission @ {rate}% of {base_amount}',
        )
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=referrer)
        wallet.credit(amount)
        from django.contrib.auth import get_user_model
        User = get_user_model()
        User.objects.filter(pk=referrer.pk).update(
            referral_earnings=F('referral_earnings') + amount,
        )
        # refresh wallet balance after credit
        wallet.refresh_from_db(fields=['balance'])
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.REFERRAL,
            amount=amount,
            balance_after=wallet.balance,
            description=f'L{level} referral from {referred_user.email} @ {rate}%',
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
                f'You earned {amount} ({rate}% of {base_amount}) from {referred_user.email}.',
                level=Notification.Level.SUCCESS,
                category=Notification.Category.REFERRAL,
                link='/referrals/',
                email=getattr(referrer, 'email_alerts', True),
                event_name='referral.commission',
            )
        except Exception:
            try:
                from notifications.models import notify
                notify(
                    referrer, f'Level {level} referral commission',
                    f'You earned {amount} from {referred_user.email}.',
                    level=Notification.Level.SUCCESS,
                    category=Notification.Category.REFERRAL,
                    link='/app/referrals',
                )
            except Exception:
                pass
        created.append(commission)
        logger.info(
            'L%s commission %s to %s amount=%s rate=%s%% base=%s',
            level, commission.id, referrer.email, amount, rate, base_amount,
        )
    return created
