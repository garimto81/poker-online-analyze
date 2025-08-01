# 🎰 포커 온라인 분석 프로젝트 기획서 v3.1

## 📋 프로젝트 개요

### 프로젝트명
**Poker Online Analyze** - 온라인 포커 사이트 트래픽 분석 및 시각화 플랫폼

### 버전 정보
- **현재 버전**: v3.1 (2025-08-01)
- **주요 업데이트**: 누적 차트 수치 표시 개선 및 스마트 툴팁 구현
- **이전 버전**: v3.0 (차트 타입 선택), v2.1.0 (시장 점유율 분석), v2.0 (누적 영역 차트)

### 프로젝트 목적
PokerScout.com에서 59개 온라인 포커 사이트의 실시간 트래픽 데이터를 수집하여 트렌드 분석과 비교 정보를 제공하는 웹 애플리케이션

## 🏗️ 시스템 아키텍처

### 전체 시스템 구조
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  GitHub Pages   │────▶│ Vercel Functions│────▶│    Firebase     │
│   (Frontend)    │     │   (Backend API) │     │   (Database)    │
│  React + Chart.js│     │   Python/FastAPI│     │   Firestore     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         ▲                                                ▲
         │                                                │
         └────────────── GitHub Actions ──────────────────┘
                    (Daily Data Crawling)
```

### 기술 스택

#### 프론트엔드
- **Framework**: React 18.2.0 + TypeScript 4.9.5
- **UI Libraries**: Chart.js 4.4.1, react-chartjs-2 5.2.0
- **Build Tool**: Create React App
- **Styling**: CSS3, Responsive Design
- **HTTP Client**: Axios 1.6.2

#### 백엔드
- **API Framework**: FastAPI 0.104.1
- **Runtime**: Python 3.9+
- **Web Server**: Uvicorn 0.24.0
- **Database ORM**: Firebase Admin SDK 6.2.0

#### 데이터 수집
- **Web Scraping**: Cloudscraper 1.2.71, BeautifulSoup4 4.12.2
- **HTTP Library**: Requests 2.31.0
- **Parser**: lxml 4.9.3

#### 인프라 & 배포
- **Frontend Hosting**: GitHub Pages (무료)
- **Backend Hosting**: Vercel Serverless Functions (무료)
- **Database**: Firebase Firestore (무료)
- **CI/CD**: GitHub Actions
- **Domain**: github.io subdomain

## 🎨 주요 기능 명세

### 1. 데이터 수집 시스템
- **자동 크롤링**: 매일 UTC 18:00 (한국시간 오전 3시)
- **데이터 소스**: PokerScout.com
- **수집 대상**: 59개 온라인 포커 사이트
- **수집 정보**:
  - 사이트명 및 카테고리
  - 현재 접속자 수 (Players Online)
  - 캐시 게임 플레이어 수 (Cash Players)
  - 24시간 최고 접속자 수 (24h Peak)
  - 7일 평균 접속자 수 (7-Day Average)

### 2. 실시간 데이터 표시
- **테이블 뷰**: 정렬 가능한 포커 사이트 순위표
- **시장 점유율**: 개별 사이트별 점유율 계산 및 표시
- **GG Poker 네트워크**: 특별 카테고리 하이라이팅
- **요약 통계**: 전체 사이트 수, 총 플레이어 수, 시장 점유율

### 3. **차트 시각화 시스템 (v3.1 최신)**

#### 3.1 차트 타입 선택 기능
사용자가 데이터를 다양한 방식으로 시각화할 수 있도록 3가지 차트 타입 제공:

##### 📈 선형 차트 (Line Chart)
- **용도**: 개별 사이트별 트렌드 분석
- **특징**: 
  - `fill: false` (영역 채우기 없음)
  - `stacked: false` (개별 라인)
  - 각 사이트의 독립적인 변화 추세 확인
  - 사이트간 성장률 비교 최적화

##### 📊 누적 차트 (Stacked Area Chart) - v3.1 개선
- **용도**: 전체 시장 규모와 사이트별 기여도 분석
- **특징**:
  - `fill: 'origin'/-1` (누적 영역 표시)
  - `stacked: true` (Y축 누적)
  - **실제 수치 표시**: 백분율이 아닌 플레이어 수로 표시
  - **전체 시장 표현**: 상위 10개 + 나머지 'Others (X sites)'로 그룹화
  - **스마트 툴팁**: 마우스 호버 시 차트 외부에 툴팁 표시

##### 📊 막대 차트 (Bar Chart)
- **용도**: 시점별 사이트간 비교 분석
- **특징**:
  - `type: 'bar'` (막대형 표시)
  - `stacked: true` (누적 막대)
  - 특정 시점에서의 사이트별 성과 비교
  - 일별/주별 변화량 직관적 확인

#### 3.2 UI/UX 구현
- **버튼 레이아웃**: 중앙 정렬, 반응형 디자인
- **시각적 피드백**: 활성 상태 파란색 배경 (#007bff)
- **아이콘 사용**: 이모지로 차트 타입 직관적 구분
- **상태 관리**: React useState 훅 활용
- **동적 렌더링**: 선택에 따른 실시간 차트 변경

#### 3.3 기술적 구현
```typescript
// 차트 타입 정의
type ChartType = 'line' | 'stacked' | 'bar';

