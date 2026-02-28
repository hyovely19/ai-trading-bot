# ==========================================
# [전략 모듈] AI 종목 분석 및 매매 타이밍 결정
# ==========================================

class TradingStrategy:
    def __init__(self, api_client):
        self.api = api_client
        
    def analyze_market(self, symbol):
        """
        시장 상황(현재가, 지표 등)을 분석하고 AI 모델을 돌려 매수/매도/관망 신호를 결정합니다.
        반환값: 'BUY', 'SELL', 'HOLD'
        """
        print(f">> [AI 분석] {symbol} 데이터 수집 및 분석 중...")
        current_price = self.api.get_current_price(symbol)
        
        # 임시 로직: 무조건 관망(HOLD) 신호를 보냄
        # 추후 여기에 머신러닝/딥러닝 등 진짜 AI 로직이 들어갈 곳입니다.
        signal = 'HOLD'
        print(f">> [AI 분석 결과] 추천 신호: {signal}")
        
        return signal

    def execute_strategy(self, symbol):
        """
        분석 결과에 따라 실제로 주문을 실행하는 함수
        """
        signal = self.analyze_market(symbol)
        
        if signal == 'BUY':
            self.api.buy_order(symbol, 1, 0) # 0은 시장가 매수를 의미
        elif signal == 'SELL':
            self.api.sell_order(symbol, 1, 0)
        else:
            print(f">> [전략] 신호가 HOLD(관망)이므로 매매를 건너뜁니다.\n")
