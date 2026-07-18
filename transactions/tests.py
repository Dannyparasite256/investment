from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from transactions.models import Deposit, Withdrawal
from wallets.models import Cryptocurrency, Wallet

User = get_user_model()


class WithdrawalWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email='admin@test.com', password='AdminPass123!')
        self.user = User.objects.create_user(email='u@test.com', password='UserPass123!')
        self.wallet = Wallet.objects.get(user=self.user)
        self.wallet.credit(Decimal('1000'), update_deposited=True)
        self.crypto = Cryptocurrency.objects.create(
            symbol='USDT_T', name='USDT', network='TRC20',
            deposit_address='Txxx', min_withdrawal=Decimal('10'),
        )

    def test_pending_approve_paid(self):
        w = Withdrawal.objects.create(
            user=self.user, cryptocurrency=self.crypto,
            amount=Decimal('100'), wallet_address='Tdest', fee=Decimal('1'),
        )
        self.wallet.lock_funds(Decimal('100'))
        w.funds_locked = True
        w.save()
        w.approve(self.admin)
        self.assertEqual(w.status, Withdrawal.Status.APPROVED)
        w.mark_paid(self.admin, tx_hash='0xabc')
        self.assertEqual(w.status, Withdrawal.Status.PAID)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, Decimal('900'))

    def test_deposit_approve_credits(self):
        d = Deposit.objects.create(
            user=self.user, cryptocurrency=self.crypto,
            amount=Decimal('50'), transaction_hash='hash12345678',
        )
        before = self.wallet.balance
        d.approve(self.admin)
        self.wallet.refresh_from_db()
        self.assertEqual(self.wallet.balance, before + Decimal('50'))
        self.assertEqual(d.status, Deposit.Status.APPROVED)
