import { test, expect } from '@playwright/test';

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

async function mockApi(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');
    let payload: unknown = {};

    if (path === '/auth/check' || path === '/auth/desktop/auto-login') {
      payload = {
        authenticated: true,
        user: { id: 1, username: 'local-user', email: 'local@example.test' },
      };
    } else if (path === '/auth/desktop/challenge') {
      payload = { nonce: 'visual-smoke-nonce' };
    } else if (path === '/gateway/sessions') {
      payload = { sessions: [] };
    } else if (path === '/ukg/pillars') {
      payload = [];
    } else if (path === '/ukg/nodes') {
      payload = [];
    } else if (path === '/ukg/edges') {
      payload = [];
    } else if (path === '/simulations') {
      payload = [];
    } else if (path.startsWith('/trace/runs')) {
      payload = { runs: [] };
    } else if (path === '/analytics/activity') {
      payload = [];
    } else if (path === '/analytics/summary' || path === '/analytics/overview') {
      payload = {};
    } else if (path === '/analytics/mcp') {
      payload = { servers: 0, tools: 0, resources: 0 };
    } else if (path === '/mcp/servers') {
      payload = { servers: [], runtime_servers: [] };
    } else if (path === '/mcp/stats') {
      payload = {
        stats: {
          total_servers: 0,
          active_servers: 0,
          total_resources: 0,
          total_tools: 0,
          active_connections: 0,
        },
      };
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(payload),
    });
  });
}

function sanitizeRoute(route: string): string {
  if (route === '/') return 'home';
  return route.replace(/^\//, '').replace(/[/?=&]/g, '-');
}

test.describe('Theme Visual Smoke', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page);

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
