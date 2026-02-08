import { _electron as electron, expect, test, ElectronApplication, Page } from '@playwright/test';
import * as path from 'path';

const BASE_URL = 'http://localhost:3000';

const CRITICAL_ROUTE_ORDER = [
  '/dashboard',
  '/admin',
  '/settings',
  '/projects',
  '/projects/view?id=smoke-session',
  '/settings/privacy',
  '/admin/mcp/servers',
];

async function launchDesktopApp(): Promise<{ app: ElectronApplication; page: Page }> {
  const mainPath = path.join(__dirname, '../../dist-electron/main.js');
  const app = await electron.launch({
    args: [mainPath],
  });
  const pickMainWindow = (windows: Page[]) =>
    windows.find((candidate) => !candidate.url().startsWith('devtools://'));

  let page = pickMainWindow(app.windows());
  if (!page) {
    while (!page) {
      const candidate = await app.waitForEvent('window');
      if (!candidate.url().startsWith('devtools://')) {
        page = candidate;
      }
    }
  }

  await page.waitForLoadState('domcontentloaded');
  return { app, page };
}

async function assertNoNotFound(page: Page) {
  await expect(page.getByRole('heading', { name: 'Page Not Found' })).toHaveCount(0);
}

test.describe('Electron Route And Sidebar Smoke', () => {
  test('critical routes work in order', async () => {
    const { app, page } = await launchDesktopApp();
    try {
      for (const route of CRITICAL_ROUTE_ORDER) {
        await test.step(`navigate to ${route}`, async () => {
          const response = await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded' });
          expect(response).not.toBeNull();
          expect(response!.status()).toBeLessThan(400);
          await page.waitForLoadState('networkidle');
          await assertNoNotFound(page);
        });
      }
    } finally {
      await app.close();
    }
  });

  test('sidebar toggles collapse and expand', async () => {
    const { app, page } = await launchDesktopApp();
    try {
      await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle');

      const appSidebarToggle = page.getByTestId('app-sidebar-toggle');
      await expect(appSidebarToggle).toBeVisible();
      await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

      await appSidebarToggle.click();
      await expect(page.getByRole('button', { name: /expand sidebar/i })).toBeVisible();

      await appSidebarToggle.click();
      await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

      await page.goto(`${BASE_URL}/settings`, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle');

      const settingsSidebarToggle = page.getByTestId('settings-sidebar-toggle');
      await expect(settingsSidebarToggle).toBeVisible();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);

      await settingsSidebarToggle.click();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /expand settings sidebar/i);

      await settingsSidebarToggle.click();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);
    } finally {
      await app.close();
    }
  });

  test('dashboard quick upload navigates to chat upload intent', async () => {
    const { app, page } = await launchDesktopApp();
    try {
      await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('networkidle');
      await page.getByRole('button', { name: /quick upload/i }).click();
      await expect(page).toHaveURL(/\/chat\?intent=upload/);
      await assertNoNotFound(page);
    } finally {
      await app.close();
    }
  });
});
