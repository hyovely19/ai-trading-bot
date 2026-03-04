import sys
import json
import time
sys.path.append(r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot")
from src.api.koreainvestment import KoreaInvestmentAPI

api = KoreaInvestmentAPI()
api.get_access_token()

# Inquire Daily Executions
url = f"{api.url_base}/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
headers = api.headers.copy()
headers["tr_id"] = "VTTC8001R" if "vts" in str(api.url_base).lower() else "TTTC8001R"

params = {
    "CANO": api.account_no,
    "ACNT_PRDT_CD": api.product_code,
    "INQR_STRT_DT": time.strftime("%Y%m%d"),
    "INQR_END_DT": time.strftime("%Y%m%d"),
    "SLL_BUY_DVSN_CD": "00",
    "INQR_DVSN": "00",
    "PDNO": "",
    "CCLD_DVSN": "00", # 00: 전체, 01: 체결, 02: 미체결
    "ORD_GNO_BRNO": "",
    "ODNO": "",
    "INQR_DVSN_3": "00",
    "INQR_DVSN_1": "",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": ""
}

import requests
res = requests.get(url, headers=headers, params=params).json()
print("=== DAILY EXECUTIONS === ")
out1 = res.get('output1', [])
for o in out1: # latest first
    print(f"Time: {o.get('ord_tmd')}, Name: {o.get('prdt_name')}, Status: {o.get('ord_dtpt_ccld_rcnn_name')}({o.get('ord_dtpt_ccld_rcnn_cd')}), Qty: {o.get('ord_qty')}, Rej: {o.get('rmn_qty')}")

print("\nDetail Output (Top 3):")
print(json.dumps(out1[:3], indent=2, ensure_ascii=False))
