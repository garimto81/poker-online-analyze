# Poker Online Analyze

온라인 포커 사이트의 데이터를 수집하고 분석하여 트렌드 및 비교 분석 정보를 제공하는 웹 애플리케이션입니다.

## 프로젝트 개요

이 프로젝트는 PokerScout.com에서 온라인 포커 사이트의 데이터를 매일 자동으로 수집하고, 이를 시각화하여 사용자에게 트렌드 및 비교 분석 정보를 제공하는 것을 목표로 합니다.

## 최신 업데이트 (2025-01-30)

- 포트 변경: Backend (8001→4001), Frontend (3001→4000)
- 차트 개선: 각 지표별로 독립적인 상위 10개 사이트 표시
- Windows Task Scheduler를 통한 자동 크롤링 지원

## 주요 기능

### 데이터 수집
- PokerScout.com에서 47개 온라인 포커 사이트의 실시간 데이터 크롤링
- Firebase Firestore에 일별 트래픽 데이터 저장
- Windows Task Scheduler를 통한 자동 일일 크롤링 (매일 오전 3시)
- GitHub Actions를 통한 자동 일일 크롤링 (UTC 자정)

### 데이터 시각화
- **실시간 순위 테이블**
  - 현재 온라인 플레이어 수 기준 순위
  - 모든 컬럼별 정렬 기능 (클릭하여 오름차순/내림차순 전환)
  - GG Poker 네트워크 사이트 하이라이트
  
- **차트 및 그래프**
  - 4가지 메트릭별 독립적인 상위 10개 사이트의 일별 트렌드 라인 차트:
    - Players Online (온라인 플레이어)
    - Cash Players (캐시 게임 플레이어)
    - 24h Peak (24시간 최고치)
    - 7-Day Average (7일 평균)
  - 각 메트릭별로 전체 47개 사이트 중 상위 10개를 독립적으로 선정하여 표시
  
### 사용자 인터페이스
- 탭 네비게이션 (테이블 뷰 / 차트 뷰)
- 반응형 디자인
- 데이터 새로고침 및 크롤링 트리거 버튼
- 인터랙티브 차트 (호버 툴팁, 범례 클릭)

## 기술 스택

*   **프론트엔드:** React (TypeScript), Chart.js (react-chartjs-2), CSS
*   **백엔드:** Python (FastAPI), APScheduler
*   **데이터베이스:** Firebase (Firestore)
*   **크롤링:** Python (Cloudscraper, BeautifulSoup)
*   **배포:** Docker, GitHub Actions, Render (백엔드), Vercel (프론트엔드)
*   **버전 관리:** Git / GitHub

## 로컬 환경 설정

이 프로젝트는 Docker Compose를 사용하여 로컬 개발 환경을 쉽게 설정할 수 있습니다. (단, 현재 Docker 환경 문제로 인해 로컬 환경에서 직접 실행하는 것을 권장합니다.)

1.  **저장소 클론:**
    ```bash
    git clone https://github.com/garimto81/poker-online-analyze.git
    cd poker-online-analyze
    ```

2.  **Firebase 서비스 계정 키 설정:**
    - Firebase Console에서 프로젝트 생성 후 서비스 계정 키를 다운로드합니다.
    - 로컬 개발 환경에서는 `backend/key/` 디렉토리를 생성하고 키 파일을 `firebase-service-account-key.json`으로 저장합니다:
    ```bash
    mkdir -p backend/key
    # firebase-service-account-key.json 파일을 backend/key/ 디렉토리에 복사
    ```
    - **주의:** 이 키 파일은 절대 Git에 커밋하지 마세요! `.gitignore`에 이미 포함되어 있습니다.

3.  **Docker Compose 실행 (선택 사항 - 현재 로컬 직접 실행 권장):**
    ```bash
    docker-compose up --build
    ```
    *   **참고:** Windows 환경에서 Docker Desktop 권한 문제로 `docker-compose up`이 실패할 수 있습니다. Docker Desktop이 실행 중인지 확인하고, 관리자 권한으로 터미널을 실행해야 합니다.

