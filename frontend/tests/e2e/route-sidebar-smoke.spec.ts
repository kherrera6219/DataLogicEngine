import { test, expect } from '@playwright/test';

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

const CRITICAL_ROUTE_ORDER = [
  '/dashboard',
  '/settings',
  '/projects',
  '/projects/view?id=smoke-session',
  '/settings/privacy',
  '/admin/mcp/servers',
];

const STATIC_ROUTES = [
  '/',
  '/about',
  '/about/ai-limitations',
  '/about/cloud-services',
  '/admin/compliance',
  '/admin/mcp',
  '/admin/mcp/servers',
  '/algorithms',
  '/analytics',
  '/chat',
  '/dashboard',
  '/graph',
  '/knowledge',
  '/legal/privacy',
  '/login',
  '/mcp',
  '/profile',
  '/projects',
  '/projects/view?id=smoke-session',
  '/register',
  '/runs',
  '/runs/view?trace=smoke',
  '/settings',
  '/settings/privacy',
  '/simulations',
  '/truth-engine',
];

test.describe('Route And Sidebar Smoke', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page);
  });

  async function assertNoNotFound(page: import('@playwright/test').Page) {
    await expect(page.getByRole('heading', { name: 'Page Not Found' })).toHaveCount(0);
  }

  test('critical route flow works in order', async ({ page }) => {
    for (const route of CRITICAL_ROUTE_ORDER) {
      await test.step(`navigate to ${route}`, async () => {
        const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
        expect(response).not.toBeNull();
        expect(response!.status()).toBeLessThan(400);
        await page.waitForLoadState('networkidle');
        await assertNoNotFound(page);
      });
    }
  });

  test('all static routes avoid not-found', async ({ page }) => {
    for (const route of STATIC_ROUTES) {
      await test.step(`check ${route}`, async () => {
        const response = await page.goto(route, { waitUntil: 'domcontentloaded' });
        expect(response).not.toBeNull();
        expect(response!.status()).toBeLessThan(400);
        await page.waitForLoadState('networkidle');
        await assertNoNotFound(page);
      });
    }
  });

  test('global sidebar toggle collapses and expands', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    const toggle = page.getByTestId('app-sidebar-toggle');
    await expect(toggle).toBeVisible();
    await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

    await toggle.click();
    await expect(page.getByRole('button', { name: /expand sidebar/i })).toBeVisible();

    await toggle.click();
    await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();
  });

  test('settings sidebar toggle collapses and expands', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    const toggle = page.getByTestId('settings-sidebar-toggle');
    await expect(toggle).toBeVisible();
    await expect(toggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);

    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-label', /expand settings sidebar/i);

    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);
  });

  test('dashboard quick upload navigates to chat upload intent', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle');

    await page.getByRole('button', { name: /quick upload/i }).click();
    await expect(page).toHaveURL(/\/chat\?intent=upload/);
    await assertNoNotFound(page);
  });
});
