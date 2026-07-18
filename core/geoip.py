"""
Free IP geolocation for access location + timezone.
Primary: ipwho.is (HTTPS, no key). Fallback: ip-api.com (HTTP).
Results cached to respect free-tier limits.
"""
from __future__ import annotations

import json
import logging
import urllib.request
from typing import Any

from django.core.cache import cache

logger = logging.getLogger('core.geoip')

CACHE_TTL = 60 * 60 * 24  # 24h per IP


def _is_private(ip: str | None) -> bool:
    if not ip:
        return True
    ip = ip.strip()
    if ip in ('127.0.0.1', '::1', 'localhost'):
        return True
    if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
        return True
    return False


def _http_json(url: str, timeout: int = 6) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'CryptoInvestGeo/1.0', 'Accept': 'application/json'},
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8', errors='replace'))


def lookup_ip(ip: str | None) -> dict[str, str]:
    """
    Return {country, city, region, timezone, isp, ip} for a public IP.
    Empty strings on failure / private IP.
    """
    empty = {'country': '', 'city': '', 'region': '', 'timezone': '', 'isp': '', 'ip': ip or ''}
    if not ip or _is_private(ip):
        return {**empty, 'country': 'Local', 'city': 'Private network', 'timezone': ''}

    cache_key = f'geoip:v1:{ip}'
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    result = dict(empty)
    # 1) ipwho.is — free HTTPS
    try:
        data = _http_json(f'https://ipwho.is/{ip}')
        if data.get('success') is not False and (data.get('country') or data.get('city')):
            result = {
                'ip': ip,
                'country': (data.get('country') or '')[:100],
                'city': (data.get('city') or '')[:100],
                'region': (data.get('region') or data.get('regionName') or '')[:100],
                'timezone': (
                    (data.get('timezone') or {}).get('id')
                    if isinstance(data.get('timezone'), dict)
                    else (data.get('timezone') or '')
                )[:64],
                'isp': (data.get('connection', {}) or {}).get('isp', '')[:120]
                if isinstance(data.get('connection'), dict)
                else (data.get('isp') or '')[:120],
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result
    except Exception as exc:
        logger.debug('ipwho.is failed for %s: %s', ip, exc)

    # 2) ip-api.com — free HTTP (may work where allowed)
    try:
        data = _http_json(
            f'http://ip-api.com/json/{ip}?fields=status,country,regionName,city,timezone,isp,query'
        )
        if data.get('status') == 'success':
            result = {
                'ip': ip,
                'country': (data.get('country') or '')[:100],
                'city': (data.get('city') or '')[:100],
                'region': (data.get('regionName') or '')[:100],
                'timezone': (data.get('timezone') or '')[:64],
                'isp': (data.get('isp') or '')[:120],
            }
            cache.set(cache_key, result, CACHE_TTL)
            return result
    except Exception as exc:
        logger.debug('ip-api failed for %s: %s', ip, exc)

    cache.set(cache_key, result, 300)  # short cache on miss
    return result


def format_location(geo: dict | None) -> str:
    if not geo:
        return ''
    parts = [p for p in [geo.get('city'), geo.get('region'), geo.get('country')] if p]
    # de-dupe adjacent
    cleaned = []
    for p in parts:
        if not cleaned or cleaned[-1].lower() != p.lower():
            cleaned.append(p)
    return ', '.join(cleaned)
