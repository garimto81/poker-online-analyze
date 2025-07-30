# GitHub Pages 웹 호스팅 설정

GitHub에서 직접 웹사이트를 호스팅하는 방법입니다.

## 🚀 설정 방법

### 1. GitHub Pages 활성화

1. **GitHub 저장소**로 이동: https://github.com/garimto81/poker-online-analyze
2. **Settings** 탭 클릭
3. 왼쪽 메뉴에서 **Pages** 선택
4. Source 설정:
   - **Source**: GitHub Actions 선택
   - **Branch**: main (자동 선택됨)

### 2. 자동 배포 실행

1. **Actions** 탭으로 이동
2. "Deploy to GitHub Pages" 워크플로우 찾기
3. **"Run workflow"** 버튼 클릭하여 수동 실행

### 3. 배포 완료 확인

배포가 완료되면 다음 URL에서 접속 가능:
**https://garimto81.github.io/poker-online-analyze**

## 🌐 웹사이트 구조

### Frontend (GitHub Pages)
- **URL**: https://garimto81.github.io/poker-online-analyze
- **호스팅**: GitHub Pages (무료)
- **업데이트**: main 브랜치 푸시시 자동 배포

### Backend API (Vercel 서버리스)
- **URL**: https://poker-analyzer-api.vercel.app
- **호스팅**: Vercel Functions (무료)
- **기능**: Firebase 데이터 조회, 크롤링 API

## 📊 데이터 흐름

1. **데이터 수집**: GitHub Actions → Firebase
2. **API 서버**: Vercel Functions → Firebase 조회
3. **웹사이트**: GitHub Pages → API 호출 → 차트 표시

## ✅ 장점

- **완전 무료**: GitHub Pages + Vercel 무료 플랜
- **자동 배포**: 코드 푸시시 자동 업데이트
- **안정성**: GitHub 인프라 사용
- **빠른 속도**: CDN 자동 적용

## 🔧 문제 해결

### 배포 실패시
1. Actions 탭에서 로그 확인
2. Node.js 빌드 오류 확인
3. 의존성 설치 문제 확인

### API 연결 실패시
1. CORS 설정 확인
2. API URL 환경 변수 확인
3. Firebase 설정 확인

### 데이터 표시 안됨
1. GitHub Actions "Daily Poker Data Crawl" 실행 확인
2. Firebase Console에서 데이터 확인
3. 브라우저 개발자 도구에서 네트워크 오류 확인

## 📈 모니터링

- **GitHub Actions**: 자동 배포 및 크롤링 상태
- **Vercel Dashboard**: API 서버 상태 및 사용량
- **Firebase Console**: 데이터베이스 상태 및 사용량

모든 설정이 완료되면 완전히 무료로 운영되는 웹사이트가 됩니다! 🎉