# 자산을 안전하게 지키고 관리하는 위기 대응(Risk Manager) 파일입니다.
import sys
import os

# 현재 폴더(src/utils) 위(src)를 넘어 최상위 폴더(ai_trading_bot)를 인식하도록 등록합니다.
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import INVESTMENT_RATIO, STOP_LOSS_RATE, TARGET_PROFIT_RATE

class RiskManager:
    """내 자산의 손실을 최소화하고 투자 비중을 조절하는 클래스"""
    
    def __init__(self):
        """
        위험 관리에 필요한 기준값들을 준비합니다.
        (config.py 파일에 적은 손절 기준, 익절 기준 등을 가져옵니다.)
        """
        self.investment_ratio = INVESTMENT_RATIO
        self.stop_loss_rate = STOP_LOSS_RATE
        self.target_profit_rate = TARGET_PROFIT_RATE
        pass

    def check_stop_loss(self, buy_price: float, current_price: float) -> bool:
        """
        현재 가격이 손해를 끊어내야 할(손절) 기준까지 떨어졌는지 감시합니다.
        
        Args:
            buy_price (float): 내가 주식을 샀던 가격
            current_price (float): 현재 주식 가격
            
        Returns:
            bool: 손절 기준까지 떨어졌다면 True(손절 명령), 아니면 False 반환
        """
        pass

    def check_take_profit(self, buy_price: float, current_price: float) -> bool:
        """
        현재 가격이 목표했던 이익(익절) 기준까지 올라왔는지 확인합니다.
        
        Args:
            buy_price (float): 내가 주식을 샀던 가격
            current_price (float): 현재 주식 가격
            
        Returns:
            bool: 목표 이익에 도달했다면 True(익절 명령), 아니면 False 반환
        """
        pass

    def calculate_order_quantity(self, total_capital: int, current_price: int) -> int:
        """
        내가 가진 전체 현금에서 이번에 몇 주까지 살 수 있는지 안전하게 계산해 줍니다.
        (config 파일에서 설정한 '1회 투자 비중'만큼만 사도록 조절합니다.)
        
        Args:
            total_capital (int): 내 계좌에 있는 전체 현금(주식 구매 가능한 돈)
            current_price (int): 사려는 주식의 현재 1주 가격
            
        Returns:
            int: 구매해도 안전한 주식 주문 수량(몇 개를 살지)
        """
        pass
