import os
import sys
from datetime import datetime, timedelta

# backend 디렉토리를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.claude_parser import ClaudeMessageParser

# ClaudeMessageParser의 프롬프트 생성 로직만 추출
today = datetime.now().date()
tomorrow = today + timedelta(days=1)
today_str = today.strftime("%Y-%m-%d")
tomorrow_str = tomorrow.strftime("%Y-%m-%d")
three_days_later = (tomorrow + timedelta(days=2)).strftime("%Y-%m-%d")

# 요일 정보 (한글)
weekday_names = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]
today_weekday = weekday_names[today.weekday()]

# 다음주 금요일 계산 (금요일 = 4)
days_until_this_friday = (4 - today.weekday()) % 7
if days_until_this_friday == 0:  # 오늘이 금요일
    days_until_this_friday = 7
days_until_next_friday = days_until_this_friday + 7
next_friday = (today + timedelta(days=days_until_next_friday)).strftime("%Y-%m-%d")

print(f"📅 오늘: {today_str} ({today_weekday})")
print(f"📅 내일: {tomorrow_str}")
print(f"📅 다음주 금요일: {next_friday}")
print(f"📅 계산: 이번주금요일까지 {days_until_this_friday}일 + 7일 = {days_until_next_friday}일 후")
print()

# 프롬프트 일부 출력
message = "다음주 금요일에도 못가요"
print(f"테스트 메시지: {message}")
print()
print("="*70)
print("프롬프트에 들어가는 날짜 정보:")
print("="*70)
print(f"- 오늘 날짜: {today_str} ({today_weekday})")
print(f'- "다음주 금요일" → {next_friday} (오늘이 {today_weekday}이므로 다음주 금요일은 {next_friday})')
