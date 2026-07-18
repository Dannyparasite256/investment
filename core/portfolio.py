"""Portfolio equity snapshots for performance charts."""
from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from core.platform_models import PortfolioSnapshot
from investments.models import Investment
from wallets.models import Wallet


def compute_equity(user):
    wallet, _ = Wallet.objects.get_or_create(user=user)
    active = Investment.objects.filter(user=user, status=Investment.Status.ACTIVE).aggregate(
        t=Sum('amount')
    )['t'] or Decimal('0')
    balance = wallet.balance or Decimal('0')
    profit = wallet.total_profit or Decimal('0')
    # Equity = available balance + capital in active investments
    equity = balance + active
    return {
        'balance': balance,
        'invested': active,
        'profit': profit,
        'equity': equity,
    }


def record_snapshot(user, on_date=None):
    on_date = on_date or timezone.localdate()
    data = compute_equity(user)
    snap, _ = PortfolioSnapshot.objects.update_or_create(
        user=user,
        date=on_date,
        defaults=data,
    )
    return snap


def chart_series(user, days=30):
    """Return labels + equity values; backfill from ledger-ish estimate if sparse."""
    since = timezone.localdate() - timedelta(days=days)
    snaps = list(
        PortfolioSnapshot.objects.filter(user=user, date__gte=since).order_by('date')
    )
    if not snaps:
        # Create today's point so chart isn't empty
        record_snapshot(user)
        snaps = list(
            PortfolioSnapshot.objects.filter(user=user, date__gte=since).order_by('date')
        )
    labels = [s.date.isoformat() for s in snaps]
    equity = [float(s.equity) for s in snaps]
    profit = [float(s.profit) for s in snaps]
    return labels, equity, profit


def snapshot_all_users():
    from django.contrib.auth import get_user_model
    User = get_user_model()
    count = 0
    for u in User.objects.filter(is_active=True).iterator():
        record_snapshot(u)
        count += 1
    return count
