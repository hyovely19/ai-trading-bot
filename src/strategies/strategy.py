# 투자 전략과 AI 모델의 결정을 관리하는 파일입니다.

class AIStrategy:
    """AI 기반 자동매매 판단 전략 클래스"""
    
    def __init__(self):
        """
        AI 모델이나 전략에 필요한 정보를 초기화합니다.
        """
        # 수익률이 8% 도달한 이후 하락을 방어할 '트레일링 스탑(추적 매도)' 최고 수익률 기록용 책갈피입니다.
        self.highest_profit_rates = {}
        
    def update_market_data(self, new_data):
        """
        최신 시장 데이터(가격, 거래량 등)를 받아와서 내부 데이터를 업데이트합니다.
        
        Args:
            new_data: 새롭게 받아온 시장 데이터
        """
        pass

    def analyze_market(self):
        """
        업데이트된 데이터를 바탕으로 AI 모델(또는 알고리즘)을 사용해 시장 상황을 분석합니다.
        """
        pass
        
    def check_buy_signal(self, stock_code: str, df_daily=None, current_price: float=None):
        """
        분석 결과를 바탕으로 지금 해당 종목을 사야 할지(매수) 결정합니다.
        매수 조건: 5일 이평선이 20일 이평선을 뚫고 올라가는 골든크로스 발생 + 거래량 전일 대비 200% 이상 폭발
        + 추가: 매수 신호 발생 시 현재가보다 0.5% 높은 '지정가'를 생성해 너무 비싸게 체결되는 것(슬리피지)을 막습니다.
        
        Args:
            stock_code (str): 확인할 종목코드
            df_daily (DataFrame, optional): 최근 일봉 데이터 (종가 'close', 거래량 'volume' 포함)
            current_price (float, optional): 현재가 (슬리피지 방지용)
            
        Returns:
            tuple: (매수할지_여부(bool), 주문할지정가(float))
        """
        # 만약 차트 데이터가 없거나 20일치보다 적으면 판단을 보류합니다.
        if df_daily is None or len(df_daily) < 20 or current_price is None:
            return False, 0.0
            
        try:
            # 5일, 20일 평균 가격(이동평균선)을 계산합니다.
            ma5 = df_daily['close'].rolling(window=5).mean()
            ma20 = df_daily['close'].rolling(window=20).mean()
            
            # 오늘과 어제의 이평선 값 추출
            today_ma5 = ma5.iloc[-1]
            today_ma20 = ma20.iloc[-1]
            yesterday_ma5 = ma5.iloc[-2]
            yesterday_ma20 = ma20.iloc[-2]
            
            # 거래량 조건: 오늘 거래량이 어제 거래량의 200%(2배) 이상인지 확인합니다.
            today_volume = df_daily['volume'].iloc[-1]
            yesterday_volume = df_daily['volume'].iloc[-2]
            
            # 어제 거래량이 0일 경우(거래 정지 등) 에러를 막기 위한 방어 코드
            if yesterday_volume == 0:
                return False, 0.0
                
            is_volume_burst = today_volume >= (yesterday_volume * 2.0)
            
            # 골든크로스 조건: 어제는 5일선이 20일선 아래였는데, 오늘은 20일선 위로 올라왔는지 확인합니다.
            is_golden_cross = (yesterday_ma5 <= yesterday_ma20) and (today_ma5 > today_ma20)
            
            # 두 가지 조건을 동시에 만족할 경우
            if is_golden_cross and is_volume_burst:
                # 슬리피지 방지: 현재가보다 0.5%만 딱 높여서 그 가격까지만 사겠다고 '지정'합니다.
                # 이렇게 하면 가격이 0.5% 이상 미친듯이 튀어 오를 때는 비싸게 사지 않고 포기하게 됩니다.
                limit_buy_price = current_price * 1.005 
                return True, limit_buy_price
                
            return False, 0.0
            
        except Exception as e:
            # 에러 발생 시 사지 않고 안전하게 넘어갑니다.
            return False, 0.0
            
    def check_sell_signal(self, stock_code: str, buy_price: float, current_price: float):
        """
        분석 결과를 바탕으로 지금 해당 종목을 팔아야 할지(매도) 결정합니다.
        매도 조건: 수익률 8% 이상 도달 후 최고 수익률 대비 -3% 하락 시 트레일링 스탑 작동
        
        Args:
            stock_code (str): 확인할 종목코드
            buy_price (float): 내가 산 평균 가격
            current_price (float): 현재 시장 가격
        """
        # 아직 사지 않은 종목이거나 에러라면 팔지 않습니다.
        if buy_price <= 0:
            return False
            
        # 현재 몇 퍼센트 이익/손해를 보고 있는지 계산합니다. (예: 0.08 = 8%)
        current_profit_rate = (current_price - buy_price) / buy_price
        
        # 종목별로 가장 높았던 수익률을 기록해둡니다. (처음이면 현재 수익률로 저장)
        if stock_code not in self.highest_profit_rates:
            self.highest_profit_rates[stock_code] = current_profit_rate
            
        # 가격이 더 올랐다면 역대 최고 수익률을 갈아치웁니다.
        if current_profit_rate > self.highest_profit_rates[stock_code]:
            self.highest_profit_rates[stock_code] = current_profit_rate
            
        highest_rate = self.highest_profit_rates[stock_code]
        
        # [트레일링 스탑 로직]
        # 1. 예전에 한 번이라도 수익률이 8% (0.08) 이상을 찍은 적이 있는가?
        if highest_rate >= 0.08:
            # 2. 그렇다면, 가장 고점을 찍었을 때 대비 현재 수익률이 3%나 떨어졌는가?
            # (예: 한때 수익률이 10% 였는데, 지금은 7% 이하가 되었다면)
            if current_profit_rate <= (highest_rate - 0.03):
                # 팔 때가 되었으므로, 다음 번 새로운 매수를 위해 기록을 싹 지워줍니다.
                self.highest_profit_rates.pop(stock_code, None)
                # '팔아라(True)' 신호를 내보냅니다.
                return True
                
        # 조건에 안 맞으면 아직 들고 갑니다(False).
        return False
