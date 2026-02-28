import os

# ==========================================
# 자동매매 시스템 환경 설정 파일 (config.py)
# ==========================================
# 이 파일은 주식을 사고팔 때 기준이 되는 금액과 규칙들을 정해두는 곳입니다.
# 나중에 투자 전략을 바꾸고 싶다면 이 파일의 숫자들만 수정하시면 됩니다.

# [1. 자본금/현금 관리]
# 운용 기준 자본금 (기본값: 100,000,000원 = 모의투자 기본 제공)
TOTAL_CAPITAL = 100000000

# 평상시 최소 현금 비중 (기본값: 0.10 = 10%)
CASH_BUFFER_RATIO = 0.10

# 최대 보유 종목 수 (기본값: 5)
MAX_POSITIONS = 5

# 종목당 최대 투자 비중 (기본값: 0.10 = 10%)
MAX_PER_STOCK_RATIO = 0.10

# 1회 투자 비중 (비율) - 기존 속성 유지 (MAX_PER_STOCK_RATIO와 용도 유사)
INVESTMENT_RATIO = 0.10

# [2. 손절/익절 규칙]
# 손절 기준 (기본값: -0.07 = -7%)
# 주식 가격이 떨어졌을 때 더 큰 손해를 막기 위해 파는 기준입니다.
STOP_LOSS_RATE = -0.07

# 목표 수익률 (기존 익절 기준 유지)
TARGET_PROFIT_RATE = 0.05

# 손절 유예 거래일 수 (기본값: 7)
FORGIVENESS_COUNT = 7

# 1차 익절 기준 (기본값: 0.06 = +6%, 보유량 50% 매도)
TAKE_PROFIT_HALF = 0.06

# 2차 익절 기준 (기본값: 0.125 = +12.5%, 전량 매도)
TAKE_PROFIT_FULL = 0.125


# [3. 피라미딩 (분할 매수)]
# 1단계 비중 (기본값: 0.30 = 30%)
PYRAMID_STAGE_1 = 0.30

# 2단계 비중 (기본값: 0.30 = 30%)
PYRAMID_STAGE_2 = 0.30

# 3단계 비중 (기본값: 0.40 = 40%)
PYRAMID_STAGE_3 = 0.40

# 2단계 진입 조건 (기본값: 0.02 = +2%)
PYRAMID_TRIGGER_2 = 0.02

# 3단계 진입 조건 (기본값: 0.04 = +4%)
PYRAMID_TRIGGER_3 = 0.04


# [4. AI 설정]
# 최소 AI 점수 (기본값: 70)
MIN_AI_SCORE = 70

# GEMINI_API_KEY: 환경변수에서 가져오기
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


# [5. 거시경제 임계값]
# VIX 공포 기준 (기본값: 30)
VIX_STORMY_THRESHOLD = 30

# VIX 불안 기준 (기본값: 20)
VIX_CLOUDY_THRESHOLD = 20


# [6. 일일 한도/안전장치]
# 하루 최대 거래 허용 횟수
# 프로그램이 오작동하여 하루 종일 주식을 사고파는 것을 막기 위한 안전장치입니다.
MAX_DAILY_TRADES = 10

# 일일 최대 허용 손실률 (기본값: -0.05 = -5%)
MAX_DAILY_LOSS = -0.05


# [7. 텔레그램 설정]
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")


# [8. 한투 API 설정]
KIS_APP_KEY = os.environ.get("KIS_APP_KEY")
KIS_APP_SECRET = os.environ.get("KIS_APP_SECRET")
KIS_ACCOUNT_NO = os.environ.get("KIS_ACCOUNT_NO")

# 증권사 서버 요청 간격 (단위: 초) - 기존 유지
# 너무 자주 요청하면 접속 차단될 수 있으므로 대기시간을 설정합니다.
API_REQUEST_INTERVAL = 1.0


# [9. 종목 유니버스]
# 매매 대상 종목 리스트 (기본 10개 종목)
UNIVERSE = [
    {"code": "005930", "name": "삼성전자", "sector": "IT/반도체"},
    {"code": "000660", "name": "SK하이닉스", "sector": "IT/반도체"},
    {"code": "373220", "name": "LG에너지솔루션", "sector": "에너지/배터리"},
    {"code": "005380", "name": "현대차", "sector": "자동차"},
    {"code": "035420", "name": "NAVER", "sector": "IT/플랫폼"},
    {"code": "035720", "name": "카카오", "sector": "IT/플랫폼"},
    {"code": "207940", "name": "삼성바이오로직스", "sector": "제약/바이오"},
    {"code": "241520", "name": "DSC인베스트먼트", "sector": "창투/벤처캐피탈"}, # POSCO홀딩스 대체
    {"code": "016360", "name": "삼성증권", "sector": "금융/증권"},        # KB금융 대체
    {"code": "161890", "name": "한국콜마", "sector": "화장품/제조"}       # 셀트리온 대체
]

# 기존 참조 코드(TARGET_STOCKS)와의 호환성을 위한 리스트
TARGET_STOCKS = [stock["code"] for stock in UNIVERSE]


# [10. 파일/디렉토리]
DATA_DIR = "data"
LOG_DIR = "logs"
REPORT_DIR = "reports"
