import requests
import json
import config

# ==========================================
# [API 통신 모듈] 한국투자증권 API 통신 담당
# ==========================================

class KISApiClient:
    def __init__(self):
        self.base_url = config.BASE_URL
        self.app_key = config.APP_KEY
        self.app_secret = config.APP_SECRET
        self.access_token = None
        
    def get_access_token(self):
        """
        API 호출에 필요한 접근 토큰(Access Token)을 발급받습니다.
        """
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        url = f"{self.base_url}/oauth2/tokenP"
        
        # 주석: 실제 API 호출 코드 (현재는 프린트만)
        # res = requests.post(url, headers=headers, data=json.dumps(body))
        # self.access_token = res.json().get("access_token")
        
        print(">> [API] 접근 토큰 발급 완료 (가상)")
        self.access_token = "dummy_token"
        
    def get_current_price(self, symbol):
        """
        특정 종목(symbol)의 현재가를 조회합니다.
        """
        print(f">> [API] {symbol} 종목 현재가 조회 요청")
        # 실제 API 호출을 통해 현재가 리턴하는 로직 구현 필요
        return 80000 
        
    def buy_order(self, symbol, qty, price):
        """
        매수 주문을 넣습니다.
        """
        print(f">> [API] {symbol} 종목 {qty}주 매수 주문 (가격: {price})")
        return True
        
    def sell_order(self, symbol, qty, price):
        """
        매도 주문을 넣습니다.
        """
        print(f">> [API] {symbol} 종목 {qty}주 매도 주문 (가격: {price})")
        return True
