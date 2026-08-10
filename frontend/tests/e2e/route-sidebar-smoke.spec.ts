import { test, expect } from '@playwright/test';
import { installSourceApiMocks } from './support/mock-source-api';

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
  '/admin/diagnostics',
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
    await installSourceApiMocks(page);
  });

  async function assertNoNotFound(page: import('@playwright/test').Page) {
    await expect(page.getByRole('heading', { name: 'Page Not Found' })).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Module Error' })).toHaveCount(0);
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
