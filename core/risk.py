"""Simple user risk scoring for staff."""
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone

from accounts.security_models import LoginHistory
from transactions.models import Deposit, Withdrawal


def compute_risk_score(user) -> dict:
    """
    0–100 score. Higher = riskier.
    Factors: failed logins, suspicious logins, rapid withdraw after deposit,
    multi-IP, high reject rate.
    """
    score = 0
    reasons = []
    since = timezone.now() - timedelta(days=30)

    fails = LoginHistory.objects.filter(
        user=user, result=LoginHistory.Result.FAILED, created_at__gte=since,
    ).count()
    if fails >= 5:
        score += 15
        reasons.append(f'{fails} failed logins (30d)')
    elif fails >= 2:
        score += 5

    suspicious = LoginHistory.objects.filter(
        user=user, is_suspicious=True, created_at__gte=since,
    ).count()
    if suspicious:
        score += min(25, suspicious * 10)
        reasons.append(f'{suspicious} suspicious logins')

    ips = (
        LoginHistory.objects.filter(user=user, created_at__gte=since)
        .exclude(ip_address=None)
        .values('ip_address')
        .distinct()
        .count()
    )
    if ips >= 5:
        score += 15
        reasons.append(f'{ips} distinct IPs')
    elif ips >= 3:
        score += 8

    rejected_dep = Deposit.objects.filter(user=user, status=Deposit.Status.REJECTED).count()
    total_dep = Deposit.objects.filter(user=user).count() or 1
    if rejected_dep / total_dep >= 0.3 and rejected_dep >= 2:
        score += 20
        reasons.append('High deposit rejection rate')

    # Withdraw soon after deposit
    recent_dep = Deposit.objects.filter(
        user=user, status=Deposit.Status.APPROVED, reviewed_at__gte=since,
    ).order_by('-reviewed_at')[:5]
    for d in recent_dep:
        if not d.reviewed_at:
            continue
        quick = Withdrawal.objects.filter(
            user=user,
            created_at__gte=d.reviewed_at,
            created_at__lte=d.reviewed_at + timedelta(hours=6),
        ).exists()
        if quick:
            score += 15
            reasons.append('Withdrawal within 6h of deposit')
            break

    score = min(100, score)
    level = 'low'
    if score >= 60:
        level = 'high'
    elif score >= 30:
        level = 'medium'

    return {'score': score, 'level': level, 'reasons': reasons}
