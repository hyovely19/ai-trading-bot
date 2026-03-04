import sys
import json
import time
sys.path.append(r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot")
from src.api.koreainvestment import KoreaInvestmentAPI

api = KoreaInvestmentAPI()
api.get_access_token()

code = "005930" # Samsung
qty = 1

curr_price = api.get_current_price(code)
print(f"Current price for {code}: {curr_price}")

# Custom limit order
url = f"{api.url_base}/uapi/domestic-stock/v1/trading/order-cash"
headers = api.headers.copy()
headers["tr_id"] = "VTTC0802U" if "vts" in str(api.url_base).lower() else "TTTC0802U"
body = {
    "CANO": api.account_no,
    "ACNT_PRDT_CD": api.product_code,
    "PDNO": code,
    "ORD_DVSN": "00", # 00: Limit order (지정가)
    "ORD_QTY": str(qty),
    "ORD_UNPR": str(curr_price) # Current price
}

import requests
print("\n--- Place Limit Order ---")
res = requests.post(url, headers=headers, data=json.dumps(body)).json()
print(json.dumps(res, indent=2, ensure_ascii=False))

time.sleep(2)

print("\n--- Balance After Limit Order ---")
bal = api.get_account_balance()
print(json.dumps(bal, indent=2, ensure_ascii=False))
