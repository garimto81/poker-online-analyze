# 테스트 실행 가이드

## 사전 준비사항

### 1. Firebase 설정
1. [Firebase Console](https://console.firebase.google.com) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. 프로젝트 설정 > 서비스 계정 > "새 비공개 키 생성" 클릭
4. 다운로드한 JSON 파일을 `backend/key/firebase-service-account-key.json`으로 저장

### 2. Python 환경 설정
```bash
cd backend
pip install -r requirements.txt
```

### 3. Node.js 환경 설정
```bash
cd frontend
npm install
```

## 테스트 단계

### 1단계: Firebase 연결 테스트
```bash
cd backend
python test_firebase_connection.py
```

예상 결과:
- ✅ Firebase 연결 성공!
- ✅ Firestore 업로드 성공!
- ✅ 사이트 문서 확인
- ✅ 트래픽 로그 확인

### 2단계: 백엔드 서버 실행
```bash
cd backend
uvicorn main:app --reload
```

서버가 실행되면:
- 브라우저에서 http://localhost:8000 접속
- API 문서: http://localhost:8000/docs

### 3단계: API 테스트
새 터미널에서:
```bash
cd backend
python test_api.py
```

예상 결과:
- ✅ API 서버 연결 성공!
- ✅ 사이트 목록 조회 성공!
- ✅ 현재 순위 조회 성공!
- 크롤링 테스트 (선택사항)

### 4단계: 프론트엔드 실행
새 터미널에서:
```bash
cd frontend
npm start
```

브라우저가 자동으로 열리고 http://localhost:3000 에서 앱이 실행됩니다.

### 5단계: 전체 시스템 테스트
1. 프론트엔드에서 "🔄 Refresh Data" 클릭 → 현재 데이터 표시
2. "🕷️ Trigger New Crawl" 클릭 → 새로운 데이터 크롤링 및 저장
3. 테이블에서 순위, 사이트명, 플레이어 수 등 확인

## 문제 해결

### Firebase 연결 실패
- 서비스 계정 키 파일 경로 확인: `backend/key/firebase-service-account-key.json`
- 파일 권한 확인
- Firebase 프로젝트가 활성화되어 있는지 확인

### API 서버 연결 실패
- 8000 포트가 사용 중인지 확인
- 방화벽 설정 확인
- uvicorn이 정상적으로 실행되었는지 확인

### 프론트엔드 오류
- npm install이 완료되었는지 확인
- 3000 포트가 사용 중인지 확인
- 백엔드 서버가 실행 중인지 확인

## 성공 지표

✅ Firebase에 데이터가 저장됨
✅ API가 Firebase에서 데이터를 읽어옴
✅ 프론트엔드가 실시간 데이터를 표시함
✅ 크롤링 트리거가 작동함
✅ GitHub Actions가 자동으로 데이터를 수집함 (배포 후)