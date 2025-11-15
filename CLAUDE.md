# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

학생 출결 관리 시스템 - 텔레그램 봇과 웹 대시보드를 통한 자동화된 출결 관리 플랫폼

### Core Workflow

1. **텔레그램 메시지 수신**: 학생이 출결 정보를 텔레그램으로 전송
2. **AI 기반 정보 추출**: Claude AI가 메시지에서 '이름', '날짜', '출결 상황' 추출
3. **추출 실패 처리**: 정보 추출 실패 시 텔레그램으로 추가 정보 요청
4. **데이터베이스 저장**: 추출된 정보를 데이터베이스에 저장
5. **교사 승인 프로세스**: 웹 대시보드에서 교사가 출결 데이터 수락/거부/수정
6. **월별 현황 표시**: 달력 형태의 대시보드에 출결 현황 시각화
7. **서류 관리**: 서류 제출 여부 체크 및 미제출 학생에게 독려 메시지 자동 발송

## Architecture

### Backend
- **Language**: Python
- **Framework**: FastAPI or Django
- **API Design**: RESTful API
- **AI Integration**: Claude API for message parsing

### Frontend
- **Dashboard**: 월별 출결 현황 그리드 UI
  - 세로축: 학생 목록 (출석번호순)
  - 가로축: 날짜 (1~30/31일)
  - 각 셀: 출결 상태 표시 및 편집 가능
- **Features**: 출결 승인/거부/수정, 서류 제출 체크, 독려 메시지 발송

### Telegram Bot
- **Message Reception**: 학생의 출결 메시지 수신
- **Interactive Response**: AI 추출 실패 시 추가 정보 요청
- **Notification**: 서류 미제출 학생에게 독려 메시지 발송

## Key Components

### 1. Attendance Status System (9 Combinations)
출결 상태는 **출결 타입 (3종류) × 출결 사유 (3종류) = 9가지 조합**으로 구성:

**출결 타입:**
- 결석 (ABSENT)
- 지각 (LATE)
- 조퇴 (EARLY_LEAVE)

**출결 사유:**
- 질병 (ILLNESS): 병원, 아픈 경우
- 미인정 (UNAUTHORIZED): 개인 사정, 무단
- 출석인정 (AUTHORIZED): 현장체험학습, 체험학습, 가족여행 등

**9가지 조합 및 기호:**
- ♡ 질병결석
- # 질병지각
- ＠ 질병조퇴
- 🖤 미인정결석
- × 미인정지각
- ◎ 미인정조퇴
- △ 출석인정결석 (현장체험학습 등)
- ◁ 출석인정지각
- ▷ 출석인정조퇴

### 2. Message Parser (Claude AI Integration)
- **Input**: 텔레그램 메시지 원문
- **Output**: 구조화된 데이터 (이름, 날짜, 출결 타입, 출결 사유)
- **Error Handling**: 추출 실패 시 명확한 에러 메시지와 재요청 로직
- **특수 처리**: "현장체험학습", "체험학습" → 자동으로 "결석 + 출석인정"으로 분류

### 3. Database Schema
주요 테이블:
- **Students**: 학생 정보 (이름, 연락처 등)
- **Attendance**: 출결 기록 (학생 ID, 날짜, 출결 상황, 승인 상태)
- **Documents**: 서류 제출 여부 (학생 ID, 날짜, 제출 상태)
- **Requests**: 원본 텔레그램 메시지 및 추출 결과 로그

### 4. Approval Workflow
- **Pending**: 초기 저장 상태
- **Approved**: 교사 승인
- **Rejected**: 교사 거부
- **Modified**: 교사 수정 후 승인

### 5. Dashboard Grid
- **Layout**: 월별 출결 현황 그리드
  - **세로축 (Rows)**: 학생 목록 (출석번호순 정렬)
  - **가로축 (Columns)**: 날짜 (1일 ~ 30/31일)
  - **Cell**: 각 학생의 해당 날짜 출결 상태 표시
- **Features**:
  - 각 셀 클릭 시 출결 승인/거부/수정 가능
  - 서류 제출 여부 체크박스 또는 별도 컬럼
  - 서류 미제출 학생에게 독려 메시지 발송 버튼
  - 일괄 승인/거부 기능

## Development Commands

### Setup
```bash
# Backend 설정
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 TELEGRAM_BOT_TOKEN과 ANTHROPIC_API_KEY 설정

# Frontend 설정
cd frontend
npm install
```

### Telegram Bot
```bash
cd backend
source venv/bin/activate
python run_bot.py
```

### Backend API
```bash
cd backend
source venv/bin/activate

# FastAPI 실행 (개발 모드)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 샘플 데이터 생성
python seed_data.py
```

### Frontend
```bash
cd frontend

# 개발 서버 실행
npm run dev

# 빌드
npm run build
```

## Important Implementation Notes

### Claude AI Message Parsing
- **Prompt Engineering**: 메시지에서 이름, 날짜, 출결 상황을 정확히 추출하는 프롬프트 설계 중요
- **Structured Output**: Claude API의 structured output 기능 활용 권장
- **Validation**: 추출된 데이터의 유효성 검증 (날짜 형식, 이름 확인 등)
- **Fallback**: 추출 실패 시 사용자에게 명확한 형식 안내

### Telegram Bot Integration
- **python-telegram-bot** 라이브러리 사용 권장
- **Webhook vs Polling**: 프로덕션에서는 webhook 사용
- **Rate Limiting**: 텔레그램 API rate limit 고려
- **Error Handling**: 네트워크 오류, API 오류 처리

### Security Considerations
- 텔레그램 Bot Token은 환경 변수로 관리
- Claude API Key는 환경 변수로 관리
- 교사 인증/인가 시스템 구현 필요
- 학생 개인정보 보호 (HTTPS, 데이터 암호화)

### Database Design
- 출결 상태 변경 이력 추적 (audit log)
- 원본 메시지 보관 (추후 재처리 가능)
- 인덱스: 학생 ID, 날짜, 승인 상태

## Testing Strategy

### Unit Tests
- Claude AI 응답 파싱 로직
- 날짜 유효성 검증
- 출결 상태 변경 로직

### Integration Tests
- 텔레그램 봇 ↔ 백엔드 API
- 백엔드 API ↔ 데이터베이스
- Claude API 호출 및 응답 처리

### E2E Tests
- 학생 메시지 전송 → AI 추출 → DB 저장 → 교사 승인 → 대시보드 반영
- 서류 미제출 독려 메시지 발송 플로우
