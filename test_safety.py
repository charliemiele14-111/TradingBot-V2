from safety import check_buy

cases = [
    ("Good buy of NVDA", {"action": "buy", "symbol": "NVDA"}, 5000, [], 0),
    ("Symbol not on list", {"action": "buy", "symbol": "XYZ"}, 5000, [], 0),
    ("Trade limit reached", {"action": "buy", "symbol": "NVDA"}, 5000, [], 5),
    ("Too many open positions", {"action": "buy", "symbol": "NVDA"}, 5000,
     [{"symbol": "AMD"}, {"symbol": "TSLA"}, {"symbol": "SPY"}], 0),
    ("Cash would fall too low", {"action": "buy", "symbol": "NVDA"}, 120, [], 0),
]

for name, decision, cash, positions, trades_today in cases:
    problems = check_buy(decision, cash, positions, trades_today)
    if problems:
        print(f"BLOCKED - {name}: " + "; ".join(problems))
    else:
        print(f"ALLOWED - {name}")