// 상태 관리
const [chartType, setChartType] = useState<ChartType>('stacked');

// 조건부 데이터셋 구성
switch (chartType) {
  case 'stacked':
    return { fill: index === 0 ? 'origin' : '-1', ... };
  case 'line':
    return { fill: false, ... };
  case 'bar':
    return { backgroundColor: color + '80', ... };
}
```

### 4. **스마트 툴팁 시스템 (v3.1 신규)**

#### 4.1 외부 툴팁 기능
- **마우스 호버 전용**: 평상시에는 깔끔한 차트만 표시
- **차트 비차단**: 툴팁이 차트를 가리지 않도록 외부에 표시
- **자동 위치 조정**: 화면 경계 감지하여 툴팁 위치 자동 조정
- **상위 10개 표시**: 많은 사이트 중 상위 10개만 정렬하여 표시
- **스마트 포맷팅**: K/M 단위 자동 축약 (예: 25K, 1.2M)

#### 4.2 기술적 구현
```typescript
// 외부 툴팁 생성
external: function(context) {
  const tooltipEl = document.getElementById('chartjs-tooltip');
  // 동적 HTML 생성 및 위치 계산
  // 화면 경계 체크 및 자동 위치 조정
}
```

#### 4.3 UX 개선사항
- **색상 인디케이터**: 각 사이트별 색상 구분점
- **정렬된 표시**: 플레이어 수 기준 내림차순 정렬
- **추가 사이트 알림**: 10개 초과 시 "...and X more" 표시
- **부드러운 애니메이션**: 0.1초 전환 효과

### 5. 사용자 인터페이스
- **반응형 디자인**: 모바일/태블릿/데스크톱 지원
- **탭 네비게이션**: Table View ↔ Charts View
- **실시간 갱신**: 수동 새로고침 버튼
- **정렬 기능**: 모든 컬럼 오름차순/내림차순 정렬
- **데이터 트리거**: 수동 크롤링 실행 버튼

## 📊 데이터 플로우

### 1. 데이터 수집 프로세스
```
PokerScout.com → Cloudscraper → BeautifulSoup → Firebase Firestore
     ↓
GitHub Actions (매일 3AM KST) → Python 크롤러 → 데이터 저장
```

### 2. 데이터 제공 프로세스
```
사용자 요청 → React App → Vercel API → Firebase → 데이터 반환 → Chart.js 시각화
```

### 3. 실시간 워크플로우
```
1. GitHub Actions: 자동 데이터 수집
2. Firebase: 실시간 데이터베이스 업데이트
3. Vercel API: RESTful 엔드포인트 제공
4. React App: 동적 차트 렌더링
5. GitHub Pages: 정적 사이트 호스팅
```

## 🚀 배포 및 운영

### CI/CD 파이프라인

#### GitHub Actions 워크플로우
1. **`deploy-github-pages.yml`**
   - 트리거: `main` 브랜치 push
   - 과정: Node.js 18 → npm install → npm build → GitHub Pages 배포
   - 환경변수: `REACT_APP_API_URL=https://poker-analyzer-api.vercel.app`

2. **`daily-crawl.yml`**
   - 트리거: 매일 UTC 18:00 + 수동 실행
   - 과정: Python 3.9 → 의존성 설치 → 크롤링 실행 → Firebase 저장

### 환경별 URL
- **프론트엔드**: https://garimto81.github.io/poker-online-analyze/
- **백엔드 API**: https://poker-analyzer-api.vercel.app
- **API 문서**: https://poker-analyzer-api.vercel.app/docs
- **모니터링**: https://github.com/garimto81/poker-online-analyze/actions

