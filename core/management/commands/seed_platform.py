"""Seed cryptocurrencies, sample investment plans, and optional admin user."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from investments.models import InvestmentPlan
from wallets.models import Cryptocurrency

User = get_user_model()

# usd_price = USD value of 1 unit of that crypto (required for display conversion)
CRYPTOS = [
    {
        'symbol': 'BTC',
        'name': 'Bitcoin',
        'network': Cryptocurrency.Network.BITCOIN,
        'icon': '₿',
        'min_deposit': Decimal('0.0001'),
        'min_withdrawal': Decimal('0.001'),
        'deposit_address': '16LUSj9T99VJMxem4DN3PsgxkdVtkV4ejB',
        'usd_price': Decimal('95000'),
        'sort_order': 1,
    },
    {
        'symbol': 'ETH',
        'name': 'Ethereum',
        'network': Cryptocurrency.Network.ETHEREUM,
        'icon': 'Ξ',
        'min_deposit': Decimal('0.01'),
        'min_withdrawal': Decimal('0.05'),
        'deposit_address': '0x576b6b2a3506c3f207a88119648a5c32836d2bb8',
        'usd_price': Decimal('3500'),
        'sort_order': 2,
    },
    {
        'symbol': 'USDT_TRC20',
        'name': 'USDT (TRC20)',
        'network': Cryptocurrency.Network.TRON,
        'icon': '₮',
        'min_deposit': Decimal('10'),
        'min_withdrawal': Decimal('10'),
        'deposit_address': 'TX3rxziMTWTRQZrzZhTeHBCKLUFehu3R3c',
        'usd_price': Decimal('1'),
        'sort_order': 3,
    },
    {
        'symbol': 'USDT_ERC20',
        'name': 'USDT (ERC20)',
        'network': Cryptocurrency.Network.ETHEREUM,
        'icon': '₮',
        'min_deposit': Decimal('10'),
        'min_withdrawal': Decimal('20'),
        'deposit_address': '0x576b6b2a3506c3f207a88119648a5c32836d2bb8',
        'usd_price': Decimal('1'),
        'sort_order': 4,
    },
    {
        'symbol': 'USDT_BEP20',
        'name': 'USDT (BEP20)',
        'network': Cryptocurrency.Network.BSC,
        'icon': '₮',
        'min_deposit': Decimal('10'),
        'min_withdrawal': Decimal('10'),
        'deposit_address': '0x576b6b2a3506c3f207a88119648a5c32836d2bb8',
        'usd_price': Decimal('1'),
        'sort_order': 5,
    },
    {
        'symbol': 'BNB',
        'name': 'BNB',
        'network': Cryptocurrency.Network.BSC,
        'icon': '◆',
        'min_deposit': Decimal('0.05'),
        'min_withdrawal': Decimal('0.1'),
        'deposit_address': '0x576b6b2a3506c3f207a88119648a5c32836d2bb8',
        'usd_price': Decimal('600'),
        'sort_order': 6,
    },
    {
        'symbol': 'LTC',
        'name': 'Litecoin',
        'network': Cryptocurrency.Network.LITECOIN,
        'icon': 'Ł',
        'min_deposit': Decimal('0.1'),
        'min_withdrawal': Decimal('0.5'),
        'deposit_address': 'LZeJKupiMPyhUjmcyCEZfKjvmoG3cdnQAB',
        'usd_price': Decimal('90'),
        'sort_order': 7,
    },
]

PLANS = [
    {
        'name': 'Starter Yield',
        'description': 'Low-risk daily returns for beginners. Ideal for testing the platform with smaller capital.',
        'short_description': 'Low risk · Daily payouts · Great for beginners',
        'min_deposit': Decimal('50'),
        'max_deposit': Decimal('5000'),
        'duration_days': 7,
        'profit_method': InvestmentPlan.ProfitMethod.PERCENTAGE_OF_PRINCIPAL,
        'return_percent_min': Decimal('3.5'),
        'return_percent_max': Decimal('5.5'),
        'profit_rate_percent': Decimal('0.7'),  # per day
        'payout_frequency': InvestmentPlan.PayoutFrequency.DAILY,
        'risk_level': InvestmentPlan.RiskLevel.LOW,
        'is_featured': True,
        'color': '#0ecb81',
        'icon': 'bi-shield-check',
        'sort_order': 1,
    },
    {
        'name': 'Growth Plus',
        'description': 'Balanced weekly compound growth. Medium risk with competitive admin-configured rates.',
        'short_description': 'Medium risk · Weekly · Balanced returns',
        'min_deposit': Decimal('100'),
        'max_deposit': Decimal('25000'),
        'duration_days': 30,
        'profit_method': InvestmentPlan.ProfitMethod.PERCENTAGE_OF_PRINCIPAL,
        'return_percent_min': Decimal('12'),
        'return_percent_max': Decimal('18'),
        'profit_rate_percent': Decimal('3.5'),  # per week
        'payout_frequency': InvestmentPlan.PayoutFrequency.WEEKLY,
        'risk_level': InvestmentPlan.RiskLevel.MEDIUM,
        'is_featured': True,
        'color': '#f0b90b',
        'icon': 'bi-graph-up-arrow',
        'sort_order': 2,
    },
    {
        'name': 'Alpha Monthly',
        'description': 'Higher-yield monthly plan for experienced investors. Returns principal at maturity.',
        'short_description': 'Higher yield · Monthly · Flexible reinvest',
        'min_deposit': Decimal('500'),
        'max_deposit': Decimal('100000'),
        'duration_days': 90,
        'profit_method': InvestmentPlan.ProfitMethod.PERCENTAGE_OF_PRINCIPAL,
        'return_percent_min': Decimal('25'),
        'return_percent_max': Decimal('40'),
        'profit_rate_percent': Decimal('10'),  # per month
        'payout_frequency': InvestmentPlan.PayoutFrequency.MONTHLY,
        'risk_level': InvestmentPlan.RiskLevel.HIGH,
        'is_featured': False,
        'color': '#f6465d',
        'icon': 'bi-rocket-takeoff',
        'sort_order': 3,
    },
    {
        'name': 'Flex Compound',
        'description': 'Compound interest plan with auto-reinvest. Flexible duration between 14 and 60 days.',
        'short_description': 'Compound · Flexible duration · Auto reinvest',
        'min_deposit': Decimal('200'),
        'max_deposit': Decimal('50000'),
        'duration_days': 30,
        'duration_flexible': True,
        'min_duration_days': 14,
        'max_duration_days': 60,
        'profit_method': InvestmentPlan.ProfitMethod.COMPOUND,
        'return_percent_min': Decimal('8'),
        'return_percent_max': Decimal('22'),
        'profit_rate_percent': Decimal('1.0'),
        'payout_frequency': InvestmentPlan.PayoutFrequency.DAILY,
        'risk_level': InvestmentPlan.RiskLevel.MEDIUM,
        'is_featured': True,
        'allow_auto_reinvest': True,
        'color': '#3b82f6',
        'icon': 'bi-arrow-repeat',
        'sort_order': 4,
    },
]


class Command(BaseCommand):
    help = 'Seed cryptocurrencies and sample investment plans'

    def add_arguments(self, parser):
        parser.add_argument('--quiet', action='store_true')
        parser.add_argument('--admin-email', default='admin@cryptoinvest.local')
        parser.add_argument('--admin-password', default='AdminPass123!')

    def handle(self, *args, **options):
        quiet = options['quiet']
        log = (lambda m: None) if quiet else self.stdout.write

        for data in CRYPTOS:
            obj, created = Cryptocurrency.objects.update_or_create(
                symbol=data['symbol'],
                defaults=data,
            )
            log(self.style.SUCCESS(f"{'Created' if created else 'Updated'} crypto {obj.symbol}"))

        for data in PLANS:
            slug = slugify(data['name'])
            obj, created = InvestmentPlan.objects.update_or_create(
                slug=slug,
                defaults={**data, 'slug': slug, 'status': InvestmentPlan.Status.ACTIVE},
            )
            log(self.style.SUCCESS(f"{'Created' if created else 'Updated'} plan {obj.name}"))

        email = options['admin_email']
        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(
                email=email,
                password=options['admin_password'],
                first_name='Admin',
                email_verified=True,
                is_kyc_verified=True,
            )
            log(self.style.SUCCESS(f'Created superuser {email}'))
        else:
            log(f'Superuser {email} already exists')

        from cms.models import CMSPage, FAQ
        from referrals.models import ReferralProgram
        from core.models import CurrencyRate, SiteConfiguration

        SiteConfiguration.get_solo()
        if not ReferralProgram.objects.exists():
            ReferralProgram.objects.create(name='Standard', commission_percent=5, is_active=True)
            log('Created referral program')

        # rate_to_usd = USD value of 1 unit of that currency
        # UGX: ~3,700 UGX per 1 USD → 1 UGX ≈ 1/3700 USD
        fiat_rates = [
            ('USD', 'US Dollar', Decimal('1'), 'USD'),
            ('UGX', 'Ugandan Shilling', Decimal('1') / Decimal('3700'), 'UGX'),
            ('EUR', 'Euro', Decimal('0.92'), 'EUR'),
            ('GBP', 'British Pound', Decimal('0.79'), 'GBP'),
        ]
        for code, name, rate, symbol in fiat_rates:
            CurrencyRate.objects.update_or_create(
                code=code,
                defaults={
                    'name': name,
                    'rate_to_usd': rate,
                    'symbol': symbol,
                    'is_active': True,
                },
            )
        log('Ensured fiat rates (USD, UGX, EUR, GBP)')

        if not CMSPage.objects.filter(page_type=CMSPage.PageType.TERMS).exists():
            CMSPage.objects.create(
                title='Terms of Service', slug='terms-of-service',
                page_type=CMSPage.PageType.TERMS,
                content='<p>These Terms govern use of the CryptoInvest platform. By registering you agree to our rules for deposits, investments, and withdrawals. This is a demo template — replace with legal counsel-approved text.</p>',
            )
        if not CMSPage.objects.filter(page_type=CMSPage.PageType.PRIVACY).exists():
            CMSPage.objects.create(
                title='Privacy Policy', slug='privacy-policy',
                page_type=CMSPage.PageType.PRIVACY,
                content='<p>We process personal data for account, KYC, and transaction purposes. Contact support for data requests. Replace with your privacy policy.</p>',
            )
        if not FAQ.objects.exists():
            FAQ.objects.bulk_create([
                FAQ(question='How long do deposits take?', answer='Deposits are credited after administrator approval, typically within a few hours.', category='Deposits', sort_order=1),
                FAQ(question='How do withdrawals work?', answer='Submit a withdrawal request. Status moves Pending → Approved → Paid after admin processing.', category='Withdrawals', sort_order=2),
                FAQ(question='How are profits calculated?', answer='Each plan has admin-configured rates and payout frequencies. There are no hard-coded returns.', category='Investments', sort_order=3),
            ])
            log('Created FAQs')

        log(self.style.SUCCESS('Seed complete.'))
