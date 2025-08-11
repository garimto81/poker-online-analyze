import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright 설정
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests',
  /* 병렬 테스트 실행 */
  fullyParallel: true,
  /* CI에서 실패시 재시도 안함 */
  forbidOnly: !!process.env.CI,
  /* CI에서만 재시도 */
  retries: process.env.CI ? 2 : 0,
  /* 병렬 워커 수 */
  workers: process.env.CI ? 1 : undefined,
  /* 테스트 결과 리포터 */
  reporter: 'html',
  /* 모든 테스트에 공통 설정 */
  use: {
    /* 실패시 스크린샷 캡처 */
    screenshot: 'only-on-failure',
    /* 실패시 비디오 녹화 */
    video: 'retain-on-failure',
    /* 추적 수집 (디버깅용) */
    trace: 'on-first-retry',
  },

  /* 다양한 브라우저 및 디바이스에서 테스트 */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* 모바일 테스트 */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },

    /* 태블릿 테스트 */
    {
      name: 'Tablet iPad',
      use: { ...devices['iPad Pro'] },
    },
  ],

  /* 로컬 개발 서버 설정 (필요시) */
  // webServer: {
  //   command: 'npm run start',
  //   url: 'http://127.0.0.1:3000',
  //   reuseExistingServer: !process.env.CI,
  // },
});