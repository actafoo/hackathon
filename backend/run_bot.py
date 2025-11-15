#!/usr/bin/env python3
"""텔레그램 봇 실행 스크립트"""

import sys
import os

# 현재 디렉토리를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.telegram_bot import AttendanceTelegramBot
from app.database import init_db


def main():
    """봇 실행"""
    print("Initializing database...")
    init_db()

    print("Starting Telegram bot...")
    bot = AttendanceTelegramBot()
    bot.run()


if __name__ == "__main__":
    main()
