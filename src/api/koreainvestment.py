# 한국투자증권 API와의 통신을 담당하는 파일입니다.
import requests
import json
import os
from dotenv import load_dotenv

# 환경설정 파일(.env)을 불러옵니다.
load_dotenv()

class KoreaInvestmentAPI:
    """한국투자증권 OPEN API 통신 클래스"""
    
    def __init__(self):
        """
        API 키와 필요한 정보들을 초기화합니다.
        .env 파일에서 보안 정보들을 읽어옵니다.
        """
        self.app_key = os.getenv("APP_KEY")
        self.app_secret = os.getenv("APP_SECRET")
        self.url_base = os.getenv("URL_BASE")
        self.account_no = os.getenv("CANO")
        self.product_code = os.getenv("ACNT_PRDT_CD")
        
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
        # 토큰 발급을 위한 주소 설정
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
                
                print("✅ 한국투자증권 API 토큰 발급 성공!")
            else:
                print(f"❌ 토큰 발급 실패: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ 토큰 발급 중 오류 발생: {e}")

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
                print(f"❌ 현재가 조회 실패: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ 현재가 조회 중 오류 발생: {e}")
            return None

    def buy_market_order(self, stock_code: str, quantity: int):
        """
        지정한 종목을 현재 시장 가격(시장가)으로 매수(살 때)하는 주문을 넣습니다.
        
        Args:
            stock_code (str): 매수할 종목코드
            quantity (int): 매수할 수량
        """
        pass

    def sell_market_order(self, stock_code: str, quantity: int):
        """
        지정한 종목을 현재 시장 가격으로 매도(팔 때)하는 주문을 넣습니다.
        
        Args:
            stock_code (str): 매도할 종목코드
            quantity (int): 매도할 수량
        """
        pass

    def get_account_balance(self):
        """
        현재 내 계좌의 잔고(보유 예수금 및 주식)를 조회합니다.
        """
        pass
