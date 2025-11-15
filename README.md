# 📋 학생 출결 관리 시스템

AI 기반 텔레그램 봇과 웹 대시보드를 통한 자동화된 출결 관리 플랫폼

## 🎯 주요 기능

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

### 3. 출결 상태 시스템
9가지 출결 조합 (타입 × 사유):
- **타입**: 결석, 지각, 조퇴
- **사유**: 질병, 미인정, 출석인정
- **기호 표시**: ♡(질병결석), #(질병지각), △(출석인정결석) 등

## 🏗️ 기술 스택

### Backend
- **Python 3.10+**
- **FastAPI**: 고성능 비동기 웹 프레임워크
- **SQLAlchemy**: ORM
- **SQLite**: 데이터베이스
- **python-telegram-bot**: 텔레그램 봇 API
- **Anthropic Claude API**: AI 메시지 파싱

### Frontend
- **React 18**: UI 라이브러리
- **Vite**: 빌드 도구
- **Day.js**: 날짜 처리
- **Axios**: HTTP 클라이언트

## 📦 설치 및 실행

### 사전 요구사항
- Python 3.10 이상
- Node.js 16 이상
- Telegram Bot Token
- Anthropic API Key

### 1. 저장소 클론
\`\`\`bash
git clone https://github.com/yourusername/attendance-system.git
cd attendance-system
\`\`\`

### 2. 백엔드 설정
\`\`\`bash
cd backend

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate

# 패키지 설치
pip install -r requirements.txt

# 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 다음 항목 설정:
# - TELEGRAM_BOT_TOKEN=your_telegram_bot_token
# - ANTHROPIC_API_KEY=your_anthropic_api_key

# 데이터베이스 초기화
python seed_data.py  # 샘플 데이터 생성 (선택사항)

# 백엔드 서버 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
\`\`\`

### 3. 프론트엔드 설정
\`\`\`bash
cd frontend

# 패키지 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드 (배포용)
npm run build
\`\`\`

### 4. 텔레그램 봇 실행
\`\`\`bash
cd backend
source venv/bin/activate
python run_bot.py
\`\`\`

## 🚀 배포

### 프론트엔드 배포 (Vercel/Netlify)
1. GitHub에 코드 푸시
2. Vercel 또는 Netlify에서 프로젝트 연결
3. 빌드 설정:
   - **Base directory**: \`frontend\`
   - **Build command**: \`npm run build\`
   - **Publish directory**: \`frontend/dist\`

### 백엔드 배포 (Railway/Render)
1. \`backend\` 폴더를 별도 저장소로 분리 (권장)
2. 환경 변수 설정 (TELEGRAM_BOT_TOKEN, ANTHROPIC_API_KEY)
3. 시작 명령어: \`uvicorn app.main:app --host 0.0.0.0 --port \$PORT\`

## 📱 사용 방법

### 학부모용 (텔레그램)
1. 봇과 대화 시작: \`/start\`
2. 자연어로 출결 신고:
   - "주선이 오늘 아파요" → 질병 결석
   - "철수 늦습니다" → 지각
   - "영희 현장체험학습" → 출석인정 결석
3. 서류 제출: 사진 전송

### 교사용 (웹 대시보드)
1. 브라우저에서 \`http://localhost:3000\` 접속
2. 년도/월 선택하여 출결 현황 확인
3. 셀 클릭하여 출결 기록 승인/거부/수정
4. 학생 관리 버튼으로 학생 정보 관리
5. 출결표 인쇄 버튼으로 인쇄/PDF 저장

## 📊 데이터베이스 스키마

### Students (학생)
- id, name, student_number, telegram_id, phone

### AttendanceRecords (출결 기록)
- id, student_id, date, attendance_type, attendance_reason
- approval_status, original_message, document_submitted

### StudentParents (학부모)
- id, student_id, telegram_id, parent_name, relation
- is_active, auto_registered

### DocumentSubmissions (서류 제출)
- id, student_id, attendance_record_id, file_path
- is_submitted, submitted_at

## 🔐 보안

- \`.env\` 파일은 절대 GitHub에 올리지 마세요
- API 키는 환경 변수로 관리
- 프로덕션 환경에서는 HTTPS 사용 필수
- 데이터베이스는 정기적으로 백업

## 📝 라이선스

MIT License

## 🤝 기여

이슈와 Pull Request를 환영합니다!

## 📧 문의

프로젝트에 대한 문의사항은 Issues 탭을 이용해주세요.

---

🤖 Generated with Claude Code
