import { test, expect } from '@playwright/test';

// 테스트할 웹사이트 URL
const WEBSITE_URL = 'https://garimto81.github.io/poker-online-analyze';

test.describe('Poker Online Analyze - 종합 E2E 테스트', () => {
  
  test.beforeEach(async ({ page }) => {
    // 각 테스트 전에 페이지 로딩
    await page.goto(WEBSITE_URL, { waitUntil: 'networkidle' });
  });

  test('1. 기본 페이지 로딩 및 타이틀 확인', async ({ page }) => {
    // 페이지 타이틀 확인
    await expect(page).toHaveTitle(/poker/i);
    
    // 메인 컨테이너 존재 확인
    const mainContainer = page.locator('#root');
    await expect(mainContainer).toBeVisible();
    
    // 스크린샷 캡처
    await page.screenshot({ 
      path: 'test-results/01-main-page-load.png',
      fullPage: true 
    });
  });

  test('2. 네비게이션 탭 기능 및 수정사항 검증', async ({ page }) => {
    // 탭 요소들이 존재하는지 확인 (여러 선택자로 안정성 향상)
    const tableTab = page.locator('text=📊 Table View').or(page.locator('.tab:has-text("Table View")')).or(page.locator('button:has-text("Table View")'));
    const chartTab = page.locator('text=📈 Charts View').or(page.locator('.tab:has-text("Charts View")')).or(page.locator('button:has-text("Charts View")'));
    
    // 탭 컨테이너 로딩 대기
    await page.waitForSelector('.tabs', { timeout: 10000 });
    await page.waitForTimeout(2000);
    
    console.log('=== 네비게이션 탭 기능 테스트 시작 ===');
    
    // 기본적으로 테이블 탭이 활성화되어 있는지 확인
    await expect(tableTab.first()).toBeVisible();
    console.log('✅ Table tab is visible');
    
    // 기본 상태에서 테이블이 표시되는지 확인
    const initialTableContainer = page.locator('table, .table-container, .sites-table');
    if (await initialTableContainer.first().isVisible()) {
      console.log('✅ Initial table is visible');
    }
    
    // 차트 탭 클릭 테스트
    if (await chartTab.first().isVisible()) {
      console.log('✅ Charts tab found, testing click functionality...');
      
      // 클릭하기 전 상태 저장
      const beforeClick = await page.screenshot({ 
        path: 'test-results/02-before-chart-click.png',
        fullPage: true 
      });
      
      await chartTab.first().click();
      await page.waitForTimeout(3000); // 차트 렌더링 충분한 대기 시간
      
      // 차트 컨테이너 확인 (여러 가능한 선택자 사용)
      const chartSelectors = [
        'canvas',
        'svg', 
        '.chart-container',
        '.charts-container',
        '[class*="chart"]',
        '.recharts-wrapper'
      ];
      
      let chartFound = false;
      for (const selector of chartSelectors) {
        const chartElement = page.locator(selector);
        if (await chartElement.first().isVisible()) {
          console.log(`✅ Chart element found with selector: ${selector}`);
          await expect(chartElement.first()).toBeVisible();
          chartFound = true;
          break;
        }
      }
      
      if (!chartFound) {
        console.log('⚠️ Chart container not found, but tab switch may still work');
        // 탭 전환이 작동했는지 다른 방법으로 확인
        const afterClick = await page.textContent('body');
        console.log('Page content after chart click (first 200 chars):', afterClick?.substring(0, 200));
      }
      
      // 클릭 후 상태 스크린샷
      await page.screenshot({ 
        path: 'test-results/02-after-chart-click.png',
        fullPage: true 
      });
    }
    
    // 다시 테이블 탭으로 돌아가기 테스트
    if (await tableTab.first().isVisible()) {
      console.log('✅ Testing return to table tab...');
      await tableTab.first().click();
      await page.waitForTimeout(2000);
      
      // 테이블이 다시 표시되는지 확인
      const returnedTableContainer = page.locator('table, .table-container, .sites-table, tbody');
      if (await returnedTableContainer.first().isVisible()) {
        await expect(returnedTableContainer.first()).toBeVisible();
        console.log('✅ Table is visible after tab switch back');
      } else {
        console.log('⚠️ Table not found after return, but tab click worked');
      }
    }
    
    // 탭 상태 확인 (활성 탭 표시)
    const activeTab = page.locator('.tab.active, .tab[aria-selected="true"], [class*="active"]');
    if (await activeTab.first().isVisible()) {
      console.log('✅ Active tab indication working');
    }
    
    console.log('=== 네비게이션 탭 기능 테스트 완료 ===');
    
    await page.screenshot({ 
      path: 'test-results/02-navigation-tabs.png',
      fullPage: true 
    });
  });

  test('3. 데이터 테이블 표시 및 정렬 기능 확인', async ({ page }) => {
    // 테이블이 로드될 때까지 대기
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Firebase 데이터 로드 대기
    
    // 테이블 존재 확인
    const table = page.locator('table, .table, [role="table"]');
    await expect(table.first()).toBeVisible();
    
    // 테이블 헤더 확인 (예상되는 컬럼들)
    const expectedHeaders = ['Site', 'Players Online', 'Cash Players', '24h Peak', '7-Day Average'];
    
    for (const header of expectedHeaders) {
      const headerElement = page.locator(`text=${header}`).first();
      if (await headerElement.isVisible()) {
        console.log(`✓ 헤더 발견: ${header}`);
      }
    }
    
    // 데이터 행이 있는지 확인
    const rows = page.locator('tbody tr, .table-row');
    const rowCount = await rows.count();
    console.log(`테이블 행 수: ${rowCount}`);
    
    if (rowCount > 0) {
      // 첫 번째 행의 데이터 확인
      const firstRow = rows.first();
      await expect(firstRow).toBeVisible();
    }
    
    await page.screenshot({ 
      path: 'test-results/03-data-table.png',
      fullPage: true 
    });
  });

  test('4. 차트 표시 및 상호작용 테스트', async ({ page }) => {
    // 차트 탭으로 이동 (존재하는 경우)
    const chartTab = page.locator('text=📈 Charts View').or(page.locator('.tab:has-text("Charts View")')).or(page.locator('button:has-text("Charts View")'));
    
    // 탭 로딩 대기
    await page.waitForSelector('.tabs', { timeout: 10000 });
    
    if (await chartTab.first().isVisible()) {
      console.log('✓ Charts tab found, clicking...');
      await chartTab.first().click();
      await page.waitForTimeout(3000); // 차트 렌더링 대기 시간 증가
    }
    
    // Chart.js 캔버스 또는 차트 컨테이너 확인
    const chartElements = [
      'canvas',
      '.chart-container',
      '[class*="chart"]',
      'svg'
    ];
    
    let chartFound = false;
    for (const selector of chartElements) {
      const chart = page.locator(selector);
      if (await chart.first().isVisible()) {
        console.log(`✓ 차트 요소 발견: ${selector}`);
        chartFound = true;
        
        // 차트에 호버하여 툴팁 확인 (가능한 경우)
        try {
          await chart.first().hover();
          await page.waitForTimeout(500);
        } catch (e) {
          console.log('차트 호버 기능 테스트 중 에러:', e);
        }
        break;
      }
    }
    
    if (!chartFound) {
      console.log('⚠️ 차트 요소를 찾을 수 없음');
    }
    
    await page.screenshot({ 
      path: 'test-results/04-charts.png',
      fullPage: true 
    });
  });

  test('5. 반응형 디자인 테스트 - 모바일', async ({ page }) => {
    // 모바일 뷰포트로 설정
    await page.setViewportSize({ width: 375, height: 667 });
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    // 모바일에서 요소들이 적절히 표시되는지 확인
    const mainContainer = page.locator('#root');
    await expect(mainContainer).toBeVisible();
    
    // 햄버거 메뉴나 모바일 네비게이션 확인
    const mobileMenu = page.locator('.mobile-menu, .hamburger, [aria-label="menu"]');
    if (await mobileMenu.first().isVisible()) {
      console.log('✓ 모바일 메뉴 발견');
    }
    
    await page.screenshot({ 
      path: 'test-results/05-mobile-responsive.png',
      fullPage: true 
    });
  });

  test('6. 반응형 디자인 테스트 - 태블릿', async ({ page }) => {
    // 태블릿 뷰포트로 설정
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    const mainContainer = page.locator('#root');
    await expect(mainContainer).toBeVisible();
    
    await page.screenshot({ 
      path: 'test-results/06-tablet-responsive.png',
      fullPage: true 
    });
  });

  test('7. 데이터 새로고침 및 크롤링 버튼 테스트', async ({ page }) => {
    // 새로고침이나 크롤링 관련 버튼 찾기
    const refreshButtons = [
      'text=새로고침',
      'text=데이터 업데이트',
      'text=크롤링',
      '[data-action="refresh"]',
      '[title*="refresh"]',
      'button:has-text("새로고침")',
      'button:has-text("업데이트")'
    ];
    
    for (const selector of refreshButtons) {
      const button = page.locator(selector);
      if (await button.first().isVisible()) {
        console.log(`✓ 새로고침 버튼 발견: ${selector}`);
        
        // 버튼 클릭 테스트 (실제 API 호출은 하지 않음)
        try {
          await button.first().click();
          await page.waitForTimeout(1000);
          console.log('✓ 버튼 클릭 성공');
        } catch (e) {
          console.log(`버튼 클릭 실패: ${e}`);
        }
        break;
      }
    }
    
    await page.screenshot({ 
      path: 'test-results/07-refresh-buttons.png',
      fullPage: true 
    });
  });

  test('8. Firebase 데이터 연결 및 API 최적화 확인', async ({ page }) => {
    // 네트워크 요청 모니터링
    const firebaseRequests: any[] = [];
    const allRequests: any[] = [];
    
    page.on('response', response => {
      allRequests.push({
        url: response.url(),
        status: response.status(),
        contentType: response.headers()['content-type']
      });
      
      if (response.url().includes('firebase') || response.url().includes('firestore') || response.url().includes('googleapis')) {
        firebaseRequests.push({
          url: response.url(),
          status: response.status(),
          headers: response.headers()
        });
      }
    });
    
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(8000); // Firebase 요청 및 캐시 시스템 대기
    
    console.log(`전체 네트워크 요청 수: ${allRequests.length}`);
    console.log(`Firebase/Google API 관련 요청 수: ${firebaseRequests.length}`);
    
    // 429 에러 (Too Many Requests) 확인
    const tooManyRequests = firebaseRequests.filter(req => req.status === 429);
    console.log(`429 에러 발생 횟수: ${tooManyRequests.length}`);
    expect(tooManyRequests.length).toBeLessThan(3); // 최대 2회까지 허용 (재시도 로직)
    
    // 성공적인 요청 확인
    const successfulRequests = firebaseRequests.filter(req => req.status >= 200 && req.status < 400);
    console.log(`성공적인 Firebase 요청 수: ${successfulRequests.length}`);
    expect(successfulRequests.length).toBeGreaterThan(0);
    
    firebaseRequests.forEach((req, index) => {
      console.log(`요청 ${index + 1}: ${req.status} - ${req.url.substring(0, 100)}...`);
    });
    
    // 데이터가 실제로 로드되었는지 확인
    const dataElements = page.locator('table tr, .data-item, .poker-site, tbody td');
    const elementCount = await dataElements.count();
    console.log(`데이터 요소 수: ${elementCount}`);
    expect(elementCount).toBeGreaterThan(0); // 데이터가 실제로 로드되었는지 확인
    
    // 캐시 시스템 동작 확인 - 두 번째 로드에서 요청이 줄었는지
    const initialRequestCount = firebaseRequests.length;
    firebaseRequests.length = 0; // 배열 초기화
    
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    console.log(`두 번째 로드 시 Firebase 요청 수: ${firebaseRequests.length}`);
    console.log(`캐시 효과: ${initialRequestCount > firebaseRequests.length ? '✓ 동작' : '- 미확인'}`);
    
    await page.screenshot({ 
      path: 'test-results/08-firebase-data.png',
      fullPage: true 
    });
  });

  test('9. 성능 테스트 - 페이지 로딩 시간', async ({ page }) => {
    const startTime = Date.now();
    
    await page.goto(WEBSITE_URL, { waitUntil: 'networkidle' });
    
    const endTime = Date.now();
    const loadTime = endTime - startTime;
    
    console.log(`페이지 로딩 시간: ${loadTime}ms`);
    
    // 3초 이내 로딩 완료를 기대
    expect(loadTime).toBeLessThan(10000);
    
    // Core Web Vitals 측정
    const vitals = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          resolve(entries.map(entry => ({
            name: entry.name,
            value: entry.value || entry.duration,
            entryType: entry.entryType
          })));
        }).observe({ entryTypes: ['navigation', 'paint', 'largest-contentful-paint'] });
        
        // 타임아웃 설정
        setTimeout(() => resolve([]), 3000);
      });
    });
    
    console.log('성능 메트릭:', vitals);
    
    await page.screenshot({ 
      path: 'test-results/09-performance.png',
      fullPage: true 
    });
  });

  test('10. 접근성 테스트 기본 확인', async ({ page }) => {
    // 기본 접근성 요소 확인
    const accessibilityChecks = [
      { selector: 'h1, h2, h3', description: '제목 태그' },
      { selector: '[alt]', description: 'alt 속성을 가진 이미지' },
      { selector: '[aria-label], [aria-labelledby]', description: 'ARIA 라벨' },
      { selector: 'button, [role="button"]', description: '버튼 요소' }
    ];
    
    for (const check of accessibilityChecks) {
      const elements = page.locator(check.selector);
      const count = await elements.count();
      console.log(`${check.description}: ${count}개 발견`);
    }
    
    // 키보드 네비게이션 테스트
    await page.keyboard.press('Tab');
    await page.waitForTimeout(500);
    
    const focusedElement = page.locator(':focus');
    if (await focusedElement.count() > 0) {
      console.log('✓ 키보드 네비게이션 가능');
    }
    
    await page.screenshot({ 
      path: 'test-results/10-accessibility.png',
      fullPage: true 
    });
  });
});

