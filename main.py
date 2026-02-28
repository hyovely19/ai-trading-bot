import time
import config
from api_client import KISApiClient
from strategy import TradingStrategy

# ==========================================
# [메인 실행 파일] 전체 프로그램을 시작하고 제어
# ==========================================

def main():
    print("=" * 40)
    print(">> AI 주식 자동매매 봇을 시작합니다.")
    mode = "모의투자" if config.IS_MOCK else "실전투자"
    print(f">> 현재 모드: {mode}")
    print("=" * 40)
    
    # 1. API 접속 준비
    api = KISApiClient()
    api.get_access_token()
    
    # 2. 거래 전략 및 AI 준비
    strategy = TradingStrategy(api)
    
    # 3. 자동매매 메인 루프 (10초마다 반복 실행)
    print("\n>> 자동매매 모니터링 시작 (종료하려면 Ctrl+C 입력)")
    try:
        while True:
            for symbol in config.TARGET_SYMBOLS:
                strategy.execute_strategy(symbol)
            
            # 주식 시장에 과도한 요청이나 서버 과부하를 막기 위해 쉬는 시간 부여
            time.sleep(10) 
            
    except KeyboardInterrupt:
        print("\n>> 사용자에 의해 자동매매 프로그램이 안전하게 종료되었습니다.")

if __name__ == "__main__":
    main()
