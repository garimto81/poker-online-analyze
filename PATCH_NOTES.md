# 패치 노트 및 진행 상황 로그

이 문서는 `poker-online-analyze` 프로젝트의 주요 변경 사항과 진행 상황을 기록합니다.

---

## 2025년 1월 31일

### 🚀 v2.1.0 - 시장 점유율 분석 기능 업데이트

#### 주요 기능 추가

1. **시장 점유율 계산 및 표시**
   - 각 포커 사이트의 Players Online 점유율(%) 계산
   - 각 포커 사이트의 Cash Players 점유율(%) 계산
   - 테이블에 Share % 컬럼 2개 추가
   - Summary 섹션에 GG Poker 전체 시장 점유율 표시
   - 정렬 가능한 새로운 컬럼으로 추가

2. **누적 차트 (Stacked Area Chart) 구현**
   - 시장 점유율 분포를 시각적으로 표현하는 누적 차트 추가
   - Players Online 시장 점유율 분포 차트
   - Cash Players 시장 점유율 분포 차트
   - 상위 10개 사이트의 점유율을 100% 누적으로 표현
   - 시간에 따른 시장 점유율 변화를 직관적으로 추적 가능
   - 툴팁에 백분율과 실제 플레이어 수 동시 표시

3. **숫자 포맷팅 개선**
   - 모든 숫자에 3자리마다 쉼표(,) 추가로 가독성 향상
   - 이미 적용되어 있던 `.toLocaleString()` 메서드 확인

4. **Firebase 데이터 입력 문제 해결**
   - GitHub Actions에서 Firebase Admin SDK 초기화 실패 문제 해결
   - Firestore REST API를 사용하는 새로운 크롤러 구현
   - 서비스 계정 키 없이도 공개 REST API로 데이터 업로드 가능
   - traffic_logs 문서 ID 형식 통일 (ISO 타임스탬프 사용)

#### 기술적 변경사항

**Frontend:**
- `App.tsx`: 점유율 계산 로직 추가, 테이블 컬럼 확장
- `MarketShareStackedChart.tsx`: 새로운 차트 컴포넌트 생성
- Chart.js Filler 플러그인 추가로 영역 차트 구현

**Backend:**
- `github_actions_crawler_firestore.py`: REST API 기반 크롤러 구현
- `.github/workflows/daily-crawl.yml`: 새로운 크롤러 사용하도록 업데이트
- Google Auth 라이브러리 의존성 추가

#### 파일 변경 목록
- 수정: `frontend/src/App.tsx`
- 생성: `frontend/src/components/MarketShareStackedChart.tsx`
- 생성: `backend/github_actions_crawler_firestore.py`
- 생성: `backend/github_actions_crawler_v2.py`
- 생성: `backend/github_actions_crawler_rest.py`
- 수정: `.github/workflows/daily-crawl.yml`
- 수정: `README.md`
- 수정: `PATCH_NOTES.md`

---

## 2025년 7월 28일

### CI/CD: 프론트엔드 워크플로우 디버깅

`main` 브랜치로의 Pull Request 시 실행되는 프론트엔드 CI 워크플로우 (`.github/workflows/frontend-ci.yml`)에서 발생하는 `npm error ENOENT` 오류를 해결하기 위한 집중적인 디버깅을 진행했습니다.

#### 문제 현상

*   GitHub Actions 실행 환경에서 `npm install` 명령이 `frontend/package.json` 파일을 찾지 못하는 오류가 지속적으로 발생했습니다.
*   오류 로그 분석 결과, `.../poker-online-analyze/poker-online-analyze/frontend/` 와 같이 저장소 이름이 중첩된 비정상적인 경로에서 파일을 찾으려고 시도하는 것이 확인되었습니다.

#### 해결 과정

1.  **1차 시도 (체크아웃 경로 수정):**
    *   `actions/checkout` 스텝의 `with: path: ./` 설정이 경로 중첩의 원인으로 의심되어 해당 부분을 제거했습니다.
    *   **결과:** 문제 해결에 실패했습니다.

2.  **2차 시도 (디버깅 스텝 추가):**
    *   정확한 원인 파악을 위해 워크플로우에 `ls -R` 명령을 추가하여 Actions 실행 환경의 실제 파일 및 폴더 구조를 확인하는 단계를 추가했습니다.

3.  **3차 시도 (`--prefix` 옵션 사용):**
    *   `working-directory` 설정 대신, `npm` 명령어에 `--prefix ./frontend` 옵션을 직접 추가하여 작업 경로를 명시적으로 지정하는 방식을 시도했습니다.
    *   **결과:** 문제 해결에 실패했습니다.

4.  **최종 해결 시도 (명시적 경로 지정):**
    *   오류 로그에 나타난 경로(`.../poker-online-analyze/poker-online-analyze/frontend/`)를 역으로 이용하여, `working-directory`를 `./poker-online-analyze/frontend` 로 명확하게 지정했습니다. 이는 오류가 발생하는 바로 그 경로를 직접 타겟팅하는 가장 확실한 방법입니다.

### 파일 변경 요약

*   **.github/workflows/frontend-ci.yml**: 지속적인 경로 문제 해결을 위해 여러 차례 수정되었습니다.
