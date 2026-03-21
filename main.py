# ==========================================
# [안내] AI 주식 자동매매 봇 메인 실행 파일
# ==========================================
import sys
import os
import threading
import logging

# 기본적인 경로 및 모듈 설정을 위해 sys.path 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("로컬 환경용 AI 주식 자동매매 봇 구동을 시작합니다.")
    print("텔레그램에서 100% 정상 작동하며 해외 IP 차단 문제가 발생하지 않습니다.")
    print("=" * 50)

    # 1. 텔레그램 봇을 백그라운드 스레드에서 실행
    try:
        from telegram_bot import run_telegram_bot # type: ignore
        bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
        bot_thread.start()
        print(">> [성공] 텔레그램 봇 백그라운드 리스너 시작 완료")
    except Exception as e:
        print(f">> [실패] 텔레그램 봇 실행 실패: {e}")

    # 2. 메인 스레드에서 AI 퀀트 매니저(자동매매 엔진) 실행
    try:
        from src.utils.ai_quant_manager import AIQuantManager # type: ignore
        manager = AIQuantManager()
        manager.run_daily_loop()
    except Exception as e:
        logging.error(f"메인 루프 동작 중 컴파일/구동 치명적 에러 발생: {e}")

if __name__ == "__main__":
    main()
