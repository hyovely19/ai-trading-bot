import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

# 프로젝트 최상단 폴더 인식
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from src.utils import load_json, save_json, setup_logger

# 로거 설정
logger = setup_logger("AI_HitTracker")

class AIHitTracker:
    """AI 투자 모델의 예측 성공률(적중률)을 추적하고 매매 비중을 동적으로 조절하는 클래스"""
    
    def __init__(self):
        self.filename = "ai_predictions.json"
        self.predictions = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        """과거 예측 데이터 로드"""
        data = load_json(self.filename)
        if isinstance(data, dict) and 'predictions' in data:
            return data['predictions']
        return []

    def _save_data(self):
        """예측 데이터 저장"""
        save_json({'predictions': self.predictions}, self.filename)

    def record_prediction(self, symbol: str, name: str, price: float, score: int):
        """
        AI 추천 종목 기록 (Step 2에서 호출)
        동일 종목+날짜 중복 방지 및 최근 100건 유지
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 중복 체크
        for pred in self.predictions:
            if pred['symbol'] == symbol and pred['date'] == today:
                logger.info(f"알림: {name}({symbol})은 오늘 이미 기록되었습니다.")
                return

        new_pred = {
            'symbol': symbol,
            'name': name,
            'prediction_price': price,
            'prediction_score': score,
            'date': today,
            'result': 'PENDING', # HIT, MISS, PENDING
            'result_price': 0,
            'profit_rate': 0,
            'checked_date': None
        }
        
        self.predictions.insert(0, new_pred) # 최신순 정렬
        self.predictions = self.predictions[:100] # 최근 100건 유지
        self._save_data()
        logger.info(f"📝 AI 예측 기록 완료: {name}({symbol}), 점수: {score}")

    def update_results(self, broker) -> int:
        """
        5일 지난 예측의 결과 업데이트 (Step 0에서 호출)
        현재가 조회 -> 수익률 계산 -> (+3% 이상 HIT, 미만 MISS)
        """
        updated_count = 0
        now = datetime.now()
        check_days = getattr(config, 'HIT_RATE_CHECK_DAYS', 5)
        threshold = getattr(config, 'HIT_THRESHOLD_PCT', 0.03)

        for pred in self.predictions:
            # 아직 결과 확인 안 된 건만 대상
            if pred['result'] != 'PENDING':
                continue
            
            pred_date = datetime.strptime(pred['date'], '%Y-%m-%d')
            # 5일이 경과했는지 확인
            if now - pred_date >= timedelta(days=check_days):
                try:
                    current_price = broker.get_current_price(pred['symbol'])
                    if current_price:
                        profit_rate = (current_price - pred['prediction_price']) / pred['prediction_price']
                        pred['result_price'] = current_price
                        pred['profit_rate'] = profit_rate
                        pred['checked_date'] = now.strftime('%Y-%m-%d %H:%M:%S')
                        
                        if profit_rate >= threshold:
                            pred['result'] = 'HIT'
                        else:
                            pred['result'] = 'MISS'
                            
                        updated_count += 1
                        logger.info(f"✅ AI 결과 업데이트: {pred['name']} ({pred['result']}) - 수익률: {profit_rate*100:.2f}%")
                except Exception as e:
                    logger.error(f"❌ {pred['name']} 결과 업데이트 중 오류: {e}")

        if updated_count > 0:
            self._save_data()
            
        return updated_count

    def get_hit_rate(self) -> float:
        """
        현재 적중률 반환 (%, 최근 50건 기준)
        """
        # 결과가 나온 것들만 필터링
        results = [p for p in self.predictions if p['result'] in ['HIT', 'MISS']]
        recent_results = results[:50] # 최근 50건
        
        if not recent_results:
            return 50.0 # 데이터 없으면 기본값 50%
            
        hits = sum(1 for p in recent_results if p['result'] == 'HIT')
        hit_rate = (hits / len(recent_results)) * 100
        return round(hit_rate, 1)

    def get_dynamic_min_score(self) -> int:
        """
        적중률 기반 동적 최소 AI 점수 반환
        - 55% 이상 -> 65점
        - 45~55% -> 70점
        - 45% 미만 -> 80점
        """
        hit_rate = self.get_hit_rate()
        
        if hit_rate >= 55:
            return 65
        elif hit_rate >= 45:
            return 70
        else:
            return 80

    def get_dynamic_position_size(self) -> float:
        """
        적중률 기반 동적 투자 비중 반환
        - 55% 이상 -> 0.12 (12%)
        - 45~55% -> 0.10 (10%)
        - 45% 미만 -> 0.07 (7%)
        """
        hit_rate = self.get_hit_rate()
        
        if hit_rate >= 55:
            return 0.12
        elif hit_rate >= 45:
            return 0.10
        else:
            return 0.07

    def get_stats_summary(self) -> str:
        """텔레그램 리포트용 요약 문자열"""
        hit_rate = self.get_hit_rate()
        results = [p for p in self.predictions if p['result'] in ['HIT', 'MISS']]
        recent_results = results[:50]
        hits = sum(1 for p in recent_results if p['result'] == 'HIT')
        total = len(recent_results)
        
        status = "⚪ Normal"
        if hit_rate >= 55: status = "🟢 High"
        elif hit_rate < 45: status = "🔴 Low"
        
        return f"📊 AI 적중률: {hit_rate}% ({hits}/{total}건) - {status}"
