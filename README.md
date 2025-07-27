# Poker Online Analyze

온라인 포커 사이트의 데이터를 수집하고 분석하여 트렌드 및 비교 분석 정보를 제공하는 웹 애플리케이션입니다.

## 프로젝트 개요

이 프로젝트는 PokerScout.com과 같은 온라인 포커 사이트의 데이터를 매일 자동으로 수집하고, 이를 시각화하여 사용자에게 트렌드 및 비교 분석 정보를 제공하는 것을 목표로 합니다.

## 기술 스택

*   **프론트엔드:** React (TypeScript), Chart.js / Recharts, Tailwind CSS / Bootstrap
*   **백엔드:** Python (FastAPI), APScheduler
*   **데이터베이스:** Firebase (Firestore/Realtime Database)
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

2.  **환경 변수 설정:**
    `backend` 디렉토리에 `.env` 파일을 생성하고 다음 내용을 추가합니다. (Firebase 설정에 따라 변경될 수 있습니다.)
    ```
    DATABASE_URL="postgresql://user:password@host:port/database_name"
    # Firebase 서비스 계정 키는 GitHub Secrets에 저장하는 것을 권장합니다.
    # 로컬 테스트 시에는 직접 파일로 생성해야 할 수 있습니다.
    ```

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
        uvicorn main:app --reload
        ```
    *   **프론트엔드 (React):**
        ```bash
        cd frontend
        npm install
        npm start
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

## 배포

*   **백엔드:** Render
*   **프론트엔드:** Vercel

## 기여

기여를 환영합니다! Pull Request를 통해 코드 변경 사항을 제안해주세요. 자세한 내용은 [CONTRIBUTING.md](CONTRIBUTING.md) (아직 없음) 파일을 참조해주세요.
