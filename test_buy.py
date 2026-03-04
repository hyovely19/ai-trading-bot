import sys
import json
import logging
sys.path.append(r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot")

from src.api.koreainvestment import KoreaInvestmentAPI

logging.basicConfig(level=logging.INFO)

api = KoreaInvestmentAPI()
api.get_access_token()

print("--- Before Buy ---")
balance_before = api.get_account_balance()
print(json.dumps(balance_before, indent=2, ensure_ascii=False))

print("\n--- Buy Order (삼성전자 1주) ---")
res = api.buy_market_order("005930", 1)
print(json.dumps(res, indent=2, ensure_ascii=False))

print("\n--- After Buy ---")
import time
time.sleep(1)
balance_after = api.get_account_balance()
print(json.dumps(balance_after, indent=2, ensure_ascii=False))
