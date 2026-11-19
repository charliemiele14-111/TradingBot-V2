import os
import sys
import requests

KEY_ID = os.environ.get("ALPACA_KEY_ID", "").strip()
SECRET = os.environ.get("ALPACA_SECRET_KEY", "").strip()

print(f"Key ID length: {len(KEY_ID)} characters")
print(f"Secret length: {len(SECRET)} characters")

if not KEY_ID or not SECRET:
    print("A key is missing. The GitHub secret names may not match exactly.")
    sys.exit(1)

headers = {
    "APCA-API-KEY-ID": KEY_ID,
    "APCA-API-SECRET-KEY": SECRET,
}

base_url = "https://paper-api.alpaca.markets"

def check(label, path):
    r = requests.get(base_url + path, headers=headers)
    print(f"{label} status code: {r.status_code}")
    print(f"{label} reply: {r.text[:300]}")
    if r.status_code != 200:
        print("Stopping here. Alpaca did not accept this request.")
        sys.exit(1)
    return r.json()

account = check("Account", "/v2/account")
print(f"Connected to Alpaca. Cash available: ${account['cash']}")
print(f"Account status: {account['status']}")

clock = check("Clock", "/v2/clock")
print(f"Stock market open right now: {clock['is_open']}")
print(f"Next market open: {clock['next_open']}")
