import os
import sys
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()
headers = {"APCA-API-KEY-ID": KEY_ID, "APCA-API-SECRET-KEY": SECRET}

STOCKS = ["NVDA", "TSLA", "AMZN", "GOOGL", "MSTR", "PLTR", "AMD", "SOFI", "NFLX", "SPY"]
ASSETS = STOCKS + ["BTC/USD"]

# 1. Account status (paper account)
r = requests.get("https://paper-api.alpaca.markets/v2/account", headers=headers)
print(f"Account status code: {r.status_code}")
if r.status_code != 200:
    print(r.text[:300])
    sys.exit(1)
account = r.json()
print(f"Cash: ${float(account['cash']):,.2f}")
print(f"Portfolio value: ${float(account['portfolio_value']):,.2f}")

r = requests.get("https://paper-api.alpaca.markets/v2/positions", headers=headers)
positions = r.json() if r.status_code == 200 else []
print(f"Open positions: {len(positions)}")
for p in positions:
    print(f"  {p['symbol']} | qty {p['qty']} | avg entry ${float(p['avg_entry_price']):,.2f} | P/L {float(p['unrealized_plpc']) * 100:.2f}%")

# 2. Crypto Fear & Greed index (free, no key needed)
r = requests.get("https://api.alternative.me/fng/?limit=1")
if r.status_code == 200:
    item = r.json()["data"][0]
    print(f"Fear & Greed: {item['value']} ({item['value_classification']})")
else:
    print(f"Fear & Greed error: {r.status_code}")

# 3. Recent news, two headlines per asset
r = requests.get(
    "https://data.alpaca.markets/v1beta1/news",
    headers=headers,
    params={"symbols": ",".join(ASSETS), "limit": 30, "sort": "desc"},
)
if r.status_code != 200:
    print(f"News error {r.status_code}: {r.text[:200]}")
else:
    news = r.json().get("news", [])
    for asset in ASSETS:
        matches = [n for n in news if asset.split("/")[0] in n.get("symbols", [])][:2]
        print(f"News for {asset}:")
        if not matches:
            print("  (no recent headlines)")
        for n in matches:
            print(f"  - {n['headline']}")
