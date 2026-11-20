import os
import sys
import json
import re
from datetime import datetime, timedelta, timezone
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
headers = {"APCA-API-KEY-ID": KEY_ID, "APCA-API-SECRET-KEY": SECRET}

PAPER_URL = "https://paper-api.alpaca.markets"
DATA_URL = "https://data.alpaca.markets"
STOCKS = ["NVDA", "TSLA", "AMZN", "GOOGL", "MSTR", "PLTR", "AMD", "SOFI", "NFLX", "SPY"]
CRYPTO = ["BTC/USD"]
ALLOWED = STOCKS + CRYPTO

# Testing switch: shows stock data even when the market is closed.
# Set to False before the bot goes live.
FORCE_STOCKS = True

def get_json(url, **kwargs):
    r = requests.get(url, **kwargs)
    if r.status_code != 200:
        print(f"Error {r.status_code} from {url}: {r.text[:200]}")
        sys.exit(1)
    return r.json()

def fetch_bars(symbols, days, crypto):
    start = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    url = f"{DATA_URL}/v1beta3/crypto/us/bars" if crypto else f"{DATA_URL}/v2/stocks/bars"
    result = {s: [] for s in symbols}
    page_token = None
    while True:
        params = {"symbols": ",".join(symbols), "timeframe": "1Hour",
                  "start": start, "limit": 10000, "sort": "asc"}
        if not crypto:
            params["feed"] = "iex"
        if page_token:
            params["page_token"] = page_token
        data = get_json(url, headers=headers, params=params)
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
        candles.append(chunk[-1]["c"])
    return candles

def trend_line(name, bars):
    if len(bars) < 51:
        return f"{name}: not enough data ({len(bars)} hourly bars)"
    closes = [b["c"] for b in bars]
    vols = [b["v"] for b in bars]
    avg_vol = sum(vols[-20:]) / 20
    c4 = to_4h(bars)
    trend_4h = f"4H EMA20 {ema(c4, 20):,.2f} / EMA50 {ema(c4, 50):,.2f}" if len(c4) >= 51 else "4H: not enough data"
    return (f"{name} | price {closes[-1]:,.2f} | "
            f"1H EMA20 {ema(closes, 20):,.2f} / EMA50 {ema(closes, 50):,.2f} | "
            f"{trend_4h} | RSI {rsi(closes):.1f} | "
            f"volume {'above' if vols[-1] > avg_vol else 'below'} average")

# ---------- Gather everything ----------

clock = get_json(f"{PAPER_URL}/v2/clock", headers=headers)
market_open = clock["is_open"]

account = get_json(f"{PAPER_URL}/v2/account", headers=headers)
positions = get_json(f"{PAPER_URL}/v2/positions", headers=headers)

fng = get_json("https://api.alternative.me/fng/?limit=1")["data"][0]

watch = (STOCKS if (market_open or FORCE_STOCKS) else []) + CRYPTO
stock_watch = [s for s in watch if s not in CRYPTO]
stock_bars = fetch_bars(stock_watch, 60, crypto=False) if stock_watch else {}
crypto_bars = fetch_bars(CRYPTO, 60, crypto=True)

news = get_json(f"{DATA_URL}/v1beta1/news", headers=headers,
                params={"symbols": ",".join(watch), "limit": 50, "sort": "desc"}).get("news", [])

# ---------- Print the briefing ----------

print("=== MARKET BRIEFING ===")
print(f"Stock market open: {market_open}")
if not market_open:
    print("Market closed: stocks skipped unless the test switch is on.")

print("\n--- Account ---")
print(f"Cash: ${float(account['cash']):,.2f}")
print(f"Portfolio value: ${float(account['portfolio_value']):,.2f}")
print(f"Open positions: {len(positions)}")
for p in positions:
    print(f"  {p['symbol']} | qty {p['qty']} | avg entry ${float(p['avg_entry_price']):,.2f} | P/L {float(p['unrealized_plpc']) * 100:.2f}%")