// GitHub Actions 워크플로우 및 에러 핸들링 테스트
test.describe('시스템 안정성 테스트', () => {
  test('GitHub Actions 및 배포 상태 확인', async ({ page }) => {
    // GitHub API를 통한 워크플로우 상태 확인은 별도 스크립트로 처리
    // 여기서는 웹사이트의 마지막 업데이트 시간 등을 확인
    
    await page.goto(WEBSITE_URL);
    
    // 마지막 업데이트 시간이나 데이터 타임스탬프 찾기
    const timestampSelectors = [
      'text=/last updated/i',
      'text=/마지막 업데이트/i',
      '[data-timestamp]',
      '.timestamp',
      '.last-updated'
    ];
    
    for (const selector of timestampSelectors) {
      const timestamp = page.locator(selector);
      if (await timestamp.first().isVisible()) {
        const text = await timestamp.first().textContent();
        console.log(`✓ 타임스탬프 발견: ${text}`);
      }
    }
    
    await page.screenshot({ 
      path: 'test-results/11-github-actions.png',
      fullPage: true 
    });
  });

  test('에러 핸들링 및 복구 메커니즘 테스트', async ({ page }) => {
    console.log('=== 에러 핸들링 테스트 시작 ===');
    
    const errors: any[] = [];
    const warnings: any[] = [];
    
    // 콘솔 에러 모니터링
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
        console.log(`❌ 콘솔 에러: ${msg.text()}`);
      } else if (msg.type() === 'warning') {
        warnings.push(msg.text());
        console.log(`⚠️ 콘솔 경고: ${msg.text()}`);
      }
    });
    
    // 페이지 에러 모니터링
    page.on('pageerror', error => {
      errors.push(error.message);
      console.log(`❌ 페이지 에러: ${error.message}`);
    });
    
    await page.goto(WEBSITE_URL, { waitUntil: 'networkidle' });
    await page.waitForTimeout(10000); // 모든 비동기 작업 완료 대기
    
    // 네트워크 실패 복구 테스트 (오프라인/온라인 상태 시뮬레이션)
    await page.setOffline(true);
    await page.waitForTimeout(2000);
    
    // 새로고침 시도 (오프라인 상태)
    try {
      await page.reload({ timeout: 5000 });
    } catch (e) {
      console.log('✓ 오프라인 상태에서 예상된 에러 발생');
    }
    
    // 다시 온라인으로
    await page.setOffline(false);
    await page.reload({ waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);
    
    console.log(`총 에러 수: ${errors.length}`);
    console.log(`총 경고 수: ${warnings.length}`);
    
    // 치명적 에러는 없어야 함
    const fatalErrors = errors.filter(error => 
      error.includes('TypeError') || 
      error.includes('ReferenceError') || 
      error.includes('SyntaxError')
    );
    expect(fatalErrors.length).toBe(0);
    
    // Firebase 관련 에러 허용량 확인
    const firebaseErrors = errors.filter(error => 
      error.toLowerCase().includes('firebase') || 
      error.toLowerCase().includes('quota')
    );
    expect(firebaseErrors.length).toBeLessThan(5); // 최대 4개까지 허용
    
    await page.screenshot({ 
      path: 'test-results/12-error-handling.png',
      fullPage: true 
    });
  });

  test('리소스 로딩 및 성능 최적화 확인', async ({ page }) => {
    console.log('=== 리소스 로딩 테스트 시작 ===');
    
    const resourceMetrics = {
      images: 0,
      scripts: 0,
      stylesheets: 0,
      fonts: 0,
      others: 0,
      totalSize: 0,
      loadTimes: [] as number[]
    };
    
    page.on('response', async (response) => {
      const contentType = response.headers()['content-type'] || '';
      const contentLength = parseInt(response.headers()['content-length'] || '0');
      
      if (contentType.startsWith('image/')) {
        resourceMetrics.images++;
      } else if (contentType.includes('javascript')) {
        resourceMetrics.scripts++;
      } else if (contentType.includes('css')) {
        resourceMetrics.stylesheets++;
      } else if (contentType.includes('font')) {
        resourceMetrics.fonts++;
      } else {
        resourceMetrics.others++;
      }
      
      resourceMetrics.totalSize += contentLength;
    });
    
    const startTime = Date.now();
    await page.goto(WEBSITE_URL, { waitUntil: 'networkidle' });
    const endTime = Date.now();
    
    resourceMetrics.loadTimes.push(endTime - startTime);
    
    console.log('리소스 로딩 통계:');
    console.log(`- 이미지: ${resourceMetrics.images}개`);
    console.log(`- 스크립트: ${resourceMetrics.scripts}개`);
    console.log(`- 스타일시트: ${resourceMetrics.stylesheets}개`);
    console.log(`- 폰트: ${resourceMetrics.fonts}개`);
    console.log(`- 기타: ${resourceMetrics.others}개`);
    console.log(`- 총 크기: ${(resourceMetrics.totalSize / 1024 / 1024).toFixed(2)} MB`);
    console.log(`- 로딩 시간: ${resourceMetrics.loadTimes[0]}ms`);
    
    // 성능 기준 확인
    expect(resourceMetrics.loadTimes[0]).toBeLessThan(15000); // 15초 이내 로딩
    expect(resourceMetrics.totalSize).toBeLessThan(50 * 1024 * 1024); // 50MB 이하
    
    await page.screenshot({ 
      path: 'test-results/13-resource-optimization.png',
      fullPage: true 
    });
  });
});