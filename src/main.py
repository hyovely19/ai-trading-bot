# 프로그램이 시작되는 메인 파일입니다.
from api.koreainvestment import KoreaInvestmentAPI
from strategies.strategy import AIStrategy
from utils.logger import setup_logger

def run_trading_loop(api: KoreaInvestmentAPI, strategy: AIStrategy, logger):
    """
    매수/매도/조회를 계속해서 반복하는 실제 자동매매 핵심 함수입니다.
    
    Args:
        api (KoreaInvestmentAPI): 주식 조회/주문을 담당하는 객체
        strategy (AIStrategy): 투자를 판단하는 AI 객체
        logger: 상태를 기록할 로거 객체
    """
    pass

def main():
    """프로그램 실행 시 가장 먼저 실행되는 메인 함수입니다."""
    pass

if __name__ == "__main__":
    main()