### 보안 설정
- **GitHub Secrets**: Firebase 서비스 계정 키 암호화 저장
- **CORS 설정**: 허용된 도메인만 API 접근
- **Rate Limiting**: Vercel 자동 제한
- **Data Validation**: 입력 데이터 검증 및 정제

## 🧪 테스트 및 품질 보증

### 테스트 환경 구성
- **로컬 개발**: `npm start` (포트 3000)
- **빌드 테스트**: `npm run build` → 정적 파일 생성
- **API 테스트**: Postman/curl을 통한 엔드포인트 검증
- **통합 테스트**: 프론트엔드 ↔ 백엔드 ↔ 데이터베이스

### 품질 관리
- **TypeScript**: 컴파일 타임 타입 검증
- **ESLint**: 코드 품질 및 스타일 검사
- **Error Handling**: try-catch 블록 및 fallback 로직
- **Performance**: Chart.js 최적화 및 데이터 캐싱

### 테스트 결과 (v3.1)
- ✅ **소스 코드 검증**: 누적 차트 수치 표시 및 툴팁 시스템 완전 구현
- ✅ **빌드 시스템**: npm build 성공 (123.24 kB gzipped)
- ✅ **배포 프로세스**: GitHub Actions 배포 성공 (run #22)
- ✅ **기능 테스트**: 전체 시장 표현 및 스마트 툴팁 확인
- ✅ **로컬 서버**: TypeScript 컴파일 오류 해결 완료
- ✅ **CI/CD**: 빌드 실패 문제 진단 및 해결

## 📈 성능 및 최적화

### 프론트엔드 최적화
- **Code Splitting**: React.lazy를 통한 지연 로딩
- **Memoization**: React.memo 및 useMemo 활용
- **Bundle Size**: 123.24 kB (gzipped) 최적화
- **Caching**: 브라우저 캐시 활용
- **Chart Optimization**: 외부 툴팁으로 렌더링 성능 향상
- **Memory Management**: 컴포넌트 언마운트 시 DOM 정리

### 백엔드 최적화
- **Serverless**: 사용량 기반 자동 스케일링
- **Database Indexing**: Firestore 쿼리 최적화
- **Response Caching**: 실시간성과 성능 균형

### 비용 최적화
- **완전 무료 운영**: 모든 서비스 무료 플랜 활용
- **Resource Monitoring**: 사용량 추적 및 알림
- **Efficient Queries**: 필요한 데이터만 조회

## 🔧 유지보수 및 모니터링

### 로깅 및 모니터링
- **GitHub Actions**: 배포 및 크롤링 상태 추적
- **Vercel Insights**: API 성능 및 오류 모니터링
- **Firebase Console**: 데이터베이스 상태 및 사용량
- **Error Tracking**: 프론트엔드 JavaScript 오류 캐치

### 백업 및 복구
- **Source Code**: Git 버전 관리
- **Database**: Firebase 자동 백업
- **Static Assets**: GitHub Pages 자동 보관
- **Configuration**: 환경 변수 및 시크릿 관리

## 🎯 향후 발전 계획

### v3.1 예정 기능
- **차트 내보내기**: PNG/SVG 다운로드 기능
- **데이터 필터링**: 날짜 범위 및 사이트 선택 필터
- **알림 시스템**: 특정 조건 달성 시 알림
- **모바일 앱**: React Native 기반 모바일 버전

### 기술적 개선사항
- **실시간 업데이트**: WebSocket 연결로 실시간 데이터
- **PWA 지원**: 오프라인 모드 및 설치 가능
- **다국어 지원**: i18n 국제화
- **A/B 테스트**: 사용자 경험 최적화

## 📝 변경 이력

### v3.1 (2025-08-01) - 누적 차트 개선 및 스마트 툴팁
- ✨ **NEW**: 스마트 툴팁 시스템 구현
  - 마우스 호버 시에만 차트 외부에 툴팁 표시
  - 화면 경계 자동 감지 및 위치 조정
  - 상위 10개 사이트만 정렬하여 표시
- 🔧 **IMPROVE**: 누적 차트 데이터 표현 방식 개선
  - 100% 누적에서 실제 수치 누적으로 변경
  - 상위 10개 + 나머지 'Others (X sites)' 그룹화
  - Y축 레이블을 실제 플레이어 수로 변경
- 🔧 **IMPROVE**: 전체 시장 규모 정확한 표현
  - 모든 59개 사이트 데이터 포함
  - 11위 이하 사이트들을 'Others'로 통합 표시
- 🐛 **FIX**: TypeScript 빌드 오류 해결
  - datalabels 플러그인 옵션 제거
  - 사용하지 않는 import 정리
- 🚀 **DEPLOY**: GitHub Actions 배포 문제 해결
  - 배포 실패 원인 분석 및 수정
  - CI/CD 파이프라인 안정화

### v3.0 (2025-07-31)
- ✨ **NEW**: 차트 타입 선택 기능 (선형/누적/막대)
- ✨ **NEW**: Chart.js BarElement 지원 추가
- 🔧 **IMPROVE**: 동적 차트 옵션 시스템
- 🔧 **IMPROVE**: 사용자 인터페이스 개선
- 🐛 **FIX**: GitHub Pages 배포 브랜치 이슈 해결

### v2.1.0 (2025-07-30)
- ✨ **NEW**: 시장 점유율 분석 기능
- ✨ **NEW**: MarketShareChart 컴포넌트
- 🔧 **IMPROVE**: 데이터 시각화 강화

### v2.0 (2025-07-30)
- ✨ **NEW**: 누적 영역 차트 (Stacked Area Chart)
- 🔧 **IMPROVE**: Chart.js Filler 플러그인 활용
- 🔧 **IMPROVE**: 전체 시장 규모 시각화

### v1.0 (2025-07-29)
- 🎉 **INITIAL**: 기본 포커 사이트 트래픽 분석
- 🎉 **INITIAL**: 자동 데이터 수집 시스템
- 🎉 **INITIAL**: GitHub Pages 배포

## 👥 프로젝트 정보

### 개발팀
- **메인 개발자**: garimto81
- **AI 어시스턴트**: Claude Code (Anthropic)
- **저장소**: https://github.com/garimto81/poker-online-analyze

### 라이선스
- **오픈소스**: MIT License (예정)
- **데이터**: PokerScout.com 공개 데이터 활용
- **무료 사용**: 개인 및 상업적 목적 무료

### 연락처
- **GitHub Issues**: https://github.com/garimto81/poker-online-analyze/issues
- **Live Demo**: https://garimto81.github.io/poker-online-analyze/

---

*이 문서는 Claude Code와 함께 작성되었습니다. 최종 업데이트: 2025-08-01*

## 🔧 기술적 구현 세부사항 (v3.1)

### 누적 차트 데이터 처리 로직
```typescript
// 전체 사이트 분류
const allSortedSites = Object.entries(data)
  .sort(([, a], [, b]) => b.current_stats[metric] - a.current_stats[metric]);
const top10Sites = allSortedSites.slice(0, 10);
const etcSites = allSortedSites.slice(10);

// 11위 이하 사이트들의 합계 계산
const etcValuesByDate: { [date: string]: number } = {};
sortedDates.forEach(date => {
  let etcTotal = 0;
  etcSites.forEach(([, siteData]) => {
    const dayData = siteData.daily_data.find(
      d => new Date(d.date).toLocaleDateString() === date
    );
    if (dayData) {
      etcTotal += dayData[metric];
    }
  });
  etcValuesByDate[date] = etcTotal;
});
```

### 외부 툴팁 구현
```typescript
tooltip: {
  enabled: false, // 기본 툴팁 비활성화
  external: function(context) {
    // 동적 DOM 요소 생성
    const tooltipEl = document.getElementById('chartjs-tooltip') || 
      createTooltipElement();
    
    // 상위 10개 사이트만 필터링 및 정렬
    const sortedItems = tooltip.dataPoints
      .filter((item: any) => item.raw > 0)
      .sort((a: any, b: any) => b.raw - a.raw)
      .slice(0, 10);
    
    // 화면 경계 체크 및 위치 조정
    const tooltipX = position.left + tooltip.caretX + 20;
    const tooltipY = position.top + window.pageYOffset + tooltip.caretY - 50;
    
    if (tooltipX + tooltipWidth > window.innerWidth) {
      tooltipDiv.style.left = (position.left + tooltip.caretX - tooltipWidth - 20) + 'px';
    }
  }
}
```

### 배포 문제 해결 과정
1. **오류 발생**: TypeScript 컴파일 오류 (datalabels 타입 불일치)
2. **원인 분석**: 플러그인 제거 후 옵션 설정 잔존
3. **해결 방법**: datalabels 옵션 완전 제거
4. **검증**: 로컬 빌드 테스트 → GitHub Actions 재배포
5. **결과**: 성공적인 배포 완료 (run #22)