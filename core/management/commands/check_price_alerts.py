"""Evaluate price alerts and email users when targets are hit."""
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from accounts.social_features import send_price_alert_email
from core.platform_models import PriceAlert
from notifications.models import Notification, notify


class Command(BaseCommand):
    help = 'Check active price alerts against last known prices and notify users'

    def handle(self, *args, **options):
        # Prefer prices stored on alerts / market feed when available
        prices = {}
        try:
            from core.price_feed import get_ticker_snapshot
            snap = get_ticker_snapshot() or {}
            for k, v in snap.items():
                try:
                    prices[str(k).upper()] = Decimal(str(v))
                except Exception:
                    pass
        except Exception:
            pass

        hit = 0
        for alert in PriceAlert.objects.filter(is_active=True, triggered_at__isnull=True).select_related('user'):
            sym = (alert.symbol or '').upper()
            # Allow FX:EURUSD style keys
            price = prices.get(sym) or prices.get(sym.replace('FX:', ''))
            if price is None and alert.last_price is not None:
                price = Decimal(str(alert.last_price))
            if price is None:
                continue
            alert.last_price = price
            target = Decimal(str(alert.target_price or 0))
            triggered = False
            if alert.direction == 'above' and price >= target:
                triggered = True
            elif alert.direction == 'below' and price <= target:
                triggered = True
            if triggered:
                alert.triggered_at = timezone.now()
                alert.is_active = False
                alert.save(update_fields=['last_price', 'triggered_at', 'is_active', 'updated_at'])
                notify(
                    alert.user,
                    f'Price alert: {alert.symbol}',
                    f'{alert.symbol} is {price} ({alert.direction} {target}).',
                    level=Notification.Level.SUCCESS,
                    category=Notification.Category.SYSTEM,
                    link='/alerts/',
                )
                send_price_alert_email(alert.user, alert, price)
                hit += 1
            else:
                alert.save(update_fields=['last_price', 'updated_at'])
        self.stdout.write(self.style.SUCCESS(f'Triggered {hit} price alerts'))
