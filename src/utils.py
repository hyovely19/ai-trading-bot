import os
import sys
import json
import logging
from datetime import datetime
import requests

# 프로젝트 최상단 폴더 인식
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config

def ensure_directories():
    """data/, logs/, reports/ 폴더가 없으면 생성하는 함수"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    dirs_to_create = ['data', 'logs', 'reports']
    
    for dir_name in dirs_to_create:
        dir_path = os.path.join(base_dir, dir_name)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            # 아직 로거가 설정되기 전일 수 있으므로 print 사용
            print(f"📁 디렉토리 생성 완료: {dir_path}")

def setup_logger(name: str):
    """
    로거 생성 (파일 + 콘솔 출력)
    - 파일: logs/quant_YYYY-MM-DD.log (DEBUG 이상)
    - 콘솔: INFO 이상
    """
    ensure_directories()
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG) # 전체 로거 레벨은 가장 낮게 설정
    
    # 이미 등록된 핸들러가 있으면 중복 등록 방지
    if logger.hasHandlers():
        logger.handlers.clear()
        
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # 1. 콘솔 출력기 (INFO 이상)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 2. 파일 출력기 (DEBUG 이상)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_filename = os.path.join(base_dir, 'logs', f'quant_{get_today_str()}.log')
    
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# 전역에서 쓸 글로벌 로거 초기화
logger = setup_logger("AI_Quant")

def send_telegram_msg(message: str):
    """
    텔레그램 봇으로 메시지를 발송합니다.
    (오류 시 무한루프 방지를 위해 에러만 띄우고 넘어감)
    """
    token = getattr(config, 'TELEGRAM_TOKEN', None)
    chat_id = getattr(config, 'TELEGRAM_CHAT_ID', None)
    
    if not token or not chat_id:
        logger.warning("⚠️ 텔레그램 토큰이나 챗ID가 설정되지 않아 알림을 보낼 수 없습니다.")
        return
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown'
    }
    
    try:
        response = requests.post(url, data=payload, timeout=5)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ 텔레그램 알림 발송 실패: {e}")

def save_json(data: dict, filename: str):
    """
    딕셔너리를 data/{filename} 에 JSON 파일로 저장합니다. 
    (UTF-8, 들여쓰기 4칸)
    """
    ensure_directories()
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filepath = os.path.join(base_dir, 'data', filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"❌ JSON 저장 실패 ({filename}): {e}")

def load_json(filename: str):
    """
    data/{filename} 에서 JSON 파일을 읽어옵니다.
    파일이 없으면 빈 딕셔너리를 반환합니다.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    filepath = os.path.join(base_dir, 'data', filename)
    
    if not os.path.exists(filepath):
        return {}
        
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"❌ JSON 로드 실패 ({filename}): {e}")
        return {}

def get_today_str() -> str:
    """오늘 날짜를 'YYYY-MM-DD' 형식의 문자열로 반환합니다."""
    return datetime.now().strftime('%Y-%m-%d')

def is_weekday() -> bool:
    """오늘이 평일(월~금)인지 여부를 반환합니다. (토=5, 일=6)"""
    return datetime.now().weekday() < 5

def is_market_open_time() -> bool:
    """현재 시간이 한국 주식시장 정규장 운영 시간(09:00 ~ 15:30)인지 여부 반환"""
    now = datetime.now()
    # 9시 * 60 = 540분, 15시 30분 = 930분
    current_minutes = now.hour * 60 + now.minute
    return 540 <= current_minutes < 930

def read_recent_logs(lines: int = 20) -> str:
    """
    최근 로그 파일에서 마지막 N줄을 읽어서 반환합니다.
    (텔레그램 봇 등에서 "로그 확인" 요청 시 사용)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    log_filename = os.path.join(base_dir, 'logs', f'quant_{get_today_str()}.log')
    
    if not os.path.exists(log_filename):
        return "오늘자 로그 파일이 존재하지 않습니다."
        
    try:
        with open(log_filename, 'r', encoding='utf-8') as f:
            content = f.readlines()
            # 뒤에서부터 N줄만 가져옴
            recent_lines = content[-lines:] if len(content) > lines else content
            return "".join(recent_lines)
    except Exception as e:
        logger.error(f"❌ 로그 읽기 실패: {e}")
        return f"로그를 읽어오는 중 오류가 발생했습니다: {e}"

def update_account_history(total_asset: int, date: str):
    """
    일일 자산 기록을 account_history.json 파일에 추가합니다.
    """
    history_file = 'account_history.json'
    history_data = load_json(history_file)
    
    # 리스트 형태가 아니면 빈 리스트로 초기화
    if not isinstance(history_data, list):
        # 만약 dict로 잘못 저장되어 있었다면 비운다.
        if 'history' in history_data:
            history_data = history_data['history']
        else:
            history_data = []
            
    # 오늘 데이터 갱신/추가
    updated = False
    for record in history_data:
        if record.get('date') == date:
            record['total_asset'] = total_asset
            updated = True
            break
            
    if not updated:
        history_data.append({
            'date': date,
            'total_asset': total_asset
        })
        
    # 리스트 형태를 다시 딕셔너리로 감싸서 저장 (정규격)
    save_data = {'history': history_data}
    save_json(save_data, history_file)
    logger.info(f"📊 일일 자산 내역 저장 완료 ({date}: {total_asset:,}원)")
