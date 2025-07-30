# 웹 배포 가이드

온라인에서 포커 분석기를 볼 수 있도록 배포하는 단계별 가이드입니다.

## 📋 필요한 준비사항

### 1. 계정 생성
- **Render** (백엔드): https://render.com
- **Vercel** (프론트엔드): https://vercel.com
- 둘 다 무료 플랜 있음

### 2. GitHub Secrets 설정
Repository Settings → Secrets and variables → Actions에서 다음 추가:

#### 백엔드 (Render) 관련:
- `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase 서비스 계정 키 JSON 전체
- `RENDER_BUILD_HOOK_URL`: Render 빌드 훅 URL

#### 프론트엔드 (Vercel) 관련:
- `VERCEL_TOKEN`: Vercel API 토큰

## 🚀 백엔드 배포 (Render)

### 1. Render 서비스 생성
1. Render.com 로그인
2. "New" → "Web Service" 선택
3. GitHub 저장소 연결: `garimto81/poker-online-analyze`
4. 설정:
   - **Name**: `poker-analyzer-backend`
   - **Region**: Oregon (US West)
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 2. 환경 변수 설정
Render 대시보드에서 Environment 탭:
- `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase 키 JSON 전체 내용

### 3. 빌드 훅 URL 얻기
1. Render 서비스 Settings 탭
2. "Build & Deploy" 섹션에서 "Build Hook" URL 복사
3. GitHub Secrets에 `RENDER_BUILD_HOOK_URL`로 추가

## 🌐 프론트엔드 배포 (Vercel)

### 1. Vercel 프로젝트 생성
1. Vercel.com 로그인
2. "New Project" 클릭
3. GitHub 저장소 import: `garimto81/poker-online-analyze`
4. 설정:
   - **Project Name**: `poker-analyzer-frontend`
   - **Framework Preset**: Create React App
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### 2. 환경 변수 설정
Vercel 프로젝트 Settings → Environment Variables:
- `REACT_APP_API_URL`: `https://your-backend-name.onrender.com`

### 3. Vercel 토큰 얻기
1. Vercel Settings → Tokens
2. "Create Token" 클릭하여 토큰 생성
3. GitHub Secrets에 `VERCEL_TOKEN`으로 추가

## 🔄 자동 배포 설정

### GitHub Actions 워크플로우
- **Backend**: `backend/` 폴더 변경 시 자동 Render 배포
- **Frontend**: `frontend/` 폴더 변경 시 자동 Vercel 배포
- **Daily Crawl**: 매일 자동 데이터 수집

## 🌍 배포된 사이트 URL

배포 완료 후:
- **Frontend**: `https://poker-analyzer-frontend.vercel.app`
- **Backend API**: `https://poker-analyzer-backend.onrender.com`
- **API Docs**: `https://poker-analyzer-backend.onrender.com/docs`

## 📊 데이터 수집 확인

1. **GitHub Actions** 탭에서 "Daily Poker Data Crawl" 실행 상태 확인
2. **Firebase Console**에서 Firestore 데이터 확인
3. **배포된 사이트**에서 차트와 테이블 확인

## 🔧 문제 해결

### 백엔드 배포 실패
- Render 로그 확인
- Firebase 키 환경 변수 확인
- Python 의존성 확인

### 프론트엔드 배포 실패
- Vercel 빌드 로그 확인
- API URL 환경 변수 확인
- CORS 설정 확인

### API 연결 실패
- 백엔드 URL이 올바른지 확인
- CORS 설정에 프론트엔드 도메인 포함 여부 확인

## 💰 비용

- **Render**: 무료 플랜 (월 750시간, 512MB RAM)
- **Vercel**: 무료 플랜 (월 100GB 대역폭)
- **Firebase**: 무료 플랜 (일 50,000 읽기/20,000 쓰기)
- **GitHub Actions**: 공개 저장소는 무제한 무료

총 **무료**로 운영 가능! 🎉