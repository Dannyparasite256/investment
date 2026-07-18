"""Pull free live prices into the database.

  python manage.py update_prices
  python manage.py update_prices --force
"""
from django.core.management.base import BaseCommand

from core.price_feed import refresh_all_prices


class Command(BaseCommand):
    help = 'Update crypto + fiat rates from free public APIs (CoinGecko/Binance + open.er-api)'

    def add_arguments(self, parser):
        parser.add_argument('--force', action='store_true', help='Ignore cache and fetch now')

    def handle(self, *args, **options):
        result = refresh_all_prices(force=options['force'])
        if result.get('skipped'):
            self.stdout.write(self.style.WARNING('Skipped (still fresh in cache). Use --force to refetch.'))
            return
        self.stdout.write(self.style.SUCCESS(
            f"OK source={result.get('crypto_source')} "
            f"crypto_rows={result.get('crypto_updated')} "
            f"fiat_rows={result.get('fiat_updated')}"
        ))
        if result.get('prices'):
            for k, v in result['prices'].items():
                self.stdout.write(f'  {k}: ${v}')
        if result.get('fiat'):
            for k, v in result['fiat'].items():
                self.stdout.write(f'  {k} rate_to_usd={v}')
        if result.get('errors'):
            for e in result['errors']:
                self.stdout.write(self.style.WARNING(f'  warn: {e}'))
