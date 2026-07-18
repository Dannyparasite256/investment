"""
Set crypto USD prices and optionally re-credit approved deposits that used rate=1.

Example on PythonAnywhere:
  python manage.py fix_crypto_prices
  python manage.py fix_crypto_prices --recredit-deposits
"""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from wallets.models import Cryptocurrency, Wallet, WalletLedger


# Reference display prices (admin can change anytime in Django admin)
DEFAULT_PRICES = {
    'BTC': Decimal('95000'),
    'ETH': Decimal('3500'),
    'USDT_TRC20': Decimal('1'),
    'USDT_ERC20': Decimal('1'),
    'USDT_BEP20': Decimal('1'),
    'BNB': Decimal('600'),
    'LTC': Decimal('90'),
}


class Command(BaseCommand):
    help = 'Fix cryptocurrency usd_price values and optionally re-credit deposits approved at wrong rate'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recredit-deposits',
            action='store_true',
            help='Recalculate approved deposits that were credited with rate ~1 and top up wallets',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would change without saving',
        )

    def handle(self, *args, **options):
        dry = options['dry_run']
        recredit = options['recredit_deposits']

        for symbol, price in DEFAULT_PRICES.items():
            crypto = Cryptocurrency.objects.filter(symbol__iexact=symbol).first()
            if not crypto:
                self.stdout.write(self.style.WARNING(f'Skip missing crypto {symbol}'))
                continue
            old = crypto.usd_price
            self.stdout.write(f'{symbol}: {old} → {price}')
            if not dry:
                crypto.usd_price = price
                crypto.save(update_fields=['usd_price'])

        # Any other active crypto still at 0 stays untouched
        bad = Cryptocurrency.objects.filter(is_active=True, usd_price__lte=1).exclude(
            symbol__in=list(DEFAULT_PRICES.keys())
        )
        for c in bad:
            self.stdout.write(self.style.WARNING(
                f'{c.symbol} still has usd_price=1 — set it in /admin/ if needed'
            ))

        if not recredit:
            self.stdout.write(self.style.SUCCESS(
                'Prices updated. Run with --recredit-deposits if old approvals used rate=1.'
            ))
            return

        from transactions.models import Deposit

        qs = Deposit.objects.filter(status=Deposit.Status.APPROVED).select_related(
            'cryptocurrency', 'user'
        )
        fixed = 0
        for dep in qs:
            price_now = Decimal(str(dep.cryptocurrency.usd_price or 0))
            if price_now <= 0:
                continue
            correct = (Decimal(str(dep.amount)) - Decimal(str(dep.fee or 0))) * price_now
            correct = correct.quantize(Decimal('0.00000001'))
            old_credit = Decimal(str(dep.credit_amount or 0))
            # Only fix when old rate was ~1 (credit ≈ crypto amount) or rate_usd ~1
            rate_was_bad = (
                dep.rate_usd is None
                or Decimal(str(dep.rate_usd)) <= Decimal('1.01')
                or abs(old_credit - Decimal(str(dep.amount))) < Decimal('0.0001')
            )
            if not rate_was_bad:
                continue
            if correct <= old_credit:
                continue
            delta = correct - old_credit
            self.stdout.write(
                f'Deposit {dep.id} user={dep.user.email}: '
                f'{dep.amount} {dep.cryptocurrency.symbol} '
                f'credit {old_credit} → {correct} (+{delta})'
            )
            if dry:
                continue
            with transaction.atomic():
                wallet, _ = Wallet.objects.get_or_create(user=dep.user)
                wallet.credit(delta, update_deposited=True)
                WalletLedger.objects.create(
                    wallet=wallet,
                    entry_type=WalletLedger.EntryType.DEPOSIT,
                    amount=delta,
                    balance_after=wallet.balance,
                    description=(
                        f'Price correction for deposit {dep.id}: '
                        f'{dep.amount} {dep.cryptocurrency.symbol} @ ${price_now}'
                    ),
                    reference_type='deposit_correction',
                    reference_id=str(dep.id),
                )
                dep.credit_amount = correct
                dep.rate_usd = price_now
                dep.save(update_fields=['credit_amount', 'rate_usd'])
            fixed += 1

        self.stdout.write(self.style.SUCCESS(
            f'Recredited {fixed} deposit(s).' if not dry else f'Dry-run: would recredit {fixed}+ rows shown above.'
        ))
