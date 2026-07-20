"""
Central branded email events for users and staff.

All transactional/marketing emails go through here so templates stay consistent.
Failures are logged and never break money flows.
"""
from __future__ import annotations

import logging
from decimal import Decimal
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger('core')


def _abs(path: str) -> str:
    base = (getattr(settings, 'SITE_URL', '') or '').rstrip('/')
    if not path:
        return base
    if path.startswith('http://') or path.startswith('https://'):
        return path
    if not path.startswith('/'):
        path = '/' + path
    return f'{base}{path}'


def _name(user) -> str:
    if not user:
        return 'there'
    try:
        n = (user.get_full_name() or '').strip()
        if n:
            return n
    except Exception:
        pass
    return getattr(user, 'email', None) or 'there'


def _wants_email(user, kind: str = 'general') -> bool:
    if not user or not getattr(user, 'email', None):
        return False
    if not getattr(user, 'is_active', True):
        return False
    if kind == 'login' and not getattr(user, 'login_alert_emails', True):
        return False
    if kind == 'digest' and not getattr(user, 'weekly_digest_emails', True):
        return False
    if kind in ('promo', 'marketing', 'announcement') and not getattr(user, 'email_alerts', True):
        return False
    return True


def _send(user, *, subject, heading, paragraphs, action_url='', action_label='', badge='', note=''):
    try:
        from core.mail import send_action_email
        return send_action_email(
            user,
            subject=subject,
            heading=heading,
            paragraphs=[p for p in paragraphs if p],
            action_url=action_url,
            action_label=action_label,
            badge=badge,
            secondary_note=note,
            fail_silently=True,
        )
    except Exception:
        logger.exception('email_events send failed user=%s subject=%s', getattr(user, 'email', None), subject)
        return False


def _staff_recipients():
    """Emails for ops digests / large withdraw alerts."""
    User = get_user_model()
    configured = getattr(settings, 'STAFF_ALERT_EMAILS', '') or ''
    if isinstance(configured, str) and configured.strip():
        return [e.strip() for e in configured.split(',') if e.strip()]
    emails = list(
        User.objects.filter(is_active=True)
        .filter(is_staff=True)
        .exclude(email='')
        .values_list('email', flat=True)[:30]
    )
    return emails


def _send_staff(subject: str, heading: str, paragraphs: list, action_url='', action_label='Open staff panel'):
    from core.mail import render_action_email, send_branded_email
    recipients = _staff_recipients()
    if not recipients:
        return 0
    html, plain = render_action_email(
        name='Team',
        heading=heading,
        paragraphs=paragraphs,
        action_url=action_url or _abs('/staff/'),
        action_label=action_label,
        badge='Staff alert',
        subject_line=subject,
    )
    n = 0
    for email in recipients:
        try:
            if send_branded_email(to=email, subject=subject, text_body=plain, html_body=html, fail_silently=True):
                n += 1
        except Exception:
            logger.exception('staff email failed %s', email)
    return n


def site() -> str:
    return getattr(settings, 'SITE_NAME', 'CryptoInvest')


# ---------------------------------------------------------------------------
# Money: deposits / withdrawals
# ---------------------------------------------------------------------------

def email_deposit_approved(deposit, amount_label: str = ''):
    user = deposit.user
    if not _wants_email(user):
        return
    label = amount_label or f'{deposit.credit_amount or deposit.amount}'
    _send(
        user,
        subject=f'Deposit approved · {label}',
        heading='Your deposit was approved',
        badge='Deposit',
        paragraphs=[
            f'Great news — your deposit has been reviewed and credited to your wallet ({label}).',
            'You can invest, withdraw, or track your balance any time from your dashboard.',
        ],
        action_url=_abs('/app/wallet'),
        action_label='View wallet',
    )


def email_deposit_rejected(deposit, reason: str = ''):
    user = deposit.user
    if not _wants_email(user):
        return
    reason = (reason or 'Rejected by administrator').strip()
    _send(
        user,
        subject=f'Deposit not approved · {deposit.amount} {getattr(deposit.cryptocurrency, "symbol", "")}',
        heading='Deposit could not be approved',
        badge='Deposit',
        paragraphs=[
            f'We could not approve your deposit of {deposit.amount} {getattr(deposit.cryptocurrency, "symbol", "")}.',
            f'Reason: {reason}',
            'You can submit a new deposit with a clear transaction hash and screenshot.',
        ],
        action_url=_abs('/app/deposits'),
        action_label='Try again',
        note='If you believe this is a mistake, open a support ticket and include your deposit reference.',
    )