print("\n--- Sentiment ---")
print(f"Crypto Fear & Greed: {fng['value']} ({fng['value_classification']})")

print("\n--- Price trends ---")
for sym in CRYPTO:
    print(trend_line(sym, crypto_bars[sym]))
for sym in STOCKS:
    if sym in stock_bars:
        print(trend_line(sym, stock_bars[sym]))

print("\n--- News ---")
for asset in watch:
    base = asset.split("/")[0]
    matches = [n for n in news if asset in n.get("symbols", []) or base in n.get("symbols", [])][:2]
    print(f"{asset}:")
    if not matches:
        print("  (no recent headlines)")
    for n in matches:
        print(f"  - {n['headline']}")

# ---------- Ask Claude for a decision (no trades placed) ----------

lines = [
    f"Stock market open: {market_open}",
    f"Cash: ${float(account['cash']):,.2f}",
    f"Portfolio value: ${float(account['portfolio_value']):,.2f}",
    f"Open positions: {len(positions)}",
]
for p in positions:
    lines.append(f"  {p['symbol']} qty {p['qty']} avg entry ${float(p['avg_entry_price']):,.2f} P/L {float(p['unrealized_plpc']) * 100:.2f}%")
lines.append(f"Crypto Fear & Greed: {fng['value']} ({fng['value_classification']})")
for sym in CRYPTO:
    lines.append(trend_line(sym, crypto_bars[sym]))
for sym in STOCKS:
    if sym in stock_bars:
        lines.append(trend_line(sym, stock_bars[sym]))
for asset in watch:
    base = asset.split("/")[0]
    matches = [n for n in news if asset in n.get("symbols", []) or base in n.get("symbols", [])][:2]
    for n in matches:
        lines.append(f"News {asset}: {n['headline']}")
briefing_text = "\n".join(lines)

instructions = """You are an active trading assistant for a paper-trading account. Find good trades rather than defaulting to cash.
Allowed assets: NVDA, TSLA, AMZN, GOOGL, MSTR, PLTR, AMD, SOFI, NFLX, SPY, BTC/USD.
Pick AT MOST ONE trade per run, or hold if nothing qualifies.
Buy when the setup qualifies: price above the 20-hour average on the 1H chart, RSI between 40 and 70, and volume above average. The 4H trend being above its 20-hour average is a bonus but not required.
If several assets qualify, pick the one with the strongest setup.
The code will automatically add a 2% stop-loss and 4% take-profit to any buy, so you do not need to set them.
Reply with ONLY a JSON object, no other text, in this exact format:
{"action": "buy" or "hold", "symbol": "one allowed asset or null", "reasoning": "two to four plain sentences"}"""

r = requests.post(
    "https://api.anthropic.com/v1/messages",
    headers={
        "x-api-key": ANTHROPIC_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    },
    json={
        "model": "claude-haiku-5-5",
        "max_tokens": 400,
        "system": instructions,
        "messages": [{"role": "user", "content": briefing_text}],
    },
)
if r.status_code != 200:
    print(f"Claude error {r.status_code}: {r.text[:300]}")
    sys.exit(1)

raw = "".join(block.get("text", "") for block in r.json()["content"] if block.get("type") == "text")
cleaned = re.sub(r"```json|```", "", raw).strip()
try:
    decision = json.loads(cleaned)
except json.JSONDecodeError:
    print("Claude did not return valid JSON. Raw reply:")
    print(raw)
    sys.exit(1)

action = decision.get("action")
symbol = decision.get("symbol")
if action not in ("buy", "hold") or (action == "buy" and symbol not in ALLOWED):
    print("Decision rejected by safety check:")
    print(decision)
    sys.exit(1)

print("\n=== CLAUDE DECISION ===")
print(f"Action: {action}")
print(f"Symbol: {symbol}")
print(f"Reasoning: {decision.get('reasoning', '')}")
print("No orders were placed. This is a test run.")
