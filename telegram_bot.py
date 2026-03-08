import os
import sys
import logging
import asyncio
from telegram import Update # type: ignore
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes # type: ignore

try:
    from google import genai # type: ignore
except ImportError:
    genai = None

# 설정 값 가져오기용 패키지 경로 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config # type: ignore
from src.common_utils import get_today_str, is_market_open_time, read_recent_logs # type: ignore

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start 명령어 입력시 나오는 메시지"""
    chat = update.effective_chat
    if not chat: return
    welcome_msg = (
        "👋 안녕하세요! AI 주식 자동매매 봇입니다.\n\n"
        "저는 현재 단방향 알림만 보내도록 설정되어 있었지만, 방금 양방향 소통 기능이 추가되었습니다!\n\n"
        "사용 가능한 명령어:\n"
        "/status - 봇의 현재 상태 확인\n"
        "/logs - 최근 봇 작업 로그 확인\n"
        "/help - 도움말 보기"
    )
    await context.bot.send_message(chat_id=chat.id, text=welcome_msg)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/status 명령어 입력시 봇 동작 상태 출력"""
    chat = update.effective_chat
    if not chat: return
    is_open = is_market_open_time()
    market_status = "🟢 정규장 진행 중" if is_open else "🔴 장 마감 / 대기 중"
    
    msg = (
        f"📊 [봇 현재 상태]\n\n"
        f"날짜: {get_today_str()}\n"
        f"시장 상태: {market_status}\n\n"
        f"✅ 봇이 정상적으로 프로그램을 모니터링하고 있습니다."
    )
    await context.bot.send_message(chat_id=chat.id, text=msg)

