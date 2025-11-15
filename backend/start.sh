#!/bin/bash
set -e

echo "Starting backend services..." >&2

# 백엔드 API 서버 시작
echo "Starting API server on port $PORT..." >&2
uvicorn app.main:app --host 0.0.0.0 --port $PORT 2>&1 &
API_PID=$!
echo "API server started with PID: $API_PID" >&2

# 잠시 대기 후 API 서버 확인
sleep 2
if ! kill -0 $API_PID 2>/dev/null; then
    echo "ERROR: API server failed to start!" >&2
    exit 1
fi

# 텔레그램 봇 시작
echo "Starting Telegram bot..." >&2
python run_bot.py 2>&1 &
BOT_PID=$!
echo "Telegram bot started with PID: $BOT_PID" >&2

echo "All services started successfully!" >&2

# 모든 백그라운드 프로세스 대기
wait