4.  **로컬에서 직접 실행 (권장):**
    *   **백엔드 (FastAPI):**
        ```bash
        cd backend
        pip install -r requirements.txt
        uvicorn main:app --reload --port 4001
        ```
    *   **프론트엔드 (React):**
        ```bash
        cd frontend
        npm install
        npm start  # 자동으로 포트 4000 사용
        ```
    *   **또는 start_servers.bat 사용 (Windows):**
        ```bash
        start_servers.bat
        ```

## GitHub Actions CI/CD

이 프로젝트는 GitHub Actions를 사용하여 지속적 통합(CI) 및 지속적 배포(CD)를 자동화합니다.

### 워크플로우

*   `.github/workflows/backend-ci.yml`: 백엔드 코드에 대한 CI (린팅, 테스트)를 수행합니다. Pull Request 시 자동 실행됩니다.
*   `.github/workflows/frontend-ci.yml`: 프론트엔드 코드에 대한 CI (테스트, 빌드)를 수행합니다. Pull Request 시 자동 실행됩니다.
*   `.github/workflows/deploy-backend.yml`: `main` 브랜치에 백엔드 코드 변경 사항이 푸시될 때 Render에 자동 배포합니다.
*   `.github/workflows/deploy-frontend.yml`: `main` 브랜치에 프론트엔드 코드 변경 사항이 푸시될 때 Vercel에 자동 배포합니다.
*   `.github/workflows/schedule-crawler.yml`: 매일 자정(UTC)에 PokerScout 크롤러를 실행하여 데이터를 수집합니다.

### Secrets 설정

배포 워크플로우가 정상적으로 작동하려면 GitHub 저장소의 `Settings > Secrets > Actions`에 다음 Secret을 추가해야 합니다.

*   `RENDER_BUILD_HOOK_URL`: Render 백엔드 서비스의 Build Hook URL
*   `RENDER_API_KEY`: (선택 사항) Render API 키
*   `VERCEL_TOKEN`: Vercel 배포 토큰
*   `FIREBASE_SERVICE_ACCOUNT_KEY`: Firebase 서비스 계정 키 (JSON 형식의 문자열)

## API 엔드포인트

백엔드는 다음과 같은 RESTful API 엔드포인트를 제공합니다:

- `GET /api/firebase/current_ranking/` - 현재 시점의 전체 사이트 순위
- `GET /api/firebase/top10_daily_stats/?days=7` - 상위 10개 사이트의 일별 통계 (날짜별 점유율 포함)
- `POST /api/firebase/crawl_and_save_data/` - 수동 크롤링 트리거
- `GET /api/firebase/traffic_history/{site_name}?days=7` - 특정 사이트의 트래픽 이력

API 문서는 `http://localhost:4001/docs` (FastAPI 자동 생성 문서)에서 확인할 수 있습니다.

## Windows 자동 크롤링 설정

### 설정 방법
1. **관리자 권한**으로 `setup_scheduler.bat` 실행
2. Windows 작업 스케줄러에 "PokerDataCrawler" 작업이 등록됨
3. 매일 오전 3시에 자동으로 데이터 수집

### 수동 실행
```bash
# 작업 스케줄러를 통한 즉시 실행
schtasks /run /tn "PokerDataCrawler"

# 또는 직접 실행
auto_crawl.bat
```

### 로그 확인
- 크롤링 로그: `backend/logs/crawler_YYYYMMDD.log`
- 간단한 실행 로그: `crawl_log.txt`

## 배포

*   **백엔드:** Render
*   **프론트엔드:** Vercel

## 기여

기여를 환영합니다! Pull Request를 통해 코드 변경 사항을 제안해주세요. 자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) (아직 없음) 파일을 참조해주세요.