def email_withdrawal_approved(withdrawal, amount_label: str = ''):
    user = withdrawal.user
    if not _wants_email(user):
        return
    label = amount_label or str(withdrawal.amount)
    _send(
        user,
        subject=f'Withdrawal approved · {label}',
        heading='Withdrawal approved',
        badge='Withdrawal',
        paragraphs=[
            f'Your withdrawal of {label} was approved and is being processed for payout.',
            f'Destination: {(withdrawal.wallet_address or "")[:24]}…',
        ],
        action_url=_abs('/app/withdrawals'),
        action_label='Track withdrawal',
    )


def email_withdrawal_paid(withdrawal, amount_label: str = '', tx_hash: str = ''):
    user = withdrawal.user
    if not _wants_email(user):
        return
    label = amount_label or str(withdrawal.amount)
    paras = [
        f'Your withdrawal of {label} has been paid out.',
    ]
    if tx_hash:
        paras.append(f'Transaction hash: {tx_hash}')
    paras.append('Please allow network confirmation time before funds appear in your external wallet.')
    _send(
        user,
        subject=f'Withdrawal paid · {label}',
        heading='Funds sent successfully',
        badge='Withdrawal',
        paragraphs=paras,
        action_url=_abs('/app/withdrawals'),
        action_label='View details',
    )


def email_withdrawal_rejected(withdrawal, amount_label: str = '', reason: str = ''):
    user = withdrawal.user
    if not _wants_email(user):
        return
    label = amount_label or str(withdrawal.amount)
    reason = (reason or 'Rejected by administrator').strip()
    _send(
        user,
        subject=f'Withdrawal rejected · {label}',
        heading='Withdrawal was not completed',
        badge='Withdrawal',
        paragraphs=[
            f'Your withdrawal of {label} was rejected. Locked funds have been released to your available balance.',
            f'Reason: {reason}',
        ],
        action_url=_abs('/app/wallet'),
        action_label='View wallet',
    )


def email_withdrawal_requested(withdrawal, amount_label: str = ''):
    """User confirmation that a withdrawal was submitted."""
    user = withdrawal.user
    if not _wants_email(user):
        return
    label = amount_label or str(withdrawal.amount)
    addr = (withdrawal.wallet_address or '')[:28]
    _send(
        user,
        subject=f'Withdrawal requested · {label}',
        heading='We received your withdrawal request',
        badge='Security',
        paragraphs=[
            f'You requested a withdrawal of {label}.',
            f'To address: {addr}…',
            'Funds are locked until staff approve or reject the request. If this was not you, secure your account immediately.',
        ],
        action_url=_abs('/app/security'),
        action_label='Review security',
        note='Never share OTP codes or passwords with anyone claiming to be support.',
    )
    # Large amount → staff
    try:
        threshold = Decimal(str(getattr(settings, 'LARGE_WITHDRAW_ALERT', 5000)))
        if Decimal(str(withdrawal.amount or 0)) >= threshold:
            email_staff_large_withdrawal(withdrawal, amount_label=label)
    except Exception:
        logger.exception('large withdraw staff alert failed')


def email_staff_large_withdrawal(withdrawal, amount_label: str = ''):
    label = amount_label or str(withdrawal.amount)
    _send_staff(
        subject=f'Large withdrawal · {label} · {withdrawal.user.email}',
        heading='Large withdrawal requires attention',
        paragraphs=[
            f'User: {withdrawal.user.email}',
            f'Amount: {label}',
            f'Address: {withdrawal.wallet_address}',
            f'Status: {withdrawal.status}',
            f'Ref: {withdrawal.id}',
        ],
        action_url=_abs('/app/staff/withdrawals'),
        action_label='Review withdrawals',
    )


# ---------------------------------------------------------------------------
# KYC
# ---------------------------------------------------------------------------

def email_kyc_approved(user):
    if not _wants_email(user):
        return
    _send(
        user,
        subject='Identity verified · KYC approved',
        heading='Your KYC was approved',
        badge='KYC',
        paragraphs=[
            'Your identity verification is complete. You can access features that require KYC.',
            'Thank you for helping us keep the platform secure.',
        ],
        action_url=_abs('/app/plans'),
        action_label='Explore plans',
    )


