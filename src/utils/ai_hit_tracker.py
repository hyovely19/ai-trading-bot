# AI(또는 우리 전략)가 얼마나 주식 시장을 잘 맞히고 있는지,
# 즉 '승률'과 '수익률'을 기록하고 평가하는 파일입니다.

class AIHitTracker:
    """AI 투자 모델의 예측 성공률(승률)을 추적하는 클래스"""
    
    def __init__(self):
        """
        승률 계산에 필요한 과거 기록들(몇 번 이기고 졌는지)을 저장할 공간을 만듭니다.
        """
        self.total_trades = 0       # 총 거래 횟수
        self.winning_trades = 0     # 이익을 본 거래 횟수 (승리)
        self.losing_trades = 0      # 손해를 본 거래 횟수 (패배)
        self.trade_history = []     # 과거 모든 거래 기록을 담아두는 리스트

    def record_trade_result(self, stock_code: str, buy_price: int, sell_price: int):
        """
        주식을 사고팔 때마다 그 결과를 기록 장부에 적습니다.
        
        Args:
            stock_code (str): 거래한 종목코드
            buy_price (int): 샀던 가격
            sell_price (int): 팔았던 가격
        """
        # 주식을 팔았을 때 수익이 났는지(샀던 가격보다 비싸게 팔았는지) 확인합니다.
        profit_amount = sell_price - buy_price
        
        # 0보다 크면 이익을 본 것(승리)
        if profit_amount > 0:
            self.winning_trades += 1
            is_win = True
        # 그렇지 않다면 손해를 본 것(패배)
        else:
            self.losing_trades += 1
            is_win = False
            
        self.total_trades += 1
        
        # 언제, 어떤 종목을, 얼마에 사서 얼마에 팔았는지, 그리고 이겼는지 장부에 기록합니다.
        trade_record = {
            "stock_code": stock_code,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "profit_amount": profit_amount,
            "is_win": is_win
        }
        self.trade_history.append(trade_record)

    def calculate_win_rate(self) -> float:
        """
        지금까지 AI가 추천해서 거래한 결과가 얼마나 성공적이었는지(승률)를 퍼센트(%)로 계산합니다.
        
        Returns:
            float: 승리 비율 (예: 60.5)
        """
        # 거래한 적이 한 번도 없다면 승률은 0% 입니다.
        if self.total_trades == 0:
            return 0.0
            
        # (이긴 횟수 / 전체 횟수) * 100 으로 승률을 퍼센트(%)로 계산합니다.
        # 소수점 둘째 자리까지만 예쁘게 잘라서 보여줍니다 (예: 66.67)
        win_rate = float((self.winning_trades / self.total_trades) * 100)
        return round(win_rate, 2)

    def get_performance_summary(self) -> dict:
        """
        총 몇 번 거래해서 몇 번 이겼고, 승률은 얼마나 되는지 종합 성적표를 보여줍니다.
        (나중에 화면에 출력하거나 로거(logger)에 기록하기 좋습니다.)
        
        Returns:
            dict: 총 거래수, 승, 패, 승률이 담긴 정보 사전(dictionary)
        """
        # 종합 성적표(사전 형식)를 만들어서 돌려줍니다.
        summary = {
            "총 거래 횟수": self.total_trades,
            "성공(익절) 횟수": self.winning_trades,
            "실패(손절) 횟수": self.losing_trades,
            "현재 승률(%)": self.calculate_win_rate()
        }
        return summary
