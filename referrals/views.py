"""User-facing referral dashboard, stats, leaderboard."""
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.shortcuts import render
from django.urls import reverse

from referrals.models import ReferralCommission, ReferralProgram

User = get_user_model()


@login_required
def dashboard(request):
    user = request.user
    program = ReferralProgram.get_active()
    referred = user.referrals.all().order_by('-date_joined')
    commissions = ReferralCommission.objects.filter(referrer=user).select_related('referred_user')
    stats = {
        'total_referrals': referred.count(),
        'total_earned': user.referral_earnings,
        'pending': commissions.filter(status=ReferralCommission.Status.PENDING).aggregate(
            t=Sum('amount')
        )['t'] or 0,
        'paid': commissions.filter(status=ReferralCommission.Status.PAID).aggregate(
            t=Sum('amount')
        )['t'] or 0,
        'rate': program.commission_percent if program else 5,
    }
    referral_link = request.build_absolute_uri(
        reverse('accounts:register') + f'?ref={user.referral_code}'
    )
    page = Paginator(commissions, 20).get_page(request.GET.get('page'))
    return render(request, 'referrals/dashboard.html', {
        'stats': stats,
        'referred': referred[:20],
        'page': page,
        'referral_link': referral_link,
        'program': program,
    })


@login_required
def leaderboard(request):
    leaders = (
        User.objects.filter(referral_earnings__gt=0)
        .annotate(ref_count=Count('referrals'))
        .order_by('-referral_earnings')[:50]
    )
    return render(request, 'referrals/leaderboard.html', {'leaders': leaders})
