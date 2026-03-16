import sys
import os
import requests
import urllib3

urllib3.disable_warnings()
sys.path.append(os.getcwd())
import config
from src.api.koreainvestment import KoreaInvestmentAPI

api = KoreaInvestmentAPI()
api.get_access_token()

url = f"{api.url_base}/uapi/domestic-stock/v1/trading/inquire-balance"
headers = api.headers.copy()
headers['tr_id'] = 'VTTC8434R'

for prcs in ['00', '01']:
    for inqr in ['01', '02']:
        for unpr in ['01', '02']:
            params = {
                'CANO': api.account_no, 'ACNT_PRDT_CD': api.product_code,
                'AFHR_FLPR_YN': 'N', 'OFRT_WTHR_YN': 'N',
                'INQR_DVSN': inqr, 'UNPR_DVSN': unpr,
                'FUND_STTL_ICLD_YN': 'N', 'FNCG_AMT_AUTO_RDPT_YN': 'N',
                'PRCS_DVSN': prcs, 'CTX_AREA_FK100': '', 'CTX_AREA_NK100': '',
                'OFL_YN': ''
            }
            res = requests.get(url, headers=headers, params=params, proxies=api.proxies)
            data = res.json()
            stocks = data.get('output1', [])
            print(f"PRCS={prcs}, INQR={inqr}, UNPR={unpr} -> Stocks: {len(stocks)}")
            if len(stocks) > 0:
                s = stocks[0]
                print(f"  {s.get('prdt_name')}: qty={s.get('hldg_qty')}, ord_psbl={s.get('ord_psbl_qty')}, avg={s.get('pchs_avg_pric')}")
