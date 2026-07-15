import { test, expect, Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

type EvidenceResult = {
  name: string;
  status: 'passed';
  details: string;
};

const evidence: EvidenceResult[] = [];

function record(name: string, details: string) {
  evidence.push({ name, status: 'passed', details });
}

function jsonResponse(payload: unknown, status = 200) {
  return {
    status,
    contentType: 'application/json',
    body: JSON.stringify(payload),
  };
}

async function mockApi(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');

    if (path === '/auth/check' || path === '/auth/desktop/auto-login') {
      return route.fulfill(jsonResponse({
        authenticated: true,
        user: { id: 1, username: 'local-user', email: 'local@example.test', role: 'admin' },
      }));
    }

    if (path === '/auth/desktop/challenge') return route.fulfill(jsonResponse({ nonce: 'keyboard-evidence-nonce' }));
    if (path === '/gateway/sessions') return route.fulfill(jsonResponse({ sessions: [] }));
    if (path === '/gateway/providers') {
      return route.fulfill(jsonResponse({
        providers: [{ id: 'provider-openai', name: 'OpenAI', type: 'openai', model: 'gpt-5.5', is_default: true }],
      }));
    }
    if (path === '/settings/ai') return route.fulfill(jsonResponse({ ai_processing_enabled: true, store_chat_history: true }));
    if (path === '/analytics/activity') return route.fulfill(jsonResponse([]));
    if (path === '/analytics/summary' || path === '/analytics/overview') return route.fulfill(jsonResponse({}));
    if (path === '/analytics/mcp') return route.fulfill(jsonResponse({ servers: 0, tools: 0, resources: 0 }));
    if (path === '/pillars' || path === '/nodes' || path === '/edges') return route.fulfill(jsonResponse([]));
    if (path === '/simulations') return route.fulfill(jsonResponse([]));
    if (path.startsWith('/trace/runs')) return route.fulfill(jsonResponse({ runs: [] }));
    if (path === '/mcp/servers') return route.fulfill(jsonResponse({ servers: [], runtime_servers: [] }));
    if (path === '/mcp/stats') {
      return route.fulfill(jsonResponse({
        stats: {
          total_servers: 0,
          active_servers: 0,
          total_resources: 0,
          total_tools: 0,
          active_connections: 0,
        },
      }));
    }
    if (path === '/user/data/summary') {
      return route.fulfill(jsonResponse({
        user_id: 1,
        username: 'local-user',
        data_summary: { total_simulations: 0, simulations_by_status: {} },
        available_actions: [
          { action: 'export', endpoint: '/api/v1/user/data/export', method: 'GET' },
          { action: 'delete', endpoint: '/api/v1/user/data/delete', method: 'POST' },
        ],
      }));
    }
    if (path === '/user/notifications') {
      return route.fulfill(jsonResponse({
        success: true,
        preferences: {
          email_on_run_complete: true,
          email_on_run_failed: true,
          email_on_simulation_complete: false,
          inapp_run_complete: true,
          inapp_run_failed: true,
          inapp_simulation_complete: true,
          inapp_system_alerts: true,
          digest_frequency: 'none',
        },
      }));
    }
    if (path === '/storage/health') {
      const service = { healthy: true, is_cloud: false, url: 'local' };
      return route.fulfill(jsonResponse({
        mode: 'local',
        services: { postgres: service, redis: service, neo4j: service, vector: service, object: service },
      }));
    }
    if (path === '/storage/databases/autostart') return route.fulfill(jsonResponse({ enabled: true }));
    if (path === '/storage/cloud-config') return route.fulfill(jsonResponse({ success: true, cloud_config: {} }));
    if (path === '/gateway/offline-queue') {
      return route.fulfill(jsonResponse({ items: [], counts: {}, snapshot_at: '2026-07-14T10:01:00Z' }));
    }

    return route.fulfill(jsonResponse({ success: true }));
  });
}

async function focusAndActivate(page: Page, locator: ReturnType<Page['getByRole']>, key = 'Enter') {
  await locator.focus();
  await expect(locator).toBeFocused();
  await page.keyboard.press(key);
}

test.afterAll(async () => {
  const reportPath = resolve(__dirname, '..', '..', '..', 'reports', 'app-readiness', 'keyboard-navigation-report.json');
  mkdirSync(resolve(reportPath, '..'), { recursive: true });
  writeFileSync(
    reportPath,
    `${JSON.stringify({ generated_at: new Date().toISOString(), evidence }, null, 2)}\n`,
    'utf8',
  );
});

test.describe('Keyboard navigation evidence', () => {
  test.beforeEach(async ({ page }) => {
    await mockApi(page);
  });

  test('global sidebar collapse and dashboard primary action work from keyboard', async ({ page }) => {
    await page.goto('/dashboard', { waitUntil: 'domcontentloaded' });

    const collapse = page.getByRole('button', { name: /collapse sidebar/i });
    await focusAndActivate(page, collapse);
    await expect(page.getByRole('button', { name: /expand sidebar/i })).toBeVisible();

    const expand = page.getByRole('button', { name: /expand sidebar/i });
    await focusAndActivate(page, expand, 'Space');
    await expect(page.getByRole('button', { name: /collapse sidebar/i })).toBeVisible();

    const startSession = page.getByRole('button', { name: /start new session/i });
    await focusAndActivate(page, startSession);
    await expect(page).toHaveURL(/\/chat$/);
    await expect(page.getByTestId('main-chat-area')).toBeVisible();
    record('global keyboard navigation', 'Sidebar collapse/expand and dashboard Start New Session are keyboard-operable.');
  });

  test('settings sidebar tabs and privacy link are keyboard-operable', async ({ page }) => {
    await page.goto('/settings', { waitUntil: 'domcontentloaded' });

    const storage = page.getByRole('tab', { name: /^storage$/i });
    await focusAndActivate(page, storage);
    await expect(page.getByRole('heading', { name: /internal data plane/i })).toBeVisible();

    const aiModels = page.getByRole('tab', { name: /ai models/i });
    await focusAndActivate(page, aiModels);
    await expect(page.getByRole('heading', { name: /ai model controls/i })).toBeVisible();

    const security = page.getByRole('tab', { name: /^security$/i });
    await focusAndActivate(page, security);
    const privacyLink = page.getByRole('link', { name: /open privacy controls/i });
    await focusAndActivate(page, privacyLink);
    await expect(page).toHaveURL(/\/settings\/privacy$/);
    await expect(page.getByRole('heading', { name: /privacy & data management/i })).toBeVisible();
    record('settings keyboard navigation', 'Settings sections and privacy controls link are reachable and operable by keyboard.');
  });

  test('privacy export action is keyboard-operable and preserves visible feedback', async ({ page }) => {
    let exportRequested = false;
    await page.route('**/api/v1/user/data/export', async (route) => {
      exportRequested = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        headers: { 'Content-Disposition': 'attachment; filename=ukg_data_export_local-user.json' },
        body: JSON.stringify({ version: '1.0', profile: { username: 'local-user' }, simulations: [] }),
      });
    });

    await page.goto('/settings/privacy', { waitUntil: 'domcontentloaded' });
    const exportButton = page.getByRole('button', { name: /export my data/i });
    await focusAndActivate(page, exportButton);
    await expect.poll(() => exportRequested).toBe(true);
    await expect(page.getByText(/data export started successfully/i)).toBeVisible();
    record('privacy keyboard action', 'Export My Data is keyboard-operable and shows success feedback.');
  });
});