async def logs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/logs 명령어 입력시 최근 로그 10줄 출력"""
    chat = update.effective_chat
    if not chat: return
    logs = read_recent_logs(lines=10)
    msg = f"📜 *[최근 로그 10줄]*\n\n```text\n{logs}\n```"
    await context.bot.send_message(chat_id=chat.id, text=msg, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/help 명령어 입력시 도움말 출력"""
    chat = update.effective_chat
    if not chat: return
    help_msg = (
        "💡 *[도움말]*\n\n"
        "저는 현재 여러분이 설정해둔 `config.py` 파일의 전략에 따라 매매를 수행합니다.\n"
        "장 중(09:00~15:30)에는 자동으로 종목을 탐색하고 매매를 진행합니다.\n\n"
        "궁금한 점이 있으시면 /logs 로 최근 기록을 확인해 보세요!"
    )
    await context.bot.send_message(chat_id=chat.id, text=help_msg, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/balance 명령어 입력시 현재 주식 및 현금 잔고 출력"""
    chat = update.effective_chat
    if not chat: return
    chat_id = chat.id
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    try:
        from src.api.koreainvestment import KoreaInvestmentAPI # type: ignore
        api = KoreaInvestmentAPI()
        api.get_access_token()
        balance_data = api.get_account_balance()
        
        if not balance_data:
            await context.bot.send_message(chat_id=chat_id, text="⚠️ 봇 시스템 오류로 잔고 정보를 불러오는데 실패했습니다.")
            return
            
        if 'error' in balance_data:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ 증권사 API 통신 거절: {balance_data['error']}\n\n(클라우드 서버나 해외 IP에서 접속하여 차단되었을 확률이 매우 높습니다. Railway 서버를 정지해주세요.)")
            return
            
        cash = balance_data.get('cash', 0)
        total = balance_data.get('total', 0)
        stocks = balance_data.get('stocks', [])
        
        msg = f"💰 *[현재 계좌 잔고 (로컬 정상 연결)]*\n\n"
        msg += f"💵 *주문 가능 현금:* {cash:,.0f} 원\n"
        msg += f"🏦 *총 평가 금액:* {total:,.0f} 원\n\n"
        
        if stocks:
            msg += "📊 *[보유 종목]*\n"
            for s in stocks:
                msg += f"• {s['name']} : {s['qty']}주 (평단가 {s['avg_price']:,.0f}원)\n"
        else:
            msg += "텅~ 현재 보유 중인 주식이 없습니다."
            
        await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode='Markdown')
        
    except Exception as e:
        logging.error(f"잔고 조회 중 에러: {e}")
        await context.bot.send_message(chat_id=chat_id, text=f"⚠️ 잔고 조회 중 에러가 발생했습니다: {e}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """지정되지 않은 일반 메시지를 AI 비서처럼 답변"""
    chat = update.effective_chat
    if not chat: return
    chat_id = chat.id
    
    msg_obj = update.message
    if not msg_obj or not msg_obj.text: return
    user_text = msg_obj.text
    
    # 자연어 명령어 맵핑 (한국어로 자연스럽게 물어봐도 동작하도록)
    if any(keyword in user_text for keyword in ["잔고", "자산", "얼마", "계좌"]):
        await balance_command(update, context)
        return
        
    # Gemini API 키 확인
    api_key = getattr(config, 'GEMINI_API_KEY', None)
    if not api_key or not genai:
        reason = f"KEY:{'O' if api_key else 'X'}, GENAI:{'O' if genai else 'X'}"
        msg = f"죄송합니다. 현재 설정 문제({reason})로 인해 정해진 명령어만 수행할 수 있습니다. /help 를 참고해주세요."
        await context.bot.send_message(chat_id=chat_id, text=msg)
        return

    # 타이핑 중이라는 상태 표시 송신 (사용자 입장에서 로딩중 느낌)
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')
    
    try:
        # Gemini 클라이언트 초기화 및 프롬프트 전송
        client = genai.Client(api_key=api_key) # type: ignore
        
        system_prompt = (
            "당신은 'AI 주식 자동매매 봇'의 친절한 비서입니다. "
            "사용자의 질문에 한국어로 친절하고 알기 쉽게 답변해주세요. "
            "주식 매매 상황이나 시스템 관련 질문이 아니어도 일상적인 대화에 자연스럽게 응답하면 됩니다.\n"
        )
        
        # 🤖 AI가 실제 데이터도 알고 있도록 최신 계좌 상태를 귓속말로 전달
        try:
            from src.api.koreainvestment import KoreaInvestmentAPI # type: ignore
            api = KoreaInvestmentAPI()
            api.get_access_token()
            balance_data = api.get_account_balance()
            
            if balance_data:
                cash = balance_data.get('cash', 0)
                total = balance_data.get('total', 0)
                stocks = balance_data.get('stocks', [])
                
                system_prompt += f"\n[현재 계좌 상태 요약 (고객에게 안내할 데이터)]\n"
                system_prompt += f"- 주문 가능 현금: {cash:,.0f}원\n"
                system_prompt += f"- 총 평가 금액: {total:,.0f}원\n"
                
                if stocks:
                    system_prompt += "- 보유 종목: "
                    for s in stocks:
                        system_prompt += f"{s['name']}({s['qty']}주, 평단가 {s['avg_price']:,.0f}원), "
                    system_prompt = system_prompt.rstrip(", ") + "\n"
                else:
                    system_prompt += "- 보유 종목: 없음 (현재 주식 없음)\n"
                
                system_prompt += "\n※ 사용자가 현재 보유 종목이나 수익, 계좌 상태 등을 물어보면 위 [현재 계좌 상태 요약] 데이터를 바탕으로 정확하게 알려주세요. 직접적인 열람 권한이 없다는 식의 거절은 절대 하지 마시고, 데이터를 자연스럽게 읽어주면 됩니다.\n"

        except Exception as e:
            logging.warning(f"Gemini 프롬프트용 데이터 조회 실패: {e}")
            pass
            
        system_prompt += (
            "\n[매우 중요한 지시사항! 반드시 지킬 것]\n"
            "1. 당신은 고객의 '명령'에 따라 수동으로 매매하는 봇이 *아닙니다*. 당신은 시장 지표, 뉴스 모멘텀, 기술적 차트를 분석하여 매일 자동으로 100% 자율적인 매매를 진행하는 'AI 퀀트 주식 트레이더'입니다.\n"
            "2. 절대로 고객에게 '어떤 종목을 살까요?', '얼마나 살까요?' 등 종목 추천이나 매매 지시를 되묻지 마세요.\n"
            "3. 고객이 매매에 관해 물어보면, '저는 시장 상황을 실시간으로 분석하여 최적의 타이밍에 알아서 분할 매수 및 자동 매도를 진행하는 스마트한 AI입니다. 저를 믿고 맡겨주시면 최선을 다해 수익을 내겠습니다.'라는 식으로 든든하고 똑똑하게 답하세요."
        )
            
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{system_prompt}\n\n사용자 메시지: {user_text}"
        )
        
        answer = response.text or ""
        await context.bot.send_message(chat_id=chat_id, text=answer)
        
    except Exception as e:
        logging.error(f"Gemini API 호출 중 에러 발생: {e}")
        error_msg = "앗, AI 서버와 통신하는 중에 문제가 발생했어요. 잠시 후 다시 시도해 주세요!"
        await context.bot.send_message(chat_id=chat_id, text=error_msg)

def run_telegram_bot():
    """텔레그램 봇 리스너 실행 (Polling 방식)"""
    
    # 스레드 환경에서 이벤트 루프 문제 방지용 세팅
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

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
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("help", help_command))

    # 일반 메시지 핸들러 등록 (텍스트일 경우)
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    logging.info("텔레그램 봇 리스너가 시작되었습니다. 메시지 수신 대기 중...")
    
    # 메시지 수신 무한 대기 (Polling) - 별도 스레드에서 실행되므로 시그널 핸들러 미사용 옵션 추가(Railway 등에서 오류 방지)
    app.run_polling(drop_pending_updates=True, stop_signals=None)

if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    run_telegram_bot()
