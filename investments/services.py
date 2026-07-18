"""Investment business logic: create investments, process earnings, reinvest."""
import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import F
from django.utils import timezone

from core.models import AuditLog
from core.utils import create_audit_log, quantize_amount
from investments.models import Earning, Investment, InvestmentPlan, Reinvestment
from notifications.models import Notification, notify
from transactions.models import Transaction
from wallets.models import Wallet, WalletLedger

logger = logging.getLogger('investments')


@transaction.atomic
def create_investment(user, plan: InvestmentPlan, amount, auto_reinvest=False, duration_days=None, request=None):
    """Create a new investment and lock funds from wallet."""
    if not plan.is_available:
        raise ValueError('This investment plan is not available')

    if plan.require_kyc or plan.is_premium:
        if not user.is_kyc_verified:
            raise ValueError('KYC verification is required for this plan')
        if user.kyc_expires_at and user.kyc_expires_at < timezone.now().date():
            raise ValueError('Your KYC has expired. Please re-submit documents.')

    if plan.min_vip_slug:
        from core.vip import get_user_tier
        tier = get_user_tier(user)
        if not tier or tier.slug != plan.min_vip_slug:
            # Allow higher tiers by sort_order
            from core.platform_models import VIPTier
            required = VIPTier.objects.filter(slug=plan.min_vip_slug).first()
            if required and (not tier or tier.min_total_invested < required.min_total_invested):
                raise ValueError(f'This plan requires VIP tier: {required.name}')

    amount = quantize_amount(amount)
    if amount < plan.min_deposit:
        raise ValueError(f'Minimum deposit is {plan.min_deposit}')
    if amount > plan.max_deposit:
        raise ValueError(f'Maximum deposit is {plan.max_deposit}')

    if plan.max_investments_per_user:
        active_count = Investment.objects.filter(
            user=user, plan=plan, status=Investment.Status.ACTIVE
        ).count()
        if active_count >= plan.max_investments_per_user:
            raise ValueError('Maximum investments for this plan reached')

    days = duration_days or plan.duration_days
    if plan.duration_flexible:
        if plan.min_duration_days and days < plan.min_duration_days:
            raise ValueError(f'Minimum duration is {plan.min_duration_days} days')
        if plan.max_duration_days and days > plan.max_duration_days:
            raise ValueError(f'Maximum duration is {plan.max_duration_days} days')

    wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
    if wallet.available_balance < amount:
        raise ValueError('Insufficient available balance')

    wallet.debit(amount)
    # Track invested capital for portfolio stats (balance already reduced)
    Wallet.objects.filter(pk=wallet.pk).update(
        total_invested=F('total_invested') + amount,
    )
    wallet.refresh_from_db()

    WalletLedger.objects.create(
        wallet=wallet,
        entry_type=WalletLedger.EntryType.INVESTMENT,
        amount=-amount,
        balance_after=wallet.balance,
        description=f'Invested in {plan.name}',
        reference_type='investment_plan',
        reference_id=str(plan.id),
    )

    now = timezone.now()
    expected = plan.periods_count(days)
    from datetime import timedelta as _td

    next_payout = (
        now + plan.period_delta()
        if plan.payout_frequency != InvestmentPlan.PayoutFrequency.END
        else now + _td(days=days)
    )

    inv = Investment.objects.create(
        user=user,
        plan=plan,
        amount=amount,
        profit_rate_percent=plan.profit_rate_percent,
        profit_method=plan.profit_method,
        payout_frequency=plan.payout_frequency,
        duration_days=days,
        return_principal=plan.return_principal,
        auto_reinvest=auto_reinvest and plan.allow_auto_reinvest,
        expected_payouts=expected,
        started_at=now,
        matures_at=now + _td(days=days),
        next_payout_at=next_payout,
    )

    InvestmentPlan.objects.filter(pk=plan.pk).update(
        total_invested=F('total_invested') + amount,
        investors_count=F('investors_count') + 1,
    )

    Transaction.objects.create(
        user=user,
        tx_type=Transaction.TxType.INVESTMENT,
        amount=amount,
        status=Transaction.Status.COMPLETED,
        description=f'Investment in {plan.name}',
        reference_type='investment',
        reference_id=str(inv.id),
    )

    notify(
        user,
        'Investment Created',
        f'You invested {amount} in {plan.name}. Maturity: {inv.matures_at.date()}.',
        level=Notification.Level.SUCCESS,
        category=Notification.Category.INVESTMENT,
        link=f'/investments/{inv.id}/',
    )

    create_audit_log(
        request=request,
        user=user,
        action=AuditLog.Action.INVEST_CREATE,
        message=f'Created investment {inv.id} amount={amount} plan={plan.name}',
        object_type='Investment',
        object_id=str(inv.id),
    )

    logger.info('Investment created id=%s user=%s amount=%s', inv.id, user.email, amount)
    return inv


