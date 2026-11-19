import os
import sys
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()

headers = {
    "APCA-API-KEY-ID": KEY_ID,
    "APCA-API-SECRET-KEY": SECRET,
}

url = "https://data.alpaca.markets/v1beta3/crypto/us/bars"
params = {"symbols": "BTC/USD", "timeframe": "1Hour", "limit": 5}

r = requests.get(url, headers=headers, params=params)
print(f"Bars status code: {r.status_code}")

if r.status_code != 200:
    print(r.text[:300])
    sys.exit(1)

bars = r.json()["bars"]["BTC/USD"]
for b in bars:
    print(f"Time {b['t']} | Close ${b['c']} | Volume {b['v']}")
print(f"Got {len(bars)} hourly bars for BTC/USD.")
