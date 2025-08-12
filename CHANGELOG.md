# Changelog

## [2025-08-12] - 테이블 정렬 기능 개선 및 Firebase 에러 해결

### 추가됨
- 테이블 기본 정렬을 온라인 플레이어 수 내림차순으로 변경
- 모든 헤더 클릭 시 정렬 방향 토글 기능
- 정렬 상태 시각적 피드백 (↑ ↓ ↕ 아이콘)
- 현재 정렬 컬럼 배경색 강조
- 정적 JSON 데이터 서비스 구현

### 수정됨
- Firebase 429 Rate Limit 에러를 정적 JSON 파일로 우회
- 차트 렌더링 오류 수정 (current_stats 필드 추가)
- 헤더 클릭 시 데이터 중복 오류 수정
- useCallback, useMemo를 사용한 성능 최적화
- 초기 데이터 로드 시 중복 호출 방지

### 제거됨
- Firebase 직접 API 호출 의존성
- 불필요한 리렌더링 로직

## [2025-01-31] - 초기 배포

### 추가됨
- PokerScout 데이터 크롤링 기능
- React 프론트엔드 구현
- Chart.js를 사용한 데이터 시각화
- GitHub Pages 배포 설정
- 시장 점유율 계산 및 표시 기능
- 누적 차트 (Stacked Area Chart) 구현

### 기술 스택
- Frontend: React (TypeScript), Chart.js
- Data: 정적 JSON 파일
- Crawling: Python (CloudScraper, BeautifulSoup)
- Deployment: GitHub Pages