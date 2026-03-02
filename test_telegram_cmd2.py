import asyncio

async def run_test():
    from telegram_bot import handle_message, balance_command

    class MockBot:
        async def send_chat_action(self, chat_id, action):
            print(f"[ACTION] chat={chat_id} action={action}")
        async def send_message(self, chat_id, text, parse_mode=None):
            print(f"[MSG] To {chat_id}: {repr(text)}")

    class MockContext:
        bot = MockBot()

    class MockUser:
        id = 1234
        
    class MockChat:
        id = 5678
        type = "private"

    class MockMessage:
        def __init__(self, text):
            self.text = text
            self.message_id = 1
            self.date = None
            self.chat = MockChat()
            self.from_user = MockUser()

    class MockUpdate:
        def __init__(self, text):
            self.message = MockMessage(text)
            self.effective_chat = MockChat()

    print("--- Testing /balance ---")
    await balance_command(MockUpdate("/balance"), MockContext())
    
    print("\n--- Testing 자연어 잔고 ---")
    await handle_message(MockUpdate("잔고 확인 좀"), MockContext())

asyncio.run(run_test())
