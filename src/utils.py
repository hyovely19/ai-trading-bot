# 프로그램 여러 곳에서 공통으로 자주 쓰이는 도우미(Helper) 함수들을 모아둔 파일입니다.
# 예: 날짜/시간 계산, 숫자를 보기 좋게 콤마(,) 찍기 등

from datetime import datetime, timedelta

def get_current_time_str() -> str:
    """
    현재 시간을 보기 좋은 문자열 형태(YYYY-MM-DD HH:MM:SS)로 돌려줍니다.
    
    Returns:
        str: 현재 시간 문자열
    """
    pass

def is_market_open() -> bool:
    """
    지금이 한국 주식 시장이 열려있는 시간(평일 오전 9시 ~ 오후 3시 30분)인지 확인합니다.
    (주말이나 공휴일, 장 마감 이후에는 거래를 시도하지 않도록 방지합니다.)
    
    Returns:
        bool: 장 중이면 True, 장이 닫혀있으면 False
    """
    pass

def format_price_with_comma(price: int) -> str:
    """
    1000000 처럼 보기 힘든 숫자를 '1,000,000' 처럼 알아보기 쉽게 콤마를 찍어줍니다.
    
    Args:
        price (int): 원본 숫자
        
    Returns:
        str: 콤마가 찍힌 문자열
    """
    pass

def calculate_fee_and_tax(sell_price: int, quantity: int) -> int:
    """
    주식을 팔 때 발생하는 증권사 수수료와 세금을 대략적으로 계산해 줍니다.
    (실제 수익을 정확하게 파악하기 위해 필요합니다.)
    
    Args:
        sell_price (int): 매도 가격
        quantity (int): 파는 수량
        
    Returns:
        int: 예상되는 세금 및 수수료의 총합
    """
    pass
