import sys
sys.path.append(r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot")

from src.api.koreainvestment import KoreaInvestmentAPI

api = KoreaInvestmentAPI()
api.get_access_token()
res = api.get_account_balance()
print("잔고 데이터 리턴값:", res)
