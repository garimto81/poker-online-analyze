# GitHub Actions 수동 실행 방법

## 웹 브라우저에서 실행:

1. https://github.com/garimto81/poker-online-analyze 접속
2. "Actions" 탭 클릭
3. 왼쪽 사이드바에서 "Daily Poker Data Crawl" 선택
4. 오른쪽의 "Run workflow" 버튼 클릭
5. "Run workflow" 녹색 버튼 클릭

## 실행 상태 확인:

1. Actions 탭에서 실행 중인 워크플로우 확인
2. 클릭하여 상세 로그 확인
3. 각 단계별 성공/실패 여부 확인

## 주의사항:

⚠️ Firebase 서비스 계정 키를 GitHub Secrets에 먼저 추가해야 합니다!

Settings → Secrets and variables → Actions → New repository secret
- Name: FIREBASE_SERVICE_ACCOUNT_KEY
- Value: Firebase JSON 키 전체 내용