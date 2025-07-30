# 클라우드 자동 크롤링 설정 가이드

로컬 PC가 꺼져 있어도 매일 자동으로 데이터를 수집하는 방법입니다.

## 옵션 1: GitHub Actions (무료, 추천) ✅

GitHub Actions를 사용하면 GitHub 서버에서 매일 자동으로 크롤링이 실행됩니다.

### 설정 방법

1. **Firebase 서비스 계정 키를 GitHub Secrets에 추가**

   a. Firebase 콘솔에서 서비스 계정 키 JSON 파일 내용 복사
   
   b. GitHub 저장소로 이동
   
   c. Settings → Secrets and variables → Actions
   
   d. "New repository secret" 클릭
   
   e. 설정:
      - Name: `FIREBASE_SERVICE_ACCOUNT_KEY`
      - Value: Firebase 서비스 계정 키 JSON 전체 내용 붙여넣기
   
   f. "Add secret" 클릭

2. **GitHub Actions 워크플로우 활성화**

   이미 `.github/workflows/daily-crawl.yml` 파일이 포함되어 있으므로,
   GitHub에 푸시하면 자동으로 활성화됩니다.

3. **동작 확인**

   - 매일 한국시간 오전 3시에 자동 실행
   - Actions 탭에서 실행 상태 확인 가능
   - "Run workflow" 버튼으로 수동 실행 가능

### 장점
- ✅ 무료 (공개 저장소)
- ✅ PC가 꺼져 있어도 실행
- ✅ 실행 로그 GitHub에서 확인 가능
- ✅ 별도 서버 불필요

### 단점
- ⚠️ 비공개 저장소는 월 2,000분 무료 제한
- ⚠️ 최대 실행 시간 6시간 제한

## 옵션 2: 클라우드 서버 (유료)

### A. AWS EC2 t2.micro (1년 무료)
```bash
# EC2 인스턴스에서 cron 설정
0 3 * * * cd /home/ubuntu/poker-online-analyze && ./auto_crawl.sh
```

### B. Google Cloud Functions (월 200만 호출 무료)
- HTTP 트리거로 크롤링 함수 생성
- Cloud Scheduler로 매일 호출

### C. Heroku Scheduler (무료 플랜 종료)
- 대안: Railway, Render 등의 스케줄러 사용

## 옵션 3: 로컬 대안

### A. Wake-on-LAN 설정
- PC를 원격으로 켜고 작업 실행 후 종료

### B. 라즈베리파이
- 24시간 저전력 운영
- 로컬 네트워크에서 크롤링 실행

## 권장 사항

**GitHub Actions**를 사용하는 것을 권장합니다:
1. 무료이고 설정이 간단함
2. PC 전원 상태와 무관하게 안정적 실행
3. 실행 로그를 GitHub에서 바로 확인 가능

## 보안 주의사항

- Firebase 서비스 계정 키는 반드시 GitHub Secrets에만 저장
- 절대 코드에 직접 포함하지 말 것
- API 엔드포인트는 인증 없이 크롤링 가능하므로 주의

## 문제 해결

### GitHub Actions가 실패하는 경우
1. Actions 탭에서 로그 확인
2. Firebase 키가 올바르게 설정되었는지 확인
3. Python 패키지 설치 오류 확인

### 크롤링이 차단되는 경우
1. User-Agent 헤더 추가
2. 요청 간격 늘리기
3. 프록시 사용 고려