# 알림 시스템 설정 가이드

## 개요
향상된 크롤러는 데이터 수집 실패 시 다양한 채널로 알림을 발송합니다.

## 주요 기능

### 1. 다중 폴백 메커니즘
- **CloudScraper** → **Regular Requests** → **Custom Headers** → **Cached Data**
- 각 방법 실패 시 자동으로 다음 방법 시도
- 모든 방법 실패 시에만 Critical 알림 발송

### 2. 알림 채널
- Discord 웹훅
- Slack 웹훅  
- GitHub Issues (자동 생성)
- GitHub Actions 로그

### 3. 알림 레벨
- **INFO**: 복구 성공, 정상 작동
- **WARNING**: 캐시 데이터 사용, 일부 실패
- **ERROR**: 주요 기능 실패
- **CRITICAL**: 완전 실패, 즉시 조치 필요

## 설정 방법

### GitHub Secrets 설정

1. **GitHub 저장소 → Settings → Secrets and variables → Actions**

2. 다음 시크릿 추가:

#### Discord 알림 설정
```
Name: DISCORD_WEBHOOK_URL
Value: https://discord.com/api/webhooks/YOUR_WEBHOOK_URL
```

**Discord 웹훅 생성 방법:**
1. Discord 서버 설정 → 연동 → 웹훅
2. 새 웹훅 생성
3. 웹훅 URL 복사

#### Slack 알림 설정
```
Name: SLACK_WEBHOOK_URL
Value: https://hooks.slack.com/services/YOUR_WEBHOOK_URL
```

**Slack 웹훅 생성 방법:**
1. https://api.slack.com/apps 접속
2. Incoming Webhooks 활성화
3. 채널 선택 및 웹훅 URL 생성

#### GitHub Issue 자동 생성
```
Name: GITHUB_TOKEN
Value: (자동으로 제공됨, 추가 설정 불필요)
```

### 워크플로우 실행

#### 수동 실행 (테스트)
```bash
# GitHub Actions 탭에서
1. "Enhanced Daily Poker Data Crawl with Alerts" 선택
2. "Run workflow" 클릭
3. 필요시 debug_mode 활성화
```

#### 자동 실행
- 매일 한국시간 오전 3시 (UTC 18:00) 자동 실행
- 실패 시 설정된 모든 채널로 알림 발송

## 알림 예시

### Discord 알림 형식
```
🚨 PokerScout 크롤링 완전 실패
━━━━━━━━━━━━━━━━━━━━━━━━
모든 크롤링 방법이 실패했습니다. 즉시 점검이 필요합니다.

시간: 2025-08-11 03:00:00
URL: https://www.pokerscout.com
시도한 방법: CloudScraper, Requests, Custom Headers, Cache
액션 필요: 크롤링 로직 점검 필요
```

### GitHub Issue 형식
```markdown
## 크롤링 실패 알림

**실행 시간:** 2025-08-11T18:00:00Z
**워크플로우:** Enhanced Daily Poker Data Crawl
**실행 ID:** 123456789

### 확인 필요 사항
1. PokerScout.com 접속 가능 여부
2. 페이지 구조 변경 여부
3. CloudFlare 차단 여부
4. Firebase 연결 상태
```

## 모니터링

### 상태 확인
1. **GitHub Actions 탭**
   - 워크플로우 실행 기록 확인
   - 실패 시 로그 상세 분석

2. **Artifacts**
   - 실패 시 자동 저장되는 파일:
     - `crawl_failure_*.json`: 실패 상세 리포트
     - `backup_*.json`: 백업 데이터
     - `error_screenshot_*.png`: 에러 스크린샷

### 로그 분석
```bash
# 실패 리포트 확인
cat crawl_failure_*.json

# 백업 데이터 확인
cat backup_*.json | jq '.sites[:5]'
```

## 트러블슈팅

### 문제: 알림이 오지 않음
**해결:**
1. GitHub Secrets 설정 확인
2. 웹훅 URL 유효성 확인
3. 워크플로우 로그에서 알림 발송 부분 확인

### 문제: 크롤링은 성공하는데 업로드 실패
**해결:**
1. Firebase 서비스 계정 키 확인
2. Firebase 프로젝트 권한 확인
3. 네트워크 연결 상태 확인

### 문제: 모든 크롤링 방법 실패
**해결:**
1. PokerScout.com 직접 접속 테스트
2. CloudFlare 차단 여부 확인
3. 페이지 HTML 구조 변경 확인
4. User-Agent 업데이트 필요 여부 확인

## 유지보수

### 정기 점검 사항
- [ ] 월 1회: 알림 채널 테스트
- [ ] 주 1회: 크롤링 성공률 확인
- [ ] 일 1회: GitHub Actions 로그 확인

### 업데이트 시 주의사항
1. 크롤러 로직 변경 시 로컬 테스트 필수
2. 알림 임계값 조정 시 문서 업데이트
3. 새로운 폴백 방법 추가 시 순서 고려

## 연락처
문제 발생 시:
- GitHub Issues: https://github.com/garimto81/poker-online-analyze/issues
- 프로젝트 관리자에게 직접 연락