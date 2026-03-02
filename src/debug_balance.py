import sys
import os
import json
import requests

base_dir = r"c:\Users\sunny\Desktop\bootcamp_test\ai_trading_bot"
sys.path.append(base_dir)

from src.api.koreainvestment import KoreaInvestmentAPI

def check_raw_balance():
    api = KoreaInvestmentAPI()
    api.get_access_token()
    
    url = f"{api.url_base}/uapi/domestic-stock/v1/trading/inquire-balance"
    headers = api.headers.copy()
    
    # 모의투자는 VTTC8434R, 실전투자는 TTTC8434R
    tr_id = "VTTC8434R" if "vts" in api.url_base.lower() else "TTTC8434R"
    headers["tr_id"] = tr_id
    
    print(f"URL: {url}")
    print(f"TR_ID: {tr_id}")
    print(f"AUTHORIZATION: {api.access_token[:10]}...")
    
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
    
    response = requests.get(url, headers=headers, params=params)
    print("STATUS:", response.status_code)
    print("TEXT:", response.text)

check_raw_balance()
