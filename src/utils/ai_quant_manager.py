import time
import datetime
import os
import json
import logging
from typing import Dict, List, Any

# 구글 Gemini 연동 패키지: google-genai 기준
try:
    from google import genai
except ImportError:
    pass # 실제 환경에 맞게 설치 필요

import sys
# 프로젝트 최상위 경로(ai_trading_bot)를 sys.path에 추가하여 패키지를 정상적으로 찾도록 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 시스템 설정 파일 불러오기
try:
    import config
    from src.utils.risk_manager import RiskManager
    from src.utils.ai_hit_tracker import AIHitTracker
    from src.common_utils import logger, send_telegram_msg
    # 통신 및 API 모듈
    from src.api.koreainvestment import KoreaInvestmentAPI
except ImportError as e:
    logging.error(f"필수 모듈 임포트 에러: {e}")
    pass

# 로깅 기본 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

class AIQuantManager:
    """
    매일 자동으로 실행되는 주식 자동매매 시스템의 메인 엔진 클래스.
    7단계 일일 루틴(초기화 -> 거시경제 분석 -> 종목 선정 -> 매수 실행 -> 모니터링 -> 종료 전략 -> 리포트)을 순서대로 실행합니다.
    """
    
    def __init__(self):
        """시스템 운영에 필요한 기본 설정 및 상태 변수를 초기화합니다."""
        logging.info("AI Quant Manager 초기화 시작")
        
        # API 클라이언트 초기화
        self.kis_api = KoreaInvestmentAPI()
        self.risk_manager = RiskManager() if 'RiskManager' in globals() else None
        
        # 포지션(보유 종목) 데이터 구조
        # key: 종목코드, value: dict(name, quantity, avg_price, stop_loss, target_price, pyramid_stage, highest_price, consecutive_down_days)
        self.positions: Dict[str, Any] = {}
        
        # 당일 트레이딩 모드 (AGGRESSIVE, MODERATE, DEFENSIVE)
        self.trading_mode = "AGGRESSIVE"
        
        # 당일 매수 가능 종목 수 
        self.max_today_positions = config.MAX_POSITIONS
        
        # 기타 상태 변수
        self.total_assets = 0.0
        self.cash_balance = 0.0
        self.is_running = False

    def send_telegram_msg(self, message: str):
        """
        텔레그램 알림 발송 함수 (가상 구현 없음 - 실제 발송)
        """
        logging.info(f"텔레그램 알림 발송: {message}")
        try:
            send_telegram_msg(message)
        except Exception as e:
            logging.error(f"텔레그램 발송 실패: {e}")

    # =========================================================================
    # 7단계 일일 루틴 구현
    # =========================================================================

    def step_0_initialize(self):
        """
        Step 0: 초기화 (08:20 이전 수행)
        - 한투 API 토큰 확인/재발급
        - 거래일 확인 (주말/공휴일 대기)
        - 잔고 조회 및 포지션 동기화
        """
        logging.info("Step 0: 초기화 진행 중...")
        
        # 1. API 토큰 재발급 로직
        self.kis_api.get_access_token()
        
        # 2. 거래일 확인 (주말 체크)
        today = datetime.datetime.now()
        if today.weekday() >= 5: # 토=5, 일=6
            logging.info("오늘은 주말(휴장일)입니다. 다음 거래일까지 대기합니다.")
            self.send_telegram_msg("💤 [안내] 오늘은 주말(휴장일)입니다. 다음 거래일까지 대기합니다.")
            return False
            
        # 3. 잔고 조회 및 포지션 동기화
        for _ in range(3):
            try:
                balance_data = self.kis_api.get_account_balance()
                if balance_data:
                    self.cash_balance = balance_data['cash']
                    self.total_assets = balance_data['total']
                    # 포지션 동기화
                    self.positions = {}
                    for s in balance_data['stocks']:
                        self.positions[s['code']] = {
                            "name": s['name'],
                            "quantity": s['qty'],
                            "avg_price": s['avg_price'],
                            "stop_loss": s['avg_price'] * (1 + config.STOP_LOSS_RATE),
                            "target_price": s['avg_price'] * (1 + config.TAKE_PROFIT_FULL),
                            "pyramid_stage": 1,
                            "highest_price": s['avg_price'],
                            "consecutive_down_days": 0
                        }
                    break
            except Exception as e:
                logging.warning(f"잔고 조회 실패 (재시도 중..): {e}")
                time.sleep(2)
        else:
            logging.error("잔고 조회 3회 연속 실패. 시스템을 점검해 주세요.")
            self.send_telegram_msg("[비상] 잔고 조회 실패로 자동매매를 일시 중지합니다.")
            return False
            
        return True

    def step_1_macro_analysis(self):
        """
        Step 1: 거시경제 분석 (08:20)
        - VIX, 나스닥 등락률, 환율, 유가 데이터 수집 (가상)
        - 트레이딩 모드 결정 및 One-Way Downgrade 적용
        """
        logging.info("Step 1: 거시경제 분석 중...")
        
        # 가상 데이터 수집
        vix = 18.5
        nasdaq_change = 0.5   # %
        exchange_rate_change = 0.2  # %
        oil_change = -1.0     # %
        
        # 모드 결정 로직
        new_mode = "AGGRESSIVE" # 초기값
        allowed_positions = config.MAX_POSITIONS
        
        # VIX 기준 (MODERATE 조건 우선)
        if config.VIX_CLOUDY_THRESHOLD <= vix < config.VIX_STORMY_THRESHOLD:
            new_mode = "MODERATE"
            allowed_positions = min(5, config.MAX_POSITIONS)
            
        # 보조 지표 MODERATE 기준
        if nasdaq_change <= -1.0 or exchange_rate_change >= 1.0 or abs(oil_change) >= 5.0:
            if new_mode == "AGGRESSIVE":
                new_mode = "MODERATE"
                allowed_positions = min(5, config.MAX_POSITIONS)

        # 절대 방어(DEFENSIVE) 기준
        if vix >= config.VIX_STORMY_THRESHOLD or nasdaq_change <= -2.0 or exchange_rate_change >= 2.0 or abs(oil_change) >= 7.0:
            new_mode = "DEFENSIVE"
            allowed_positions = 0
            
        # One-Way Downgrade 검사: 기존 모드보다 위험한(안전하지 않은) 모드로 상향 금지
        mode_rank = {"AGGRESSIVE": 3, "MODERATE": 2, "DEFENSIVE": 1}
        if mode_rank[new_mode] < mode_rank[self.trading_mode]:
            # 하향 조정 적용
            self.trading_mode = new_mode
            self.max_today_positions = allowed_positions
            
        logging.info(f"오늘의 트레이딩 모드: {self.trading_mode} (최대 {self.max_today_positions}종목 매수 가능)")
        self.send_telegram_msg(f"[오늘의 시장 분석]\n모드: {self.trading_mode}\n매수 가능 수: {self.max_today_positions}개")

    def analyze_with_gemini(self, stock_info: Dict) -> Dict:
        """
        Step 2 보조: Gemini AI로 특정 종목을 분석하고 점수를 반환받습니다.
        """
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY가 없습니다. 기본 점수 50으로 처리합니다.")
            return {"score": 50, "target_price": 0, "stop_loss": 0, "reason": "키 누락"}
            
        try:
            client = genai.Client(api_key=api_key)
            prompt = f"""
            당신은 최고의 주식 퀀트 분석가입니다. 다음 종목에 대해 분석해 주세요: {stock_info['name']} ({stock_info['code']}).
            반드시 아래 3가지를 종합 평가하여 100점 만점으로 점수를 내주세요.
            1. 뉴스 모멘텀 점수 (30점)
            2. 기술적 차트 분석 점수 (40점)
            3. 손익비 점수 (30점)
            
            분석이 끝나면 오직 아래 형식의 JSON 형태 데이터만 반환해 주세요.
            {{"total_score": 85, "target_price": 90000, "stop_loss_price": 75000, "reason": "간단한 근거 1줄"}}
            """
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            # JSON 파싱 시도 (간단한 처리)
            cleaned_text = response.text.replace('```json', '').replace('```', '').strip()
            result = json.loads(cleaned_text)
            return {
                "score": result.get("total_score", 0),
                "target_price": result.get("target_price", 0),
                "stop_loss": result.get("stop_loss_price", 0),
                "reason": result.get("reason", "")
            }
        except Exception as e:
            logging.error(f"Gemini API 호출 중 에러 발생: {e}")
            return {"score": 0, "target_price": 0, "stop_loss": 0, "reason": "분석 실패"}

    def step_2_select_stocks(self) -> List[Dict]:
        """
        Step 2: 종목 선정 (08:30)
        - config.py의 UNIVERSE 리스트 가져오기
        - Gemini AI 대상 분석 -> MIN_AI_SCORE 이상만 필터링
        """
        logging.info("Step 2: 관심 종목 AI 분석 중...")
        if self.trading_mode == "DEFENSIVE":
            logging.info("모드가 DEFENSIVE이므로 신규 종목 선정을 건너뜁니다.")
            return []
            
        selected_stocks = []
        for stock in config.UNIVERSE:
            ai_result = self.analyze_with_gemini(stock)
            logging.info(f"[{stock['name']}] AI 평가 점수: {ai_result['score']}점")
            
            if ai_result['score'] >= config.MIN_AI_SCORE:
                selected_stocks.append({
                    "code": stock['code'],
                    "name": stock['name'],
                    "score": ai_result['score'],
                    "target": ai_result['target_price'],
                    "stop": ai_result['stop_loss']
                })
                
        # 점수 높은 순 정렬 후 모드별 개수만큼 자르기
        selected_stocks.sort(key=lambda x: x['score'], reverse=True)
        final_list = selected_stocks[:self.max_today_positions]
        
        logging.info(f"선정된 매수 대상 종목: {[s['name'] for s in final_list]}")
        return final_list

    def step_3_execute_buy(self, selected_stocks: List[Dict]):
        """
        Step 3: 매수 실행 (09:00 이후 장 시작 후)
        - 선정된 종목 시장가(또는 지정가) 1단계 30% 매수
        """
        logging.info("Step 3: 신규 매수 주문 실행 중...")
        
        for stock in selected_stocks:
            code = stock['code']
            
            # 이미 꽉 차있으면 포기
            if len(self.positions) >= self.max_today_positions:
                break
                
            # 이미 보유 중이면 피라미딩(추가 매수) 루틴으로 넘김
            if code in self.positions:
                continue
                
            # 매수 전 RiskManager 확인 (가상)
            # if not self.risk_manager.can_buy(self.cash_balance, ...): continue
            
            # 피라미딩 1단계 비중(30%)로 투입 금액 계산
            invest_amount = (config.TOTAL_CAPITAL * config.MAX_PER_STOCK_RATIO) * config.PYRAMID_STAGE_1
            current_price = self.kis_api.get_current_price(code) or 1 # 수량 계산을 위한 현재가
            buy_qty = int(invest_amount / current_price) if current_price > 0 else 0
            
            if buy_qty <= 0: continue
            
            try:
                # 실제 KIS API 매수 주문 호출 (시장가)
                res = self.kis_api.buy_market_order(code, buy_qty)
                
                if res and res.get('rt_cd') == '0':
                    buy_price = float(res.get('output', {}).get('ord_unpr', 0)) or 0 # 실제 체결가는 나중에 확인 필요할 수 있음
                    # 임시로 현재가 등으로 보정하거나 응답값 활용
                    buy_price = buy_price if buy_price > 0 else 0 # (실제 구현에선 체결 조회 API 필요)
                    # 포지션 등록
                    self.positions[code] = {
                        "name": stock['name'],
                        "quantity": buy_qty,
                        "avg_price": buy_price,
                        "stop_loss": buy_price * (1 + config.STOP_LOSS_RATE),
                        "target_price": buy_price * (1 + config.TAKE_PROFIT_FULL),
                        "pyramid_stage": 1,
                        "highest_price": buy_price,
                        "consecutive_down_days": 0
                    }
                    
                    self.cash_balance -= (buy_qty * buy_price)
                    msg = f"[신규 매수 성공]\n- 종목: {stock['name']}\n- 체결단가: {buy_price}원\n- 피라미딩 1단계(30%) 완료"
                    self.send_telegram_msg(msg)
            except Exception as e:
                logging.error(f"{stock['name']} 매수 주문 실패: {e}")

    def step_4_monitor_and_manage(self):
        """
        Step 4: 모니터링 (09:00 ~ 15:00)
        - 10분 주기로 보유 종목 가격 확인
        - 손절(Tit-for-Two-Tat), 익절, 트레일링 스탑, 피라미딩 처리
        """
        logging.info("Step 4: 보유 종목 모니터링 중...")
        
        # 순회 중 삭제 위험이 있으므로 키 리스트 복사
        for code in list(self.positions.keys()):
            pos = self.positions[code]
            
            # 현재가 조회 (실제 KIS API 호출)
            current_price = self.kis_api.get_current_price(code)
            if not current_price: continue
            
            # 최고가 업데이트 (트레일링 스탑 용)
            if current_price > pos['highest_price']:
                pos['highest_price'] = current_price
                
            profit_rate = (current_price - pos['avg_price']) / pos['avg_price']
            
            # 1. 트레일링 스탑 체크 (고점 대비 -2% 하락)
            # 여기서는 수익 중일 때 최고가 대비 떨어지는 것을 감시합니다.
            if profit_rate > 0:
                highest_profit_rate = (pos['highest_price'] - pos['avg_price']) / pos['avg_price']
                if profit_rate <= (highest_profit_rate - 0.02):
                    self._execute_sell(code, "트레일링 스탑 작동", current_price)
                    continue

            # 2. 손절 체크 (Tit-for-Two-Tat 로직)
            if current_price <= pos['stop_loss']:
                pos['consecutive_down_days'] += 1
                if pos['consecutive_down_days'] >= config.FORGIVENESS_COUNT:
                    self._execute_sell(code, "손절 유예 만료 (손절 처분)", current_price)
                    continue
            else:
                # 회복 시 유예 카운트 리셋
                pos['consecutive_down_days'] = 0
                
            # 3. 익절 체크
            if profit_rate >= config.TAKE_PROFIT_FULL:
                self._execute_sell(code, "목표가 달성 (전량 매도)", current_price)
                continue
            elif profit_rate >= config.TAKE_PROFIT_HALF:
                # 절반 매도 (여기서는 간단히 출력만 하고 수량을 반으로 줄인다고 가정)
                logging.info(f"{pos['name']} 1차 익절(절반 매도) 조건 도달")
                
            # 4. 피라미딩 기회 체크 (불타기)
            if pos['pyramid_stage'] == 1 and profit_rate >= config.PYRAMID_TRIGGER_2:
                self._execute_pyramiding(code, 2, current_price)
            elif pos['pyramid_stage'] == 2 and profit_rate >= config.PYRAMID_TRIGGER_3:
                self._execute_pyramiding(code, 3, current_price)

    def _execute_sell(self, code: str, reason: str, sell_price: float):
        """내부 유틸: 특정 종목 전량 매도 수행"""
        pos = self.positions[code]
        try:
            # 실제 KIS API 매도 주문 호출
            res = self.kis_api.sell_market_order(code, pos['quantity'])
            
            if res and res.get('rt_cd') == '0':
                msg = f"[매도 완료]\n- 종목: {pos['name']}\n- 사유: {reason}"
                self.send_telegram_msg(msg)
                # 포지션에서 제거
                del self.positions[code]
            else:
                logging.error(f"{pos['name']} 매도 주문 거부: {res.get('msg1')}")
        except Exception as e:
            logging.error(f"{pos['name']} 매도 실패: {e}")

    def _execute_pyramiding(self, code: str, next_stage: int, current_price: float):
        """내부 유틸: 피라미딩(추가 매수) 수행"""
        pos = self.positions[code]
        try:
            ratio = config.PYRAMID_STAGE_2 if next_stage == 2 else config.PYRAMID_STAGE_3
            invest_amount = (config.TOTAL_CAPITAL * config.MAX_PER_STOCK_RATIO) * ratio
            
            # API 추가 매수 호출 부분 (가상)
            add_qty = 5
            
            # 평단가 재계산
            total_value = (pos['avg_price'] * pos['quantity']) + (current_price * add_qty)
            new_qty = pos['quantity'] + add_qty
            new_avg_price = total_value / new_qty
            
            self.cash_balance -= (current_price * add_qty)
            pos['quantity'] = new_qty
            pos['avg_price'] = new_avg_price
            pos['pyramid_stage'] = next_stage
            
            msg = f"[피라미딩 {next_stage}차 추매]\n- 종목: {pos['name']}\n- 평단가 변경: {new_avg_price:,.0f}원"
            self.send_telegram_msg(msg)
        except Exception as e:
            logging.error(f"{pos['name']} 추매 실패: {e}")

    def step_5_closing_strategy(self):
        """
        Step 5: 종료 전략 (15:00)
        - CASH_BUFFER_RATIO 를 위한 현금 강제 확보
        - 모자랄 경우 수익률 가장 낮은 종목부터 눈물의 매도 처리
        """
        logging.info("Step 5: 장 마감 전 종료 전략 및 현금 확보 점검 중...")
        
        target_cash = self.total_assets * config.CASH_BUFFER_RATIO
        
        while self.cash_balance < target_cash and len(self.positions) > 0:
            logging.warning("현금 비중이 기준치보다 부족합니다. 가장 안 좋은 종목을 정리합니다.")
            
            # 현재 모든 보유 종목의 임시 수익률 계산하여 리스트화
            eval_list = []
            for code, pos in self.positions.items():
                current_price = pos['avg_price'] # 임시로 평단가로 퉁침
                profit_rate = (current_price - pos['avg_price']) / pos['avg_price']
                eval_list.append((code, profit_rate, current_price))
                
            # 수익률 오름차순(낮은 것부터) 정렬
            eval_list.sort(key=lambda x: x[1])
            
            worst_code = eval_list[0][0]
            worst_price = eval_list[0][2]
            
            self._execute_sell(worst_code, "현금 비중 확보를 위한 강제 매도", worst_price)

    def step_6_daily_report(self):
        """
        Step 6: 일일 리포트 (15:30)
        - 오늘의 성과 집계 후 텔레그램 발송
        """
        logging.info("Step 6: 일일 리포트 작성 중...")
        
        msg = f"""
        [AI Quant 일일 마감 리포트]
        - 총 자산: {self.total_assets:,.0f} 원
        - 남은 현금: {self.cash_balance:,.0f} 원
        - 보유 주식수: {len(self.positions)} 개
        오늘 하루도 수고하셨습니다! 내일 뵙겠습니다.
        """
        self.send_telegram_msg(msg)

    # =========================================================================
    # 메인 루프 실행
    # =========================================================================
        
    def run_daily_loop(self):
        """
        무한 루프로 7단계 루틴을 시간에 맞춰 실행하는 메인 엔진 루프입니다.
        (테스트를 위해 시간 체류 코드는 주석 처리, 로직 흐름만 구성)
        """
        self.is_running = True
        logging.info("AI Quant 메인 루프를 시작합니다.")
        
        try:
            while self.is_running:
                # -----------------------------
                # 실전에서는 datetime.now()를 체크하여 
                # 각 시각에 도달하면 동작. 
                # 여기서는 테스트용으로 순차 실행.
                # -----------------------------
                
                # Step 0: 08:20 이전 (초기화)
                is_ready = self.step_0_initialize()
                
                if is_ready:
                    # Step 1: 08:20 (거시경제 파악)
                    self.step_1_macro_analysis()
                    
                    # Step 2: 08:30 (종목 AI 분석)
                    selected_stocks = self.step_2_select_stocks()
                    
                    # Step 3: 09:00 (신규 매수 실행)
                    self.step_3_execute_buy(selected_stocks)
                    
                    # Step 4: 09:00 ~ 15:00 (10분 주기 모니터링)
                    # (테스트용으로 1회만 실행)
                    self.step_4_monitor_and_manage()
                    
                    # Step 5: 15:00 (현금 확보 등 종료 전략)
                    self.step_5_closing_strategy()
                    
                    # Step 6: 15:30 (마감 보고서)
                    self.step_6_daily_report()
                
                # 하루 사이클 종료 후, 실전에서는 다음날 08:20까지 sleep 합니다.
                logging.info("오늘의 정규 루틴이 모두 끝났습니다. 다음 거래일까지 대기합니다.")
                # 방지턱: 시연용이므로 루프를 한 번만 돌고 종료하도록 설정합니다.
                # time.sleep(86400) 
                break 

        except KeyboardInterrupt:
            logging.info("사용자 인터럽트로 시스템을 안전하게 종료합니다 (Graceful Shutdown).")
            self.is_running = False
        except Exception as e:
            logging.error(f"메인 루프 동작 중 치명적 에러 발생: {e}")
            self.send_telegram_msg("[비상] 봇 동작 중 치명적 오류가 발생했습니다. 로그를 확인하세요.")

if __name__ == "__main__":
    manager = AIQuantManager()
    manager.run_daily_loop()
