# 🚀 배포 가이드

## 준비 완료!

모든 배포 설정 파일이 준비되었습니다. 이제 Railway와 Vercel에 배포하시면 됩니다.

---

## 1️⃣ Railway로 백엔드 배포 (추천)

### 방법 1: Railway 웹사이트에서 배포 (가장 쉬움)

1. **Railway 가입**
   - https://railway.app 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "New Project" 클릭
   - "Deploy from GitHub repo" 선택
   - `actafoo/hackathon` 저장소 선택
   - **Root Directory**: `backend` 선택

3. **환경 변수 설정**
   - 프로젝트 대시보드에서 "Variables" 탭 클릭
   - 다음 환경 변수 추가:
     ```
     TELEGRAM_BOT_TOKEN=여기에_텔레그램_봇_토큰
     ANTHROPIC_API_KEY=여기에_클로드_API_키
     DATABASE_URL=sqlite:///./attendance.db
     ```

4. **배포 완료!**
   - Railway가 자동으로 빌드 및 배포 시작
   - 배포 완료 후 URL 복사 (예: `https://your-app.railway.app`)

### 방법 2: Railway CLI 사용

```bash
# Railway CLI 설치 (Mac)
brew install railway

# 로그인
railway login

# 백엔드 폴더로 이동
cd backend

# 프로젝트 초기화 및 배포
railway init
railway up

# 환경 변수 설정
railway variables set TELEGRAM_BOT_TOKEN="여기에_토큰"
railway variables set ANTHROPIC_API_KEY="여기에_API_키"
```

---

## 2️⃣ Vercel로 프론트엔드 배포

### 방법 1: Vercel 웹사이트에서 배포 (추천)

1. **Vercel 가입**
   - https://vercel.com 접속
   - GitHub 계정으로 로그인

2. **새 프로젝트 생성**
   - "Add New Project" 클릭
   - `actafoo/hackathon` 저장소 선택

3. **프로젝트 설정**
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
   - **Install Command**: `npm install`

4. **환경 변수 설정**
   - "Environment Variables" 섹션에서:
     ```
     VITE_API_URL=https://your-railway-app.railway.app/api
     ```
   - ⚠️ Railway에서 받은 백엔드 URL 사용!

5. **배포**
   - "Deploy" 클릭
   - 몇 분 후 배포 완료! (예: `https://your-app.vercel.app`)

### 방법 2: Vercel CLI 사용

```bash
# Vercel CLI 설치
npm i -g vercel

# 프론트엔드 폴더로 이동
cd frontend

# 배포
vercel

# 프로덕션 배포
vercel --prod

# 환경 변수 설정
vercel env add VITE_API_URL production
# 입력: https://your-railway-app.railway.app/api
```

---

## 3️⃣ 배포 확인

### 백엔드 확인
1. Railway URL 접속: `https://your-app.railway.app/docs`
2. FastAPI Swagger 문서가 보이면 성공!

### 프론트엔드 확인
1. Vercel URL 접속: `https://your-app.vercel.app`
2. 출결 관리 대시보드가 보이면 성공!

### 텔레그램 봇 확인
1. 텔레그램 봇에 메시지 전송
2. 응답이 오면 성공!

---

## 🔧 문제 해결

### Railway 배포 실패
- **로그 확인**: Railway 대시보드에서 "Deployments" → 실패한 배포 클릭 → 로그 확인
- **환경 변수 확인**: 모든 필수 환경 변수가 설정되었는지 확인
- **Python 버전**: `runtime.txt`에 Python 3.10 이상이 지정되어 있는지 확인

### Vercel 배포 실패
- **로그 확인**: Vercel 대시보드에서 빌드 로그 확인
- **환경 변수**: `VITE_API_URL`이 올바르게 설정되었는지 확인
- **API URL**: Railway 백엔드 URL이 `/api`로 끝나는지 확인

### 텔레그램 봇 작동 안 함
- **Railway 로그 확인**: "View Logs" → `run_bot.py` 관련 로그 확인
- **환경 변수**: `TELEGRAM_BOT_TOKEN`과 `ANTHROPIC_API_KEY` 확인
- **봇 재시작**: Railway에서 "Restart" 클릭

---

## 💡 팁

1. **무료 플랜 한도**
   - Railway: $5 크레딧/월 (충분함)
   - Vercel: 무료 (충분함)

2. **커스텀 도메인 연결**
   - Railway: Settings → Domains
   - Vercel: Settings → Domains

3. **자동 배포 설정**
   - GitHub에 push하면 자동으로 재배포됩니다!

4. **로그 모니터링**
   - Railway: Real-time logs
   - Vercel: Build logs

---

## 📝 배포 완료 체크리스트

- [ ] Railway 백엔드 배포
- [ ] Railway 환경 변수 설정
- [ ] Vercel 프론트엔드 배포
- [ ] Vercel 환경 변수 설정 (Railway URL 포함)
- [ ] 백엔드 API 접속 확인
- [ ] 프론트엔드 대시보드 접속 확인
- [ ] 텔레그램 봇 작동 확인
- [ ] 출결 기록 생성 테스트
- [ ] 웹 대시보드에서 데이터 확인

---

🎉 배포 완료되면 언제 어디서나 접속 가능합니다!
