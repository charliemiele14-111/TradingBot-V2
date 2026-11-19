import os
import requests

KEY_ID = os.environ["ALPACA_KEY_ID"]
SECRET = os.environ["ALPACA_SECRET_KEY"]

headers = {
    "APCA-API-KEY-ID": KEY_ID,
    "APCA-API-SECRET-KEY": SECRET,
}

# Paper trading account address
base_url = "https://paper-api.alpaca.markets"

response = requests.get(f"{base_url}/v2/account", headers=headers)
if response.status_code == 200:
    account = response.json()
    print("Connected to Alpaca successfully.")
    print(f"Cash available: ${account['cash']}")
    print(f"Account status: {account['status']}")
else:
    print(f"Connection failed. Status code: {response.status_code}")
    print(response.text)

clock = requests.get(f"{base_url}/v2/clock", headers=headers).json()
print(f"Stock market open right now: {clock['is_open']}")
print(f"Next market open: {clock['next_open']}")
