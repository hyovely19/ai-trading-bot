#!/bin/bash
export PYTHONIOENCODING=utf-8

echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo "Starting AI Stock Trading Bot (main.py)..."
python main.py
