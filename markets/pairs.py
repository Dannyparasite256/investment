"""
Forex & market symbols for TradingView charts.

TradingView FX format: FX:EURUSD
Crypto (extra): BINANCE:BTCUSDT
"""

# Chart type styles used by TradingView Advanced Chart widget
CHART_STYLES = [
    {'id': '1', 'label': 'Candlesticks', 'icon': 'bi-bar-chart-fill'},
    {'id': '0', 'label': 'Bars', 'icon': 'bi-bar-chart-steps'},
    {'id': '9', 'label': 'Hollow candles', 'icon': 'bi-grid-3x3'},
    {'id': '8', 'label': 'Heikin Ashi', 'icon': 'bi-graph-up'},
    {'id': '2', 'label': 'Line', 'icon': 'bi-graph-up-arrow'},
    {'id': '3', 'label': 'Area', 'icon': 'bi-activity'},
]

INTERVALS = [
    {'id': '1', 'label': '1m'},
    {'id': '5', 'label': '5m'},
    {'id': '15', 'label': '15m'},
    {'id': '30', 'label': '30m'},
    {'id': '60', 'label': '1H'},
    {'id': '240', 'label': '4H'},
    {'id': 'D', 'label': '1D'},
    {'id': 'W', 'label': '1W'},
]

