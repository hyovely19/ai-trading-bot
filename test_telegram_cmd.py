import asyncio
import logging
import sys
import os

sys.path.append('.')
from telegram_bot import handle_message, balance_command

class MockChat:
    id = 12345

class MockMessage:
    def __init__(self, text):
        self.text = text

class MockUpdate:
    def __init__(self, text):
        self.message = MockMessage(text)
        self.effective_chat = MockChat()

class MockBot:
    async def send_chat_action(self, chat_id, action):
        print(f"[ACTION] {action}")
    async def send_message(self, chat_id, text, parse_mode=None):
        print(f"[BOT MSG] {text}")

class MockContext:
    def __init__(self):
        self.bot = MockBot()

async def test():
    print('--- Testing /balance ---')
    await balance_command(MockUpdate('/balance'), MockContext())
    print('\n--- Testing 잔고 text ---')
    await handle_message(MockUpdate('잔고 알려줘'), MockContext())

asyncio.run(test())
