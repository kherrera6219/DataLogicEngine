import { _electron as electron, test, expect, ElectronApplication, Page } from '@playwright/test';
import * as path from 'path';
import * as fs from 'fs';

const AUDIT_DIR = 'C:/ProgramData/DataLogicEngine/audit/visual_checks';

test.describe('UKG Desktop Visual Audit', () => {
  let electronApp: ElectronApplication;
  let page: Page;

  test.beforeAll(async () => {
    // Ensure audit directory exists
    if (!fs.existsSync(AUDIT_DIR)) {
      fs.mkdirSync(AUDIT_DIR, { recursive: true });
    }

    // Launch Electron App
    const mainPath = path.join(__dirname, '../dist-electron/main.js');
    electronApp = await electron.launch({
      args: [mainPath],
      executablePath: process.env.ELECTRON_PATH, // Option to provide path to built EXE
    });

    page = await electronApp.firstWindow();
    
    // Capture crashes or errors
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    page.on('crash', (p: any) => console.error('PAGE CRASHED!', p.url()));
    page.on('pageerror', (err: Error) => console.error('BROWSER ERROR:', err.message));
  });

  test.afterAll(async () => {
    await electronApp.close();
  });

  async function takeScreenshot(name: string) {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const screenshotPath = path.join(AUDIT_DIR, `${name}_${timestamp}.png`);
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log(`Captured: ${screenshotPath}`);
  }

  test('01_Startup_And_Loading', async () => {
    // Wait for the initializer or landing page
    await page.waitForLoadState('networkidle');
    await takeScreenshot('01_Startup_First_Load');
    
    // Check if Initializer is visible or if we've already redirected
    const isInitializing = await page.locator('text=Initializing DataLogicEngine').isVisible();
    if (isInitializing) {
        console.log('App is in Initializing state...');
        await takeScreenshot('01_Startup_Initializing');
        // Wait for dashboard or login
        await page.waitForURL((url: URL) => url.toString().includes('/dashboard') || url.toString().includes('/login'), { timeout: 30000 });
    }
  });

  test('02_Dashboard_Verification', async () => {
    await page.goto('http://localhost:3000/dashboard');
    await page.waitForLoadState('networkidle');
    // Ensure mica/acrylic elements or specific cards are present
    await expect(page.locator('h1')).toContainText('Dashboard');
    await takeScreenshot('02_Dashboard_Main');
  });

  test('03_Chat_Interface_Verification', async () => {
    await page.goto('http://localhost:3000/chat');
    await page.waitForLoadState('networkidle');
    await expect(page.locator('textarea')).toBeVisible();
    await takeScreenshot('03_Chat_Interface');
  });

  test('04_Graph_Explorer_Verification', async () => {
    await page.goto('http://localhost:3000/graph');
    // Wait for 3D canvas
    await page.waitForSelector('canvas', { timeout: 20000 });
    await takeScreenshot('04_Graph_3D_Explorer');
  });

  test('05_Settings_And_Admin_Verification', async () => {
    // Admin user dashboard was removed under single-mode; the compliance page is
    // the remaining admin surface (auth-deprecation Phase E).
    const routes = ['/settings', '/admin/compliance'];
    for (const route of routes) {
      await page.goto(`http://localhost:3000${route}`);
      await page.waitForLoadState('networkidle');
      await takeScreenshot(`05_UI_${route.replace(/\//g, '_')}`);
    }
  });
});