# Major, minor, and exotic forex pairs (TradingView FX: symbols)
FOREX_CATEGORIES = {
    'majors': {
        'label': 'Major pairs',
        'description': 'Most liquid FX markets',
        'pairs': [
            {'symbol': 'FX:EURUSD', 'base': 'EUR', 'quote': 'USD', 'name': 'Euro / US Dollar'},
            {'symbol': 'FX:GBPUSD', 'base': 'GBP', 'quote': 'USD', 'name': 'British Pound / US Dollar'},
            {'symbol': 'FX:USDJPY', 'base': 'USD', 'quote': 'JPY', 'name': 'US Dollar / Japanese Yen'},
            {'symbol': 'FX:USDCHF', 'base': 'USD', 'quote': 'CHF', 'name': 'US Dollar / Swiss Franc'},
            {'symbol': 'FX:AUDUSD', 'base': 'AUD', 'quote': 'USD', 'name': 'Australian Dollar / US Dollar'},
            {'symbol': 'FX:USDCAD', 'base': 'USD', 'quote': 'CAD', 'name': 'US Dollar / Canadian Dollar'},
            {'symbol': 'FX:NZDUSD', 'base': 'NZD', 'quote': 'USD', 'name': 'New Zealand Dollar / US Dollar'},
        ],
    },
    'crosses': {
        'label': 'Cross pairs',
        'description': 'Non-USD major crosses',
        'pairs': [
            {'symbol': 'FX:EURGBP', 'base': 'EUR', 'quote': 'GBP', 'name': 'Euro / British Pound'},
            {'symbol': 'FX:EURJPY', 'base': 'EUR', 'quote': 'JPY', 'name': 'Euro / Japanese Yen'},
            {'symbol': 'FX:GBPJPY', 'base': 'GBP', 'quote': 'JPY', 'name': 'British Pound / Japanese Yen'},
            {'symbol': 'FX:EURCHF', 'base': 'EUR', 'quote': 'CHF', 'name': 'Euro / Swiss Franc'},
            {'symbol': 'FX:EURAUD', 'base': 'EUR', 'quote': 'AUD', 'name': 'Euro / Australian Dollar'},
            {'symbol': 'FX:EURCAD', 'base': 'EUR', 'quote': 'CAD', 'name': 'Euro / Canadian Dollar'},
            {'symbol': 'FX:GBPCHF', 'base': 'GBP', 'quote': 'CHF', 'name': 'British Pound / Swiss Franc'},
            {'symbol': 'FX:AUDJPY', 'base': 'AUD', 'quote': 'JPY', 'name': 'Australian Dollar / Japanese Yen'},
            {'symbol': 'FX:CADJPY', 'base': 'CAD', 'quote': 'JPY', 'name': 'Canadian Dollar / Japanese Yen'},
            {'symbol': 'FX:CHFJPY', 'base': 'CHF', 'quote': 'JPY', 'name': 'Swiss Franc / Japanese Yen'},
            {'symbol': 'FX:AUDNZD', 'base': 'AUD', 'quote': 'NZD', 'name': 'Australian Dollar / NZ Dollar'},
            {'symbol': 'FX:GBPAUD', 'base': 'GBP', 'quote': 'AUD', 'name': 'British Pound / Australian Dollar'},
        ],
    },
    'exotics': {
        'label': 'Exotic pairs',
        'description': 'Emerging & specialty FX',
        'pairs': [
            {'symbol': 'FX:USDTRY', 'base': 'USD', 'quote': 'TRY', 'name': 'US Dollar / Turkish Lira'},
            {'symbol': 'FX:USDZAR', 'base': 'USD', 'quote': 'ZAR', 'name': 'US Dollar / South African Rand'},
            {'symbol': 'FX:USDMXN', 'base': 'USD', 'quote': 'MXN', 'name': 'US Dollar / Mexican Peso'},
            {'symbol': 'FX:USDSGD', 'base': 'USD', 'quote': 'SGD', 'name': 'US Dollar / Singapore Dollar'},
            {'symbol': 'FX:USDHKD', 'base': 'USD', 'quote': 'HKD', 'name': 'US Dollar / Hong Kong Dollar'},
            {'symbol': 'FX:USDSEK', 'base': 'USD', 'quote': 'SEK', 'name': 'US Dollar / Swedish Krona'},
            {'symbol': 'FX:USDNOK', 'base': 'USD', 'quote': 'NOK', 'name': 'US Dollar / Norwegian Krone'},
            {'symbol': 'FX:USDDKK', 'base': 'USD', 'quote': 'DKK', 'name': 'US Dollar / Danish Krone'},
            {'symbol': 'FX:USDPLN', 'base': 'USD', 'quote': 'PLN', 'name': 'US Dollar / Polish Zloty'},
            {'symbol': 'FX:USDCNH', 'base': 'USD', 'quote': 'CNH', 'name': 'US Dollar / Chinese Yuan (offshore)'},
            {'symbol': 'FX:USDINR', 'base': 'USD', 'quote': 'INR', 'name': 'US Dollar / Indian Rupee'},
            {'symbol': 'FX:USDBRL', 'base': 'USD', 'quote': 'BRL', 'name': 'US Dollar / Brazilian Real'},
            {'symbol': 'FX:EURTRY', 'base': 'EUR', 'quote': 'TRY', 'name': 'Euro / Turkish Lira'},
            {'symbol': 'FX:EURPLN', 'base': 'EUR', 'quote': 'PLN', 'name': 'Euro / Polish Zloty'},
            {'symbol': 'FX:GBPZAR', 'base': 'GBP', 'quote': 'ZAR', 'name': 'British Pound / South African Rand'},
            {'symbol': 'FX:AUDCAD', 'base': 'AUD', 'quote': 'CAD', 'name': 'Australian Dollar / Canadian Dollar'},
        ],
    },
    'metals': {
        'label': 'Metals (FX-linked)',
        'description': 'Precious metals vs USD',
        'pairs': [
            {'symbol': 'TVC:GOLD', 'base': 'XAU', 'quote': 'USD', 'name': 'Gold / US Dollar'},
            {'symbol': 'TVC:SILVER', 'base': 'XAG', 'quote': 'USD', 'name': 'Silver / US Dollar'},
            {'symbol': 'FX:XAUUSD', 'base': 'XAU', 'quote': 'USD', 'name': 'Gold Spot / USD'},
            {'symbol': 'FX:XAGUSD', 'base': 'XAG', 'quote': 'USD', 'name': 'Silver Spot / USD'},
        ],
    },
    'crypto': {
        'label': 'Crypto (spot)',
        'description': 'Major digital assets',
        'pairs': [
            {'symbol': 'BINANCE:BTCUSDT', 'base': 'BTC', 'quote': 'USDT', 'name': 'Bitcoin / Tether'},
            {'symbol': 'BINANCE:ETHUSDT', 'base': 'ETH', 'quote': 'USDT', 'name': 'Ethereum / Tether'},
            {'symbol': 'BINANCE:BNBUSDT', 'base': 'BNB', 'quote': 'USDT', 'name': 'BNB / Tether'},
            {'symbol': 'BINANCE:SOLUSDT', 'base': 'SOL', 'quote': 'USDT', 'name': 'Solana / Tether'},
            {'symbol': 'BINANCE:XRPUSDT', 'base': 'XRP', 'quote': 'USDT', 'name': 'XRP / Tether'},
            {'symbol': 'BINANCE:LTCUSDT', 'base': 'LTC', 'quote': 'USDT', 'name': 'Litecoin / Tether'},
        ],
    },
}


def all_pairs():
    """Flat list of all pairs with category key attached."""
    items = []
    for cat_key, cat in FOREX_CATEGORIES.items():
        for p in cat['pairs']:
            items.append({**p, 'category': cat_key, 'category_label': cat['label']})
    return items


def find_pair(symbol: str):
    symbol = (symbol or '').strip()
    for p in all_pairs():
        if p['symbol'] == symbol:
            return p
    return None


def default_pair():
    return FOREX_CATEGORIES['majors']['pairs'][0]
