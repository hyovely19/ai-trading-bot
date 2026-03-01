#!/bin/bash
echo "Installing google-genai..."
pip install google-genai

echo "Starting Telegram Bot Listener in background..."
python telegram_bot.py &

echo "Starting AI Quant Manager..."
python src/utils/ai_quant_manager.py
