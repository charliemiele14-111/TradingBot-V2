import math
import sys
from datetime import datetime, timezone
import requests

from safety import check_buy, MAX_PER_TRADE, STOP_LOSS_PCT, TAKE_PROFIT_PCT

PAPER_URL = "https://paper-api.alpaca.markets"

# Keep this False while testing. Set to True only when you want real paper orders.
PLACE_ORDERS = False

def make_headers(key_id, secret):
    return {"APCA-API-KEY-ID": key_id, "APCA-API-SECRET-KEY": secret}

def get_json(url, headers, params=None):
    r = requests.get(url, headers=headers, params=params)
    if r.status_code != 200:
        print(f"Could not read {url} ({r.status_code}). Stopping to be safe.")
        sys.exit(1)
    return r.json()

def count_buys_today(headers):
    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    orders = get_json(f"{PAPER_URL}/v2/orders", headers,
                      {"status": "all", "limit": 500,
                       "after": midnight.strftime("%Y-%m-%dT%H:%M:%SZ")})
    return len([o for o in orders if o.get("side") == "buy"])

def handle_decision(decision, prices, headers):
    """prices: dict of symbol -> latest price. Returns one line describing what happened."""
    if decision.get("action") != "buy":
        return "Hold. No order placed."

    symbol = decision.get("symbol")
    if symbol == "BTC/USD":
        return "BTC/USD buys are not enabled yet (next step). No order placed."
    if symbol not in prices:
        return f"No price available for {symbol}. No order placed."

    price = prices[symbol]
    qty = math.floor(MAX_PER_TRADE / price)
    if qty < 1:
        return (f"{symbol} costs ${price:.2f} per share, which is more than the "
                f"${MAX_PER_TRADE:.0f} limit. No order placed.")

    account = get_json(f"{PAPER_URL}/v2/account", headers)
    positions = get_json(f"{PAPER_URL}/v2/positions", headers)
    trades_today = count_buys_today(headers)

    problems = check_buy(decision, float(account["cash"]), positions, trades_today)
    if problems:
        return "BLOCKED by safety rules: " + "; ".join(problems)

    stop_loss = round(price * (1 - STOP_LOSS_PCT), 2)
    take_profit = round(price * (1 + TAKE_PROFIT_PCT), 2)
    summary = f"Buy {qty} {symbol} at about ${price:.2f}, stop ${stop_loss}, target ${take_profit}"

    if not PLACE_ORDERS:
        return "TEST MODE, would place: " + summary

    order = {
        "symbol": symbol,
        "qty": str(qty),
        "side": "buy",
        "type": "market",
        "time_in_force": "day",
        "order_class": "bracket",
        "take_profit": {"limit_price": str(take_profit)},
        "stop_loss": {"stop_price": str(stop_loss)},
    }
    r = requests.post(f"{PAPER_URL}/v2/orders", headers=headers, json=order)
    if r.status_code not in (200, 201):
        return f"Alpaca rejected the order ({r.status_code}): {r.text[:200]}"
    return f"ORDER PLACED: {summary} (order id {r.json().get('id')})"
