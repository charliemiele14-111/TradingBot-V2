MAX_PER_TRADE = 50.00
MIN_CASH_RESERVE = 100.00
MAX_TRADES_PER_DAY = 5
MAX_OPEN_POSITIONS = 3
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04

# Keep this list matching the watchlist in bot_briefing.py
ALLOWED = ["NVDA", "TSLA", "AMZN", "GOOGL", "MSTR", "PLTR", "AMD", "SOFI", "NFLX", "SPY", "BTC/USD"]

def check_buy(decision, cash, positions, trades_today):
    """Return a list of reasons the buy is blocked. An empty list means allowed."""
    symbol = decision.get("symbol")
    problems = []

    if symbol not in ALLOWED:
        problems.append(f"{symbol} is not on the allowed list")
    if trades_today >= MAX_TRADES_PER_DAY:
        problems.append(f"already made {trades_today} trades today (max {MAX_TRADES_PER_DAY})")
    if len(positions) >= MAX_OPEN_POSITIONS:
        problems.append(f"already have {len(positions)} open positions (max {MAX_OPEN_POSITIONS})")
    if any(p["symbol"] == symbol for p in positions):
        problems.append(f"already holding {symbol}")
    if cash - MAX_PER_TRADE < MIN_CASH_RESERVE:
        problems.append(f"buying ${MAX_PER_TRADE:.0f} would drop cash below ${MIN_CASH_RESERVE:.0f}")

    return problems
