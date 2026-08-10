import { test, expect } from '@playwright/test';
import { installSourceApiMocks } from './support/mock-source-api';

type ThemeMode = 'dark' | 'light';

const THEMES: ThemeMode[] = ['dark', 'light'];
const ROUTES = [
  '/',
  '/about',
  '/dashboard',
  '/chat',
  '/projects',
  '/settings',
  '/simulations',
  '/mcp',
];

function sanitizeRoute(route: string): string {
  if (route === '/') return 'home';
  return route.replace(/^\//, '').replace(/[/?=&]/g, '-');
}

test.describe('Theme Visual Smoke', () => {
  test.beforeEach(async ({ page }) => {
    await installSourceApiMocks(page);

    // Reduce animation noise so screenshots are deterministic enough for smoke checks.
    await page.addInitScript(() => {
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
          scroll-behavior: auto !important;
        }
      `;
      document.head.appendChild(style);
    });
  });

  for (const theme of THEMES) {
    for (const route of ROUTES) {
      test(`renders ${route} in ${theme} mode`, async ({ page }) => {
        await page.addInitScript((selectedTheme: ThemeMode) => {
          window.localStorage.setItem('theme', selectedTheme);
        }, theme);

        const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
        expect(response).not.toBeNull();
        expect(response?.status(), `Unexpected HTTP status for ${route}`).toBeLessThan(400);

        await page.waitForLoadState('networkidle');
        await expect
          .poll(async () => page.evaluate((selectedTheme) => document.documentElement.classList.contains(selectedTheme), theme))
          .toBe(true);

        await expect(page.locator('body')).toBeVisible();
        expect(page.url()).not.toContain('/login');

        const fileName = `${sanitizeRoute(route)}-${theme}.png`;
        await expect(page).toHaveScreenshot(fileName, {
          fullPage: true,
          maxDiffPixelRatio: 0.01,
        });
      });
    }
  }
});
