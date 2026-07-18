"""Promo code application on deposits."""
from decimal import Decimal

from django.db import transaction
from django.db.models import F

from core.platform_models import PromoCode, PromoRedemption
from core.utils import quantize_amount
from wallets.models import Wallet, WalletLedger


class PromoError(Exception):
    pass


def validate_promo(code: str, user, deposit_amount) -> PromoCode:
    code = (code or '').strip().upper()
    if not code:
        raise PromoError('Enter a promo code')
    promo = PromoCode.objects.filter(code__iexact=code).first()
    if not promo or not promo.is_valid():
        raise PromoError('Invalid or expired promo code')
    deposit_amount = Decimal(str(deposit_amount))
    if deposit_amount < promo.min_deposit:
        raise PromoError(f'Minimum deposit for this code is {promo.min_deposit}')
    used = PromoRedemption.objects.filter(user=user, promo=promo).count()
    if used >= promo.per_user_limit:
        raise PromoError('You already used this promo code')
    return promo


def compute_bonus(promo: PromoCode, deposit_amount) -> Decimal:
    amount = Decimal(str(deposit_amount))
    bonus = Decimal('0')
    if promo.bonus_percent:
        bonus += amount * promo.bonus_percent / Decimal('100')
    if promo.bonus_fixed:
        bonus += promo.bonus_fixed
    return quantize_amount(bonus)


@transaction.atomic
def apply_promo_on_deposit(user, promo: PromoCode, deposit_amount, deposit_id=''):
    bonus = compute_bonus(promo, deposit_amount)
    if bonus <= 0:
        return Decimal('0')
    wallet, _ = Wallet.objects.select_for_update().get_or_create(user=user)
    wallet.credit(bonus)
    WalletLedger.objects.create(
        wallet=wallet,
        entry_type=WalletLedger.EntryType.ADJUSTMENT,
        amount=bonus,
        balance_after=wallet.balance,
        description=f'Promo {promo.code} bonus',
        reference_type='promo',
        reference_id=str(promo.id),
    )
    PromoRedemption.objects.create(
        promo=promo, user=user, deposit_id=str(deposit_id), bonus_amount=bonus,
    )
    PromoCode.objects.filter(pk=promo.pk).update(uses_count=F('uses_count') + 1)
    return bonus
