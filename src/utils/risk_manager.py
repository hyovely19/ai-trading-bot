import os
import sys
import json
import logging
from datetime import datetime
from typing import Tuple

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils.utils import load_json, save_json, setup_logger

class RiskManager:
    """매수 주문 검증(6단계) 및 시스템 보호(서킷브레이커)를 담당하는 경비원 클래스"""
    
    def __init__(self):
        self.data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'daily_counters.json')
        self.daily_counters = self._load_daily_counters()
        
        # API 오류 카운터
        self.api_error_count = 0
        self.api_failure_threshold = 3
        
        # [설정값 초기화] - config.py에서 로드하거나 기본값 설정
        self.max_daily_trades = getattr(config, 'MAX_DAILY_TRADES', 10) # 일 최대 매수 횟수
        self.cash_buffer_ratio = getattr(config, 'CASH_BUFFER_RATIO', 0.1) 
        self.max_per_stock_ratio = getattr(config, 'MAX_PER_STOCK_RATIO', 0.15)
        self.max_per_sector = getattr(config, 'MAX_PER_SECTOR', 2) # 섹터당 최대 보유 종목
        self.max_positions = getattr(config, 'MAX_POSITIONS', 5)
        self.max_daily_loss = getattr(config, 'MAX_DAILY_LOSS', -0.05) # 일일 -5% 손실 시 정지
        
    def _load_daily_counters(self) -> dict:
        """일일 카운터 JSON 로드 및 날짜 변경 시 초기화"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        default_data = {
            'date': today_str,
            'trade_count': 0,
            'realized_pnl': 0,
            'buy_amount': 0,
            'start_asset': config.TOTAL_CAPITAL,
            'is_halted': False
        }
        
        data = load_json(self.data_path, default_data)
        
        # 날짜가 바뀌었으면 카운터 초기화
        if data.get('date') != today_str:
            data = default_data
            save_json(self.data_path, data)
            
        return data

    def reset_daily_counters(self):
        """매일 Step 0에서 호출, 일일 카운터 초기화"""
        today_str = datetime.now().strftime('%Y-%m-%d')
        self.daily_counters = {
            'date': today_str,
            'trade_count': 0,
            'realized_pnl': 0,
            'buy_amount': 0,
            'start_asset': config.TOTAL_CAPITAL, # 매일 아침 총 자산액으로 갱신 필요 (보통 메인 엔진에서 주입)
            'is_halted': False
        }
        save_json(self.data_path, self.daily_counters)
        logging.info("일일 거래 카운터가 성공적으로 초기화되었습니다.")

    def can_buy(self, symbol: str, amount: int, sector: str, current_positions: dict, market_mode: str) -> Tuple[bool, str]:
        """
        매수 가능 여부를 6단계로 체크합니다.
        
        Returns:
            (bool, str): (승인 여부, 거절 사유/승인 메시지)
        """
        # Stage 0: 시스템 정지 여부
        if self.daily_counters.get('is_halted', False):
            return False, "Stage 0 거절: 서킷브레이커 발동으로 시스템이 정지된 상태입니다."
            
        # Stage 1: 일일 거래 횟수
        if self.daily_counters['trade_count'] >= self.max_daily_trades:
            return False, f"Stage 1 거절: 일일 최대 매수 횟수({self.max_daily_trades}회) 초과"
            
        # Stage 2: 현금 버퍼 체크
        total_asset = self.daily_counters['start_asset'] + self.daily_counters['realized_pnl'] # 대략적인 현재 자산 추정
        remaining_cash = total_asset - self.daily_counters['buy_amount'] - amount
        if remaining_cash < (total_asset * self.cash_buffer_ratio):
            return False, f"Stage 2 거절: 매수 후 현금 버퍼({int(self.cash_buffer_ratio*100)}%) 미달 위험"
            
        # Stage 3: 종목당 최대 투자 비중
        if amount > (total_asset * self.max_per_stock_ratio):
            return False, f"Stage 3 거절: 종목당 최대 투자 비중({int(self.max_per_stock_ratio*100)}%) 초과"
            
        # Stage 4: 섹터당 최대 종목 수
        sector_count = sum(1 for pos in current_positions.values() if pos.get('sector', '') == sector)
        if sector_count >= self.max_per_sector:
            return False, f"Stage 4 거절: '{sector}' 섹터 최대 허용 종목수({self.max_per_sector}개) 초과"
            
        # Stage 5: 최대 보유 종목 수
        if len(current_positions) >= self.max_positions:
            return False, f"Stage 5 거절: 최대 보유 종목 수({self.max_positions}개) 초과"
            
        # Stage 6: 중복 보유 체크 (이미 있는 종목은 피라미딩 로직으로 타야 함)
        if symbol in current_positions:
            return False, f"Stage 6 거절: 신규 매수 불가 (이미 보유중인 종목. 피라미딩 대상)"
            
        return True, "승인: 모든 위험 관리 단계를 통과했습니다."

    def can_pyramid(self, symbol: str, current_stage: int, profit_rate: float, current_positions: dict) -> Tuple[bool, int, str]:
        """
        피라미딩(추가 매수) 가능 여부 판단
        
        Returns:
            (bool, int, str): (승인 여부, 다음 단계, 사유)
        """
        if self.daily_counters.get('is_halted', False):
            return False, current_stage, "거절: 서킷브레이커 발동 상태"
            
        if symbol not in current_positions:
             return False, current_stage, "거절: 보유중이지 않은 종목은 피라미딩 불가"

        if current_stage >= 3:
            return False, current_stage, "거절: 이미 최대 피라미딩(Stage 3) 도달"

        if current_stage == 1 and profit_rate >= 0.02:
            return True, 2, "승인: 수익률 +2% 돌파, Stage 1 -> 2 피라미딩 실행"
        elif current_stage == 2 and profit_rate >= 0.04:
            return True, 3, "승인: 수익률 +4% 돌파, Stage 2 -> 3 피라미딩 실행"
            
        return False, current_stage, f"거절: 수익률({profit_rate*100:.1f}%) 미달. 추가 매수 조건 불만족"

    def record_trade(self, pnl: int, trade_type: str, amount: int = 0):
        """
        거래 기록을 저장합니다.
        
        Args:
            pnl (int): 실현 손익금 (매도 시)
            trade_type (str): 'BUY' 또는 'SELL'
            amount (int): 매수 금액
        """
        if trade_type.upper() == 'BUY':
            self.daily_counters['trade_count'] += 1
            self.daily_counters['buy_amount'] += amount
        elif trade_type.upper() == 'SELL':
            self.daily_counters['realized_pnl'] += pnl
            self.check_daily_circuit_breaker() # 매도 후 일일 단위 서킷체크
            
        save_json(self.data_path, self.daily_counters)

    def check_daily_circuit_breaker(self) -> bool:
        """
        일일 실현 손익을 기반으로 서킷브레이커 발동 여부 체크 (-5% 이상 손실 시)
        """
        start_asset = self.daily_counters['start_asset']
        realized_pnl = self.daily_counters['realized_pnl']
        
        if start_asset > 0:
            loss_rate = realized_pnl / start_asset
            if loss_rate <= self.max_daily_loss: # ex. -0.06 <= -0.05
                self.daily_counters['is_halted'] = True
                save_json(self.data_path, self.daily_counters)
                logging.critical(f"🚨 서킷브레이커 발동! 일일 손실률({loss_rate*100:.2f}%)이 한도({self.max_daily_loss*100:.2f}%)를 초과했습니다.")
                return True
                
        return False

    def check_system_health(self) -> bool:
        """API 오류 등 시스템 상태 점검"""
        self.api_error_count += 1
        if self.api_error_count >= self.api_failure_threshold:
            self.daily_counters['is_halted'] = True
            save_json(self.data_path, self.daily_counters)
            logging.critical(f"🚨 시스템 정지! API 연속 오류({self.api_error_count}회)가 허용치를 초과했습니다.")
            return False
        return True
        
    def reset_system_health(self):
        """API 호출 성공 시 오류 카운터 초기화"""
        self.api_error_count = 0

    def calculate_real_profit(self, buy_price: float, sell_price: float, quantity: int) -> int:
        """
        수수료와 세금을 포함한 실수익금 계산
        매수 수수료: 0.015%, 매도 수수료: 0.015%, 거래세: 0.18%
        """
        buy_amount = buy_price * quantity
        sell_amount = sell_price * quantity
        
        # 비용 계산
        buy_fee = buy_amount * 0.00015
        sell_fee = sell_amount * 0.00015
        tax = sell_amount * 0.0018
        
        total_costs = buy_fee + sell_fee + tax
        gross_profit = sell_amount - buy_amount
        
        real_profit = int(gross_profit - total_costs)
        return real_profit
