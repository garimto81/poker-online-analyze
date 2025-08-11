# 크롤러 업데이트 가이드 (2025.08)

## 문제 상황
- **날짜**: 2025년 8월 9일부터 데이터 수집 중단
- **원인**: PokerScout.com이 자동 크롤링을 차단 (403 Forbidden 에러)
- **영향**: GitHub Actions의 일일 크롤링 작업 실패

## 해결 방안 구현

### 1. 단기 조치: Selenium + Undetected ChromeDriver
**새로운 크롤러 파일**: `backend/selenium_crawler_advanced.py`

#### 주요 기능:
- ✅ Undetected ChromeDriver로 봇 탐지 회피
- ✅ 자동 재시도 로직 (최대 3회)
- ✅ 에러 발생 시 스크린샷 저장
- ✅ BeautifulSoup 폴백 지원
- ✅ GitHub Actions 환경 자동 감지

### 2. 중기 조치: 프록시 로테이션 시스템
#### ProxyManager 클래스 구현:
- 무료 프록시 자동 수집 (ProxyScrape API)
- 실패한 프록시 자동 제거
- 순환 방식 프록시 사용

### 3. GitHub Actions 워크플로우
**새로운 워크플로우**: `.github/workflows/daily-crawl-selenium.yml`

#### 개선사항:
- Chrome/Chromium 의존성 자동 설치
- Selenium 크롤러 우선 실행
- 실패 시 기존 크롤러로 자동 폴백
- 에러 스크린샷 아티팩트 저장

## 설치 방법

### 로컬 환경:
```bash
# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
cd backend
python test_selenium_crawler.py

# 브라우저 표시 모드 테스트 (디버깅용)
python test_selenium_crawler.py --visible
```

### GitHub Actions 배포:
1. 저장소에 푸시
2. Actions 탭에서 "Daily Poker Data Crawl (Selenium Enhanced)" 워크플로우 확인
3. 수동 실행으로 테스트 (workflow_dispatch)

## 테스트 스크립트
`backend/test_selenium_crawler.py` 파일로 다음 테스트 수행:
- 기본 크롤링 테스트
- 프록시 사용 테스트
- 기존 크롤러와 비교
- 결과를 JSON 파일로 저장

## 모니터링 및 디버깅

### 로그 확인:
```bash
# GitHub Actions 로그
GitHub 저장소 > Actions 탭 > 워크플로우 실행 기록

# 로컬 테스트 로그
backend/test_results_*.json
```

### 에러 스크린샷:
- GitHub Actions 실패 시 자동으로 스크린샷 저장
- Actions 아티팩트에서 다운로드 가능

## 향후 개선 사항

### 추가 가능한 개선점:
1. **캐싱 시스템**: 프록시 리스트 캐싱
2. **알림 시스템**: 크롤링 실패 시 이메일/Slack 알림
3. **대체 데이터 소스**: 다른 포커 통계 사이트 추가
4. **API 전환**: PokerScout API 제공 시 전환

### 장기 계획:
- PokerScout와 파트너십 체결 검토
- 공식 API 액세스 요청
- 여러 데이터 소스 통합

## 문제 해결

### 크롤링이 여전히 실패하는 경우:
1. PokerScout 사이트 구조 변경 확인
2. 프록시 리스트 업데이트
3. User-Agent 문자열 변경
4. 요청 간격 증가 (현재 0.5-2초)

### Chrome 관련 오류:
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install chromium-browser chromium-chromedriver

# Windows (로컬 테스트)
# Chrome이 자동으로 다운로드됨
```

## 연락처
문제 발생 시 GitHub Issues에 보고해주세요.