def email_kyc_rejected(user, reason: str = ''):
    if not _wants_email(user):
        return
    reason = (reason or 'Please resubmit clearer documents.').strip()
    _send(
        user,
        subject='KYC needs attention',
        heading='KYC could not be approved',
        badge='KYC',
        paragraphs=[
            'We could not verify your identity with the documents provided.',
            f'Reason: {reason}',
            'Please upload clear photos of a valid ID and a matching selfie, then resubmit.',
        ],
        action_url=_abs('/app/kyc'),
        action_label='Resubmit KYC',
    )


# ---------------------------------------------------------------------------
# Investments
# ---------------------------------------------------------------------------

def email_investment_created(user, plan_name: str, amount, matures_at, inv_id):
    if not _wants_email(user):
        return
    _send(
        user,
        subject=f'Investment started · {plan_name}',
        heading='Your investment is live',
        badge='Investment',
        paragraphs=[
            f'You invested {amount} in {plan_name}.',
            f'Maturity date: {matures_at}.',
            'Track payouts and performance from your portfolio.',
        ],
        action_url=_abs(f'/app/investments/{inv_id}'),
        action_label='View investment',
    )


def email_profit_credited(user, plan_name: str, profit, inv_id=None, reinvested: bool = False):
    if not _wants_email(user):
        return
    if reinvested:
        heading = 'Profit reinvested'
        body = f'{profit} profit from {plan_name} was automatically reinvested into your principal.'
    else:
        heading = 'Profit credited'
        body = f'{profit} profit from {plan_name} was added to your available balance.'
    _send(
        user,
        subject=f'{heading} · {profit}',
        heading=heading,
        badge='Earnings',
        paragraphs=[body],
        action_url=_abs(f'/app/investments/{inv_id}' if inv_id else '/app/earnings'),
        action_label='View earnings',
    )


def email_investment_matured(user, plan_name: str, amount, total_earned, inv_id):
    if not _wants_email(user):
        return
    _send(
        user,
        subject=f'Investment matured · {plan_name}',
        heading='Your investment has matured',
        badge='Investment',
        paragraphs=[
            f'Your {plan_name} investment has completed.',
            f'Principal returned: {amount}. Total earned: {total_earned}.',
            'Funds are available in your wallet — reinvest to keep growing.',
        ],
        action_url=_abs('/app/plans'),
        action_label='Reinvest now',
    )


# ---------------------------------------------------------------------------
# Security / auth
# ---------------------------------------------------------------------------

def email_new_login(user, *, ip: str = '', method: str = '', user_agent: str = ''):
    if not _wants_email(user, 'login'):
        return
    when = timezone.now().strftime('%Y-%m-%d %H:%M UTC')
    paras = [
        f'A successful sign-in was detected on your {site()} account.',
        f'Time: {when}',
    ]
    if ip:
        paras.append(f'IP: {ip}')
    if method:
        paras.append(f'Method: {method}')
    if user_agent:
        paras.append(f'Device: {user_agent[:120]}')
    paras.append('If this was not you, reset your password and enable two-factor authentication immediately.')
    _send(
        user,
        subject='New login to your account',
        heading='New sign-in detected',
        badge='Security',
        paragraphs=paras,
        action_url=_abs('/app/security'),
        action_label='Secure my account',
        note='We never ask for your password or OTP by email or chat.',
    )


def email_password_changed(user):
    if not _wants_email(user):
        return
    _send(
        user,
        subject='Your password was changed',
        heading='Password updated',
        badge='Security',
        paragraphs=[
            'Your account password was changed successfully.',
            'If you did not make this change, reset your password now and contact support.',
        ],
        action_url=_abs('/accounts/password-reset/'),
        action_label='Reset password',
    )


def email_2fa_enabled(user):
    if not _wants_email(user):
        return
    _send(
        user,
        subject='Two-factor authentication enabled',
        heading='2FA is now on',
        badge='Security',
        paragraphs=[
            'Authenticator app 2FA is active on your account. Sign-ins will require a code from your app.',
            'Keep backup codes safe. You can still use email OTP as a fallback when available.',
        ],
        action_url=_abs('/app/security'),
        action_label='Security settings',
    )


def email_2fa_disabled(user):
    if not _wants_email(user):
        return
    _send(
        user,
        subject='Two-factor authentication disabled',
        heading='2FA was turned off',
        badge='Security',
        paragraphs=[
            'Authenticator 2FA was disabled on your account.',
            'If this was not you, reset your password and re-enable 2FA immediately.',
        ],
        action_url=_abs('/app/security'),
        action_label='Secure my account',
    )


# ---------------------------------------------------------------------------
# Support / VIP / broadcast
# ---------------------------------------------------------------------------

def email_support_reply(user, ticket, preview: str):
    if not _wants_email(user, 'promo'):
        return
    _send(
        user,
        subject=f'Support replied · {ticket.subject[:60]}',
        heading='You have a new support message',
        badge='Support',
        paragraphs=[
            f'Ticket: {ticket.subject}',
            f'Preview: {preview}',
        ],
        action_url=_abs(f'/app/support/{ticket.id}'),
        action_label='Open conversation',
    )


def email_vip_upgrade(user, tier_name: str):
    if not _wants_email(user):
        return
    _send(
        user,
        subject=f'VIP upgrade · {tier_name}',
        heading=f'Welcome to {tier_name}',
        badge='VIP',
        paragraphs=[
            f'Congratulations — you reached the {tier_name} VIP tier.',
            'Enjoy enhanced benefits, priority support, and exclusive plans where available.',
        ],
        action_url=_abs('/app/vip'),
        action_label='View VIP perks',
    )


def email_broadcast(user, title: str, message: str, action_url: str = '', action_label: str = 'Open app'):
    if not _wants_email(user, 'announcement'):
        return
    url = action_url or _abs('/app/announcements')
    _send(
        user,
        subject=title,
        heading=title,
        badge='Announcement',
        paragraphs=[message],
        action_url=url,
        action_label=action_label,
    )


def email_staff_to_user(user, subject: str, message: str, action_url: str = '', action_label: str = 'Open platform'):
    """One-off staff-composed email to a single user."""
    if not user or not user.email:
        return False
    return _send(
        user,
        subject=subject,
        heading=subject,
        badge='Message from support',
        paragraphs=[message],
        action_url=action_url or _abs('/app/support'),
        action_label=action_label,
    )


# ---------------------------------------------------------------------------
# Lifecycle: welcome / nudges / win-back / statements
# ---------------------------------------------------------------------------

def email_welcome(user, day: int = 0):
    if not _wants_email(user):
        return
    if day <= 0:
        _send(
            user,
            subject=f'Welcome to {site()}',
            heading=f'Welcome aboard, {_name(user).split()[0]}',
            badge='Welcome',
            paragraphs=[
                f'Thanks for joining {site()}. You’re minutes away from your first investment.',
                'Next steps: verify your email, complete KYC if required, and make your first deposit.',
            ],
            action_url=_abs('/app/onboarding'),
            action_label='Complete setup',
        )
    elif day == 1:
        _send(
            user,
            subject='Day 1 · Secure your account',
            heading='Protect your portfolio',
            badge='Getting started',
            paragraphs=[
                'Enable two-factor authentication and confirm your email so only you can access funds.',
                'Strong security is the foundation of smart investing.',
            ],
            action_url=_abs('/app/security'),
            action_label='Open security',
        )
    else:
        _send(
            user,
            subject='Ready for your first deposit?',
            heading='Fund your wallet',
            badge='Getting started',
            paragraphs=[
                'Deposit multi-chain crypto, wait for approval, then pick a plan that matches your goals.',
                'Need help? Our support team is in-app and ready.',
            ],
            action_url=_abs('/app/deposits'),
            action_label='Deposit now',
        )


def email_stale_deposit_nudge(deposit):
    user = deposit.user
    if not _wants_email(user):
        return
    _send(
        user,
        subject='Still waiting on your deposit?',
        heading='Deposit pending confirmation',
        badge='Reminder',
        paragraphs=[
            f'Your deposit of {deposit.amount} {getattr(deposit.cryptocurrency, "symbol", "")} is still pending.',
            'If you already sent funds, ensure the transaction hash and screenshot are correct. Staff will review once received.',
            'If you have not sent funds yet, complete the transfer to the platform address shown in the app.',
        ],
        action_url=_abs('/app/deposits'),
        action_label='View deposit',
    )


def email_winback(user, days_inactive: int = 14):
    if not _wants_email(user, 'marketing'):
        return
    _send(
        user,
        subject=f'We miss you at {site()}',
        heading='Your portfolio is waiting',
        badge='Come back',
        paragraphs=[
            f'It’s been about {days_inactive} days since your last visit.',
            'Check live markets, active investments, and new plans tailored to your goals.',
        ],
        action_url=_abs('/app/dashboard'),
        action_label='Return to dashboard',
    )


def email_statement_ready(user, period_label: str, action_url: str = ''):
    if not _wants_email(user, 'digest'):
        return
    _send(
        user,
        subject=f'Statement ready · {period_label}',
        heading='Your statement is ready',
        badge='Documents',
        paragraphs=[
            f'Your {period_label} account statement is available to download or review in the app.',
        ],
        action_url=action_url or _abs('/app/statements'),
        action_label='View statements',
    )


def email_export_ready(staff_user, kind: str, note: str = ''):
    if not staff_user or not staff_user.email:
        return
    _send(
        staff_user,
        subject=f'Export ready · {kind}',
        heading='Your export is ready',
        badge='Staff',
        paragraphs=[
            f'The {kind} export you requested is ready.',
            note or 'Download it from the staff panel export tools if it was generated in-browser, or check your last download.',
        ],
        action_url=_abs('/app/staff'),
        action_label='Open staff panel',
    )


# ---------------------------------------------------------------------------
# Staff digests & SLA
# ---------------------------------------------------------------------------

def email_staff_ops_digest():
    from accounts.models import KYCDocument
    from support.models import SupportTicket
    from transactions.models import Deposit, Withdrawal

    pending_d = Deposit.objects.filter(status__in=['pending', 'waiting_confirmation']).count()
    pending_w = Withdrawal.objects.filter(status__in=['pending', 'approved', 'processing']).count()
    pending_k = KYCDocument.objects.filter(status__in=['pending', 'under_review']).count()
    open_t = SupportTicket.objects.exclude(status__in=['closed', 'resolved']).count() if hasattr(SupportTicket, 'status') else SupportTicket.objects.count()
    users_today = get_user_model().objects.filter(date_joined__date=timezone.now().date()).count()

    return _send_staff(
        subject=f'{site()} ops digest · {timezone.now().date()}',
        heading='Daily operations digest',
        paragraphs=[
            f'Pending deposits: {pending_d}',
            f'Open withdrawals: {pending_w}',
            f'KYC queue: {pending_k}',
            f'Support tickets: {open_t}',
            f'New users today: {users_today}',
            'Review queues in the staff panel to keep SLAs healthy.',
        ],
        action_url=_abs('/app/staff'),
        action_label='Open staff dashboard',
    )


def email_withdrawal_sla_breach(withdrawal):
    user = withdrawal.user
    # Staff first
    _send_staff(
        subject=f'SLA breach · withdrawal {withdrawal.id}',
        heading='Withdrawal SLA overdue',
        paragraphs=[
            f'User: {user.email}',
            f'Amount: {withdrawal.amount}',
            f'Status: {withdrawal.status}',
            f'SLA deadline: {withdrawal.sla_deadline}',
        ],
        action_url=_abs('/app/staff/withdrawals'),
        action_label='Process withdrawals',
    )
    # Soft user update
    if _wants_email(user):
        _send(
            user,
            subject='Update on your withdrawal',
            heading='We’re still processing your withdrawal',
            badge='Update',
            paragraphs=[
                'Your withdrawal is taking longer than usual. Our team has been notified and is prioritizing your request.',
                'No action is needed from you right now. We will email you when it is paid or if we need more information.',
            ],
            action_url=_abs('/app/withdrawals'),
            action_label='View status',
        )


def email_weekly_digest_html(user, available, invested, profit_week):
    if not _wants_email(user, 'digest'):
        return False
    return _send(
        user,
        subject=f'Your weekly {site()} digest',
        heading='Weekly portfolio summary',
        badge='Digest',
        paragraphs=[
            f'Available balance: {available}',
            f'Total invested: {invested}',
            f'Profit this week: {profit_week}',
            'Open the app for charts, statements, and reinvestment options.',
        ],
        action_url=_abs('/app/portfolio'),
        action_label='View performance',
    )