@transaction.atomic
def process_earning(investment: Investment):
    """Pay one period of profit for an active investment."""
    inv = Investment.objects.select_for_update().get(pk=investment.pk)
    if inv.status != Investment.Status.ACTIVE:
        return None

    now = timezone.now()
    profit = inv.calculate_period_profit()
    if profit <= 0:
        logger.warning('Zero profit for investment %s', inv.id)

    wallet, _ = Wallet.objects.select_for_update().get_or_create(user=inv.user)

    reinvested = False
    if inv.auto_reinvest and inv.plan.allow_auto_reinvest and not inv.is_matured:
        # Auto reinvest: add profit to principal (compound within same investment)
        inv.amount = quantize_amount(inv.amount + profit)
        inv.total_earned = quantize_amount(inv.total_earned + profit)
        reinvested = True
        Wallet.objects.filter(pk=wallet.pk).update(total_profit=F('total_profit') + profit)
        wallet.refresh_from_db()
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.REINVEST,
            amount=profit,
            balance_after=wallet.balance,
            description=f'Auto-reinvested profit from {inv.plan.name}',
            reference_type='investment',
            reference_id=str(inv.id),
        )
    else:
        wallet.credit(profit, update_profit=True)
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.PROFIT,
            amount=profit,
            balance_after=wallet.balance,
            description=f'Profit from {inv.plan.name}',
            reference_type='investment',
            reference_id=str(inv.id),
        )
        inv.total_earned = quantize_amount(inv.total_earned + profit)

    inv.payouts_count += 1
    inv.last_payout_at = now

    earning = Earning.objects.create(
        investment=inv,
        user=inv.user,
        amount=profit,
        period_number=inv.payouts_count,
        is_reinvested=reinvested,
        description=f'Period {inv.payouts_count} payout',
    )

    Transaction.objects.create(
        user=inv.user,
        tx_type=Transaction.TxType.REINVEST if reinvested else Transaction.TxType.PROFIT,
        amount=profit,
        status=Transaction.Status.COMPLETED,
        description=f'{"Reinvested " if reinvested else ""}Profit from {inv.plan.name}',
        reference_type='earning',
        reference_id=str(earning.id),
    )

    # Schedule next payout or complete
    if inv.is_matured or inv.payouts_count >= inv.expected_payouts:
        complete_investment(inv)
    else:
        inv.next_payout_at = now + inv.plan.period_delta()
        inv.save()

    notify(
        inv.user,
        'Profit Credited' if not reinvested else 'Profit Reinvested',
        f'{profit} {"reinvested into" if reinvested else "added from"} {inv.plan.name}.',
        level=Notification.Level.SUCCESS,
        category=Notification.Category.EARNING,
    )

    logger.info('Earning %s for investment %s amount=%s reinvest=%s', earning.id, inv.id, profit, reinvested)
    return earning


@transaction.atomic
def complete_investment(inv: Investment):
    """Mark investment complete and optionally return principal."""
    if inv.status == Investment.Status.COMPLETED:
        return inv

    inv.status = Investment.Status.COMPLETED
    inv.completed_at = timezone.now()
    inv.next_payout_at = None
    inv.save()

    if inv.return_principal:
        wallet, _ = Wallet.objects.select_for_update().get_or_create(user=inv.user)
        wallet.credit(inv.amount)
        Wallet.objects.filter(pk=wallet.pk).update(
            total_invested=F('total_invested') - inv.amount,
        )
        wallet.refresh_from_db()
        WalletLedger.objects.create(
            wallet=wallet,
            entry_type=WalletLedger.EntryType.REFUND,
            amount=inv.amount,
            balance_after=wallet.balance,
            description=f'Principal returned from {inv.plan.name}',
            reference_type='investment',
            reference_id=str(inv.id),
        )
        Transaction.objects.create(
            user=inv.user,
            tx_type=Transaction.TxType.REFUND,
            amount=inv.amount,
            status=Transaction.Status.COMPLETED,
            description=f'Principal returned — {inv.plan.name}',
            reference_type='investment',
            reference_id=str(inv.id),
        )

    # Auto reinvest into new plan instance if enabled at maturity
    if inv.auto_reinvest and inv.plan.allow_auto_reinvest and inv.plan.is_available:
        try:
            new_inv = create_investment(
                inv.user,
                inv.plan,
                inv.amount if inv.return_principal else inv.amount,  # already credited
                auto_reinvest=True,
            )
            Reinvestment.objects.create(
                user=inv.user,
                source_investment=inv,
                new_investment=new_inv,
                amount=new_inv.amount,
                mode=Reinvestment.Mode.AUTO,
            )
        except Exception as exc:
            logger.exception('Auto-reinvest failed for %s: %s', inv.id, exc)

    notify(
        inv.user,
        'Investment Completed',
        f'Your investment in {inv.plan.name} has matured. Total earned: {inv.total_earned}.',
        level=Notification.Level.SUCCESS,
        category=Notification.Category.INVESTMENT,
    )

    create_audit_log(
        user=inv.user,
        action=AuditLog.Action.INVEST_COMPLETE,
        message=f'Investment {inv.id} completed, earned={inv.total_earned}',
        object_type='Investment',
        object_id=str(inv.id),
    )
    return inv


@transaction.atomic
def manual_reinvest(user, investment: Investment, plan: InvestmentPlan = None, request=None):
    """Manually reinvest principal+profits into a plan using available balance."""
    plan = plan or investment.plan
    if not plan.allow_manual_reinvest:
        raise ValueError('Manual reinvestment is not allowed for this plan')
    if not plan.is_available:
        raise ValueError('Plan is not available')

    # Use available balance (user must have funds — typically after maturity return)
    wallet, _ = Wallet.objects.get_or_create(user=user)
    amount = quantize_amount(investment.amount)  # reinvest same size by default
    if wallet.available_balance < amount:
        amount = wallet.available_balance
    if amount < plan.min_deposit:
        raise ValueError('Insufficient balance to reinvest at plan minimum')

    new_inv = create_investment(user, plan, amount, auto_reinvest=False, request=request)
    Reinvestment.objects.create(
        user=user,
        source_investment=investment,
        new_investment=new_inv,
        amount=amount,
        mode=Reinvestment.Mode.MANUAL,
    )
    return new_inv
