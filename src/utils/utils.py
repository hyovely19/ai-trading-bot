import json
import logging
import os
import sys

def setup_logger():
    """시스템 전체 로거 설정을 초기화합니다."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger()

def load_json(filepath: str, default_val=None):
    """지정된 경로의 JSON 파일을 안전하게 읽어옵니다."""
    if not os.path.exists(filepath):
        return default_val if default_val is not None else {}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"JSON 로드 오류 ({filepath}): {e}")
        return default_val if default_val is not None else {}

def save_json(filepath: str, data: dict):
    """지정한 데이터를 지정된 경로에 JSON 형식으로 안전하게 저장합니다."""
    try:
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"JSON 저장 오류 ({filepath}): {e}")
