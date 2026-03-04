import sys
import json
sys.path.append(r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot")
from src.api.koreainvestment import KoreaInvestmentAPI

api = KoreaInvestmentAPI()
api.get_access_token()

url = f"{api.url_base}/uapi/domestic-stock/v1/trading/inquire-balance"
headers = api.headers.copy()
headers["tr_id"] = "VTTC8434R" if "vts" in str(api.url_base).lower() else "TTTC8434R"
params = {
    "CANO": api.account_no,
    "ACNT_PRDT_CD": api.product_code,
    "AFHR_FLPR_YN": "N",
    "OFRT_WTHR_YN": "N",
    "INQR_DVSN": "01",
    "UNPR_DVSN": "01",
    "FUND_STTL_ICLD_YN": "N",
    "FNCG_AMT_AUTO_RDPT_YN": "N",
    "PRCS_DVSN": "01",
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": "",
    "OFL_YN": ""
}
import requests
res = requests.get(url, headers=headers, params=params).json()
print("=== AFTER RECENT BUY ORDER RAW BALANCE === ")
print(json.dumps(res['output2'], indent=2, ensure_ascii=False))

# 미체결 내역 조회
url_pending = f"{api.url_base}/uapi/domestic-stock/v1/trading/inquire-psbl-rvsecncl"
headers["tr_id"] = "VTTC8036R" if "vts" in str(api.url_base).lower() else "TTTC8036R"
params_pending = {
    "CANO": api.account_no,
    "ACNT_PRDT_CD": api.product_code,
    "CTX_AREA_FK100": "",
    "CTX_AREA_NK100": "",
    "INQR_DVSN_1": "0",
    "INQR_DVSN_2": "0"
}
res_pending = requests.get(url_pending, headers=headers, params=params_pending).json()
print("\n=== PENDING ORDERS === ")
print(json.dumps(res_pending.get('output', []), indent=2, ensure_ascii=False))
