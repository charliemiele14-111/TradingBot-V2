import os
import sys
from datetime import datetime, timedelta, timezone
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()

headers = {"APCA-API-KEY-ID": KEY_ID, "APCA-API-SECRET-KEY": SECRET}

start = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
url = "https://data.alpaca.markets/v1beta3/crypto/us/bars"

bars = []
page_token = None
first_page = True

while True:
    params = {
        "symbols": "BTC/USD",
        "timeframe": "1Hour",
        "start": start,
        "limit": 1000,
        "sort": "asc",
    }
    if page_token:
        params["page_token"] = page_token

    r = requests.get(url, headers=headers, params=params)
    print(f"Bars status code: {r.status_code}")
    if r.status_code != 200:
        print(r.text[:300])
        sys.exit(1)

    data = r.json()
    if first_page:
        print(f"Raw response start: {r.text[:300]}")
        first_page = False

    bars.extend(data.get("bars", {}).get("BTC/USD", []))
    page_token = data.get("next_page_token")
    if not page_token:
        break

print(f"Bars received: {len(bars)}")

if len(bars) < 51:
    print("Not enough history for the 50-hour average. Stopping.")
    sys.exit(1)

closes = [b["c"] for b in bars]
volumes = [b["v"] for b in bars]

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
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

ema20 = ema(closes, 20)
ema50 = ema(closes, 50)
rsi14 = rsi(closes, 14)
avg_vol20 = sum(volumes[-20:]) / 20
last_vol = volumes[-1]
last_close = closes[-1]

print(f"Latest close: ${last_close:,.2f}")
print(f"20-hour EMA: ${ema20:,.2f}")
print(f"50-hour EMA: ${ema50:,.2f}")
print(f"14-hour RSI: {rsi14:.1f}")
print(f"Latest volume: {last_vol:.4f} vs 20-hour average {avg_vol20:.4f}")
print("Volume is ABOVE average" if last_vol > avg_vol20 else "Volume is BELOW average")
