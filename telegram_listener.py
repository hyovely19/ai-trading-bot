import os
import sys
import logging
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# 설정 값 가져오기용 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from src.common_utils import get_today_str, is_market_open_time, read_recent_logs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 명령어 입력시 나오는 메시지"""
    welcome_msg = (
        "👋 안녕하세요! AI 주식 자동매매 봇입니다.\n\n"
        "저는 현재 단방향 알림만 보내도록 설정되어 있었지만, 방금 양방향 소통 기능이 추가되었습니다!\n\n"
        "사용 가능한 명령어:\n"
        "/status - 봇의 현재 상태 확인\n"
        "/logs - 최근 봇 작업 로그 확인\n"
        "/help - 도움말 보기"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=welcome_msg)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status 명령어 입력시 봇 동작 상태 출력"""
    is_open = is_market_open_time()
    market_status = "🟢 정규장 진행 중" if is_open else "🔴 장 마감 / 대기 중"
    
    msg = (
        f"📊 [봇 현재 상태]\n\n"
        f"날짜: {get_today_str()}\n"
        f"시장 상태: {market_status}\n\n"
        f"✅ 봇이 정상적으로 프로그램을 모니터링하고 있습니다."
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/logs 명령어 입력시 최근 로그 10줄 출력"""
    logs = read_recent_logs(lines=10)
    msg = f"📜 *[최근 로그 10줄]*\n\n```text\n{logs}\n```"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 명령어 입력시 도움말 출력"""
    help_msg = (
        "💡 *[도움말]*\n\n"
        "저는 현재 여러분이 설정해둔 `config.py` 파일의 전략에 따라 매매를 수행합니다.\n"
        "장 중(09:00~15:30)에는 자동으로 종목을 탐색하고 매매를 진행합니다.\n\n"
        "궁금한 점이 있으시면 /logs 로 최근 기록을 확인해 보세요!"
    )
    await context.bot.send_message(chat_id=update.effective_chat.id, text=help_msg, parse_mode='Markdown')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지정되지 않은 일반 메시지 처리"""
    text = str(update.message.text).lower()
    msg = f"🤔 '{text}' 라고 말씀하셨군요.\n하지만 저는 아직 지정된 명령어만 처리할 수 있어요. /help 를 입력해 보세요!"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=msg)

def run_telegram_bot():
    """텔레그램 봇 리스너 실행 (Polling 방식)"""
    token = getattr(config, 'TELEGRAM_TOKEN', None)
    
    if not token:
        logging.error("TELEGRAM_TOKEN이 없습니다. 봇 리스너를 실행할 수 없습니다.")
        return

    # 봇 어플리케이션 생성
    app = ApplicationBuilder().token(token).build()

    # 명령어 핸들러 등록
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("logs", logs_command))
    app.add_handler(CommandHandler("help", help_command))

    # 일반 메시지 핸들러 등록 (텍스트일 경우)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logging.info("텔레그램 봇 리스너가 시작되었습니다. 메시지 수신 대기 중...")
    
    # 메시지 수신 무한 대기 (Polling)
    app.run_polling()

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    run_telegram_bot()
