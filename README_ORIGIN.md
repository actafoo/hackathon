# 학생 출결 관리 시스템

AI 기반 텔레그램 봇과 웹 대시보드를 통한 자동화된 출결 관리 플랫폼

## 배포 URL

- **프론트엔드 (Vercel)**: https://frontend-4w30j0oi5-actafoos-projects.vercel.app
- **백엔드 API (Fly.io)**: https://backend-aged-summit-5682.fly.dev
- **GitHub**: https://github.com/actafoo/hackathon

## 주요 기능

### 1. 텔레그램 봇 기반 출결 신고
- **AI 자동 파싱**: Claude AI가 자연어 메시지에서 출결 정보 자동 추출
- **간편한 사용**: "주선이 오늘 아파요" 같은 자연스러운 메시지로 출결 신고
- **서류 제출**: 사진 전송으로 간편한 서류 제출
- **자동 학부모 등록**: 첫 메시지 발송 시 자동으로 학부모-학생 연결

### 2. 웹 대시보드
- **월별 출결 현황**: 달력 형태의 직관적인 출결 그리드
- **실시간 통계**: 전체 학생, 출결 기록, 승인 대기, 서류 미제출 현황
- **승인 프로세스**: 출결 기록 승인/거부/수정 기능
- **학생 관리**: 학생 정보 및 학부모 연락처 관리
- **인쇄 기능**: 출결표 인쇄 및 PDF 저장

### 3. 출결 상태 시스템 (9가지)
타입(결석/지각/조퇴) × 사유(질병/미인정/출석인정):

| 기호 | 의미 |
|------|------|
| ♡ | 질병결석 |
| # | 질병지각 |
| ＠ | 질병조퇴 |
| 🖤 | 미인정결석 |
| × | 미인정지각 |
| ◎ | 미인정조퇴 |
| △ | 출석인정결석 (현장체험학습 등) |
| ◁ | 출석인정지각 |
| ▷ | 출석인정조퇴 |

## 기술 스택

| 구분 | 기술 |
|------|------|
| Backend | Python 3.10, FastAPI, SQLAlchemy, PostgreSQL |
| Frontend | React 18, Vite, Axios, Day.js |
| AI | Anthropic Claude API (Haiku) |
| Bot | python-telegram-bot |
| 배포 | Fly.io (백엔드), Vercel (프론트엔드) |

## 로컬 개발 환경 설정

### 사전 요구사항
- Python 3.10 이상
- Node.js 16 이상
- Telegram Bot Token
- Anthropic API Key

### 백엔드
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# .env 파일에 TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY 설정

# API 서버 실행 (포트 8000)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 텔레그램 봇 실행 (별도 터미널)
python run_bot.py

# 샘플 데이터 생성 (선택)
python seed_data.py
```

### 프론트엔드
```bash
cd frontend
npm install
npm run dev
```

## 배포

### 백엔드 (Fly.io)
```bash
cd backend
flyctl auth login
flyctl deploy
```

환경변수는 `flyctl secrets set KEY=VALUE`로 설정.

### 프론트엔드 (Vercel)
```bash
cd frontend
npx vercel --prod
```

`frontend/.env.production`의 `VITE_API_URL`이 백엔드 URL을 가리키는지 확인.

## 사용 방법

### 학부모 (텔레그램)
1. 봇과 대화 시작: `/start`
2. 자연어로 출결 신고:
   - "주선이 오늘 아파요" → 질병 결석
   - "철수 늦습니다" → 지각
   - "영희 현장체험학습" → 출석인정 결석
3. 서류 제출: 사진 전송

### 교사 (웹 대시보드)
1. 브라우저에서 프론트엔드 URL 접속
2. 년도/월 선택하여 출결 현황 확인
3. 셀 클릭하여 출결 기록 승인/거부/수정
4. 학생 관리 버튼으로 학생 정보 관리

## 보안

- `.env` 파일은 절대 GitHub에 올리지 마세요
- API 키는 Fly.io secrets으로 관리
- 데이터베이스는 Fly.io PostgreSQL 사용 (자동 백업)
