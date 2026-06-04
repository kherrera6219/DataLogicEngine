import { defineConfig, devices } from '@playwright/test';

const VISUAL_PORT = process.env.PLAYWRIGHT_VISUAL_PORT ?? '3102';
const BASE_URL = `http://127.0.0.1:${VISUAL_PORT}`;

export default defineConfig({
  testDir: './tests/e2e',
  testMatch: ['**/*.spec.ts'],
  testIgnore: ['**/electron-route-sidebar-smoke.spec.ts'],
  timeout: 90 * 1000,
  expect: {
    timeout: 15 * 1000,
  },
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report-visual' }],
  ],
  use: {
    baseURL: BASE_URL,
    actionTimeout: 0,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
    extraHTTPHeaders: {
      'x-datalogic-desktop': '1',
    },
  },
  webServer: {
    command: `npm run dev -- --hostname 127.0.0.1 --port ${VISUAL_PORT}`,
    url: BASE_URL,
    timeout: 180 * 1000,
    reuseExistingServer: !process.env.CI,
  },
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        channel: process.env.CI ? 'chrome' : undefined,
        viewport: { width: 1440, height: 900 },
      },
    },
  ],
});
