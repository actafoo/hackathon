#!/bin/bash

# 백엔드 API 서버 시작
uvicorn app.main:app --host 0.0.0.0 --port $PORT &

# 텔레그램 봇 시작
python run_bot.py &

# 모든 백그라운드 프로세스 대기
wait
