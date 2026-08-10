import { _electron as electron, expect, test, ElectronApplication, Page } from '@playwright/test';
import * as path from 'path';
import { installSourceApiMocks } from './support/mock-source-api';

const BASE_URL = 'http://localhost:3000';

const CRITICAL_ROUTE_ORDER = [
  '/dashboard',
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
  await page.setViewportSize({ width: 1440, height: 900 });
  page.setDefaultNavigationTimeout(10_000);
  page.setDefaultTimeout(10_000);
  await installSourceApiMocks(page);
  return { app, page };
}

async function assertNoNotFound(page: Page) {
  await expect(page.getByRole('heading', { name: 'Page Not Found' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Module Error' })).toHaveCount(0);
}

test.describe('Electron Route And Sidebar Smoke', () => {
  test('critical routes, sidebars, and quick upload work in one desktop lifecycle', async () => {
    test.setTimeout(120_000);
    const { app, page } = await launchDesktopApp();
    try {
      for (const route of CRITICAL_ROUTE_ORDER) {
        await test.step(`navigate to ${route}`, async () => {
          const response = await page.goto(`${BASE_URL}${route}`, { waitUntil: 'domcontentloaded' });
          expect(response).not.toBeNull();
          expect(response!.status()).toBeLessThan(400);
          await assertNoNotFound(page);
        });
      }

      await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });

      const appSidebarToggle = page.getByTestId('app-sidebar-toggle');
      await expect(appSidebarToggle).toBeVisible();
      await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

      await appSidebarToggle.click();
      await expect(page.getByRole('button', { name: /expand sidebar/i })).toBeVisible();

      await appSidebarToggle.click();
      await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

      await page.goto(`${BASE_URL}/settings`, { waitUntil: 'domcontentloaded' });

      const settingsSidebarToggle = page.getByTestId('settings-sidebar-toggle');
      await expect(settingsSidebarToggle).toBeVisible();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);

      await settingsSidebarToggle.click();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /expand settings sidebar/i);

      await settingsSidebarToggle.click();
      await expect(settingsSidebarToggle).toHaveAttribute('aria-label', /collapse settings sidebar/i);

      await page.goto(`${BASE_URL}/dashboard`, { waitUntil: 'domcontentloaded' });
      await page.getByRole('button', { name: /quick upload/i }).click();
      await expect(page).toHaveURL(/\/chat\?intent=upload/);
      await assertNoNotFound(page);
    } finally {
      await app.close();
    }
  });
});
