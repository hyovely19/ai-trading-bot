# 한국투자증권 API와의 통신을 담당하는 파일입니다.
import requests # type: ignore
import json
import os
from dotenv import load_dotenv # type: ignore

# config 폴더 안의 .env 파일을 찾아 로드합니다.
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(base_dir, 'config', '.env')
load_dotenv(env_path)

class KoreaInvestmentAPI:
    """한국투자증권 OPEN API 통신 클래스"""
    
    def __init__(self):
        """
        API 키와 필요한 정보들을 초기화합니다.
        .env 파일이나 config에서 보안 정보들을 읽어옵니다.
        """
        import sys
        if base_dir not in sys.path:
            sys.path.append(base_dir)
        import config # type: ignore
        
        self.app_key = config.KIS_APP_KEY or os.getenv("APP_KEY")
        self.app_secret = config.KIS_APP_SECRET or os.getenv("APP_SECRET")
        self.url_base = os.getenv("URL_BASE", "https://openapivts.koreainvestment.com:29443")
        
        cano = config.KIS_ACCOUNT_NO or os.getenv("CANO")
        self.account_no = cano.replace('-', '') if cano else ""
        self.product_code = os.getenv("ACNT_PRDT_CD", "01")
        
        # API 통신에 필요한 인증 토큰 (초기에는 None)
        self.access_token = None
        
        # 공통으로 사용할 HTTP 헤더 정보
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "text/plain",
            "charset": "UTF-8",
        }
        
    def get_access_token(self):
        """
        API를 사용하기 위한 접근 권한(토큰)을 발급받습니다.
        kis_sample 코드의 auth() 함수를 참고하여 작성되었습니다.
        """
        import time
        token_file = os.path.join(base_dir, 'config', 'kis_token.json')
        
        # 1. 저장된 기발급 토큰이 있는지 확인 (유효기간 20시간(72000초) 이내면 바로 재사용)
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if time.time() - data.get('timestamp', 0) < 72000:
                        self.access_token = data.get('access_token')
                        self.headers["authorization"] = f"Bearer {self.access_token}"
                        self.headers["appkey"] = self.app_key
                        self.headers["appsecret"] = self.app_secret
                        print("[안내] 기존에 발급받은 KIS API 토큰을 파일에서 불러와 재사용합니다.")
                        return
            except Exception as e:
                print(f"[오류] 기존 토큰 파일 읽기 실패: {e}")

        # 2. 토큰을 새로 발급받기 위한 주소 설정
        url = f"{self.url_base}/oauth2/tokenP"
        
        # 토큰을 달라고 요청할 때 보내야 하는 데이터
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            # 증권사 서버로 토큰 발급 요청 보내기
            response = requests.post(url, headers=self.headers, data=json.dumps(body))
            
            # 200은 서버가 요청을 정상적으로 처리했다는 의미입니다.
            if response.status_code == 200:
                result = response.json()
                self.access_token = result.get("access_token")
                
                # 발급받은 토큰을 앞으로의 기본 통신 헤더에 추가합니다.
                self.headers["authorization"] = f"Bearer {self.access_token}"
                self.headers["appkey"] = self.app_key
                self.headers["appsecret"] = self.app_secret
                
                # 3. 새로 발급받은 토큰을 다음번 재사용을 위해 파일에 저장해둡니다.
                try:
                    with open(token_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'access_token': self.access_token,
                            'timestamp': time.time()
                        }, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print(f"[오류] 새 토큰 파일 저장 실패: {e}")
                
                print("[성공] 한국투자증권 API 토큰 발급 완료 (새로 발급됨)!")
            else:
                print(f"[실패] 토큰 발급 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"[오류] 토큰 발급 중 오류 발생: {e}")

    def get_current_price(self, stock_code: str):
        """
        특정 종목의 현재 가격을 조회합니다.
        
        Args:
            stock_code (str): 종목코드 (예: 삼성전자 '005930')
        """
        if not self.access_token:
            print("토큰이 없습니다. 먼저 토큰을 발급받아주세요.")
            return None
            
        url = f"{self.url_base}/uapi/domestic-stock/v1/quotations/inquire-price"
        
        # 현재가 조회를 위한 특수 헤더 추가 설정(TR_ID)
        headers = self.headers.copy()
        # 'FHKST01010100'는 주식현재가 시세 조회를 의미하는 한국투자증권 고유의 거래 ID입니다.
        headers["tr_id"] = "FHKST01010100" 
        
        # 조회 요청에 필요한 추가 데이터 (종목코드 등)
        params = {
            "FID_COND_MRKT_DIV_CODE": "J", # J: 주식
            "FID_INPUT_ISCD": stock_code    # 종목번호
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                result = response.json()
                # 'stck_prpr'는 현재가를 의미하는 결괏값의 열쇠(key) 이름입니다.
                current_price = result['output']['stck_prpr']
                return int(current_price)
            else:
                print(f"[실패] 현재가 조회 실패: {response.text}")
                return None
                
        except Exception as e:
            print(f"[오류] 현재가 조회 중 오류 발생: {e}")
            return None

    def buy_market_order(self, stock_code: str, quantity: int):
        """
        지정한 종목을 현재 시장 가격(시장가)으로 매수(살 때)하는 주문을 넣습니다.
        """
        if not self.access_token: return None
        url = f"{self.url_base}/uapi/domestic-stock/v1/trading/order-cash"
        
        headers = self.headers.copy()
        # 'TTTC0802U'는 현금 매수 주문을 의미합니다. (모의투자의 경우 앞에 'V'가 붙기도 함)
        headers["tr_id"] = "VTTC0802U" if "vts" in str(self.url_base).lower() else "TTTC0802U"
        
        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "PDNO": stock_code,
            "ORD_DVSN": "01", # 01: 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0" # 시장가는 단가 0
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            return response.json()
        except Exception as e:
            print(f"[오류] 매수 주문 중 오류 발생: {e}")
            return None

    def sell_market_order(self, stock_code: str, quantity: int):
        """
        지정한 종목을 현재 시장 가격으로 매도(팔 때)하는 주문을 넣습니다.
        """
        if not self.access_token: return None
        url = f"{self.url_base}/uapi/domestic-stock/v1/trading/order-cash"
        
        headers = self.headers.copy()
        # 'TTTC0801U'는 현금 매도 주문을 의미합니다.
        headers["tr_id"] = "VTTC0801U" if "vts" in str(self.url_base).lower() else "TTTC0801U"
        
        body = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "PDNO": stock_code,
            "ORD_DVSN": "01", # 01: 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0"
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            return response.json()
        except Exception as e:
            print(f"[오류] 매도 주문 중 오류 발생: {e}")
            return None

    def get_account_balance(self):
        """
        현재 내 계좌의 잔고(보유 예수금 및 주식)를 조회합니다.
        """
        if not self.access_token: return None
        url = f"{self.url_base}/uapi/domestic-stock/v1/trading/inquire-balance"
        
        headers = self.headers.copy()
        headers["tr_id"] = "VTTC8434R" if "vts" in str(self.url_base).lower() else "TTTC8434R"
        
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
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
        
        try:
            response = requests.get(url, headers=headers, params=params)
            
            try:
                res_data = response.json()
            except json.JSONDecodeError:
                error_msg = f"서버 응답 파싱 실패 (HTTP {response.status_code}). WAF 등 IP 차단 방화벽에 막혔을 수 있습니다."
                print(f"[오류] {error_msg}")
                return {'error': error_msg}

            if res_data.get('rt_cd') != '0':
                error_msg = res_data.get('msg1', '알 수 없는 에러')
                print(f"[오류] 잔고 조회 API 에러: {error_msg}")
                return {'error': error_msg}
                
            # 메인 엔진에서 사용하기 좋게 데이터 정제
            stocks = []
            for item in res_data.get('output1', []):
                if int(item.get('hldg_qty', 0)) > 0:
                    stocks.append({
                        'code': item.get('pdno', ''),
                        'name': item.get('prdt_name', ''),
                        'qty': int(item.get('hldg_qty', 0)),
                        'avg_price': float(item.get('pchs_avg_pric', 0))
                    })
            
            output2 = res_data.get('output2', [])
            cash = 0.0
            total = 0.0
            if output2 and len(output2) > 0:
                # 한국투자증권에서 제공하는 D+2 정산 예수금(prvs_rcdl_excc_amt)이 실제 '주문 가능 현금'과 일치합니다.
                # (매수 체결 시 증권사 서버에서 즉시 차감됨)
                cash = float(output2[0].get('prvs_rcdl_excc_amt', 0))
                total = float(output2[0].get('tot_evlu_amt', 0))

            return {
                'cash': cash,
                'total': total,
                'stocks': stocks
            }
        except Exception as e:
            print(f"[오류] 잔고 조회 중 오류 발생: {e}")
            return None
