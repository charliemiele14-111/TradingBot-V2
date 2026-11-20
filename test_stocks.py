import os
import sys
from datetime import datetime, timedelta, timezone
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()
headers = {"APCA-API-KEY-ID": KEY_ID, "APCA-API-SECRET-KEY": SECRET}

STOCKS = ["NVDA", "TSLA", "AMZN", "GOOGL", "MSTR", "PLTR", "AMD", "SOFI", "NFLX", "SPY"]
CRYPTO = ["BTC/USD"]
STOCK_URL = "https://data.alpaca.markets/v2/stocks/bars"
CRYPTO_URL = "https://data.alpaca.markets/v1beta3/crypto/us/bars"

# Temporary test switch. Set to False once the test works.
FORCE_STOCKS = True

def check_market_open():
    r = requests.get("https://paper-api.alpaca.markets/v2/clock", headers=headers)
    if r.status_code != 200:
        print(f"Clock error {r.status_code}: {r.text[:200]}")
        sys.exit(1)
    return r.json()["is_open"]

def fetch_bars(url, symbols, days, extra=None):
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {s: [] for s in symbols}
    page_token = None
    while True:
        params = {"symbols": ",".join(symbols), "timeframe": "1Hour",
                  "start": start, "limit": 10000, "sort": "asc"}
        if extra:
            params.update(extra)
        if page_token:
            params["page_token"] = page_token
        r = requests.get(url, headers=headers, params=params)
        if r.status_code != 200:
            print(f"Data error {r.status_code}: {r.text[:200]}")
            sys.exit(1)
        data = r.json()
        for sym, bars in data.get("bars", {}).items():
            result[sym].extend(bars)
        page_token = data.get("next_page_token")
        if not page_token:
            break
    return result

def ema(values, period):
    k = 2 / (period + 1)
    result = sum(values[:period]) / period
    for v in values[period:]:
        result = v * k + result * (1 - k)
    return result

def rsi(values, period=14):
    gains, losses = [], []
    for i in range(1, len(values)):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
    if avg_loss == 0:
        return 100.0
    return 100 - (100 / (1 + avg_gain / avg_loss))

def to_4h(bars):
    candles = []
    n = len(bars)
    for i in range(n % 4, n, 4):
        chunk = bars[i:i + 4]
        candles.append({"c": chunk[-1]["c"], "v": sum(b["v"] for b in chunk)})
    return candles

def summarize(name, bars):
    if len(bars) < 51:
        print(f"{name}: not enough data ({len(bars)} hourly bars)")
        return
    closes = [b["c"] for b in bars]
    vols = [b["v"] for b in bars]
    avg_vol = sum(vols[-20:]) / 20
    c4 = [c["c"] for c in to_4h(bars)]
    trend_4h = "4H: not enough data"
    if len(c4) >= 51:
        trend_4h = f"4H EMA20 {ema(c4, 20):,.2f} / EMA50 {ema(c4, 50):,.2f}"
    print(
        f"{name} | price {closes[-1]:,.2f} | "
        f"1H EMA20 {ema(closes, 20):,.2f} / EMA50 {ema(closes, 50):,.2f} | "
        f"{trend_4h} | RSI {rsi(closes):.1f} | "
        f"volume {'above' if vols[-1] > avg_vol else 'below'} average"
    )

market_open = check_market_open()
print(f"Stock market open right now: {market_open}")

crypto = fetch_bars(CRYPTO_URL, CRYPTO, 60)
for sym in CRYPTO:
    summarize(sym, crypto[sym])

if market_open or FORCE_STOCKS:
    stocks = fetch_bars(STOCK_URL, STOCKS, 60, extra={"feed": "iex"})
    for sym in STOCKS:
        summarize(sym, stocks[sym])
else:
    print("Market closed, so stock data was skipped.")
  
