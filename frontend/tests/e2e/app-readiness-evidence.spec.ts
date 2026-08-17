import { test, expect, Page } from '@playwright/test';
import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

type EvidenceResult = {
  name: string;
  status: 'passed' | 'failed';
  details: string;
};

const evidence: EvidenceResult[] = [];

function record(name: string, details: string) {
  evidence.push({ name, status: 'passed', details });
}

function jsonResponse(payload: unknown, status = 200, headers: Record<string, string> = {}) {
  return {
    status,
    contentType: 'application/json',
    headers,
    body: JSON.stringify(payload),
  };
}

async function mockBaseApi(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');

    if (path === '/auth/check' || path === '/auth/desktop/auto-login') {
      return route.fulfill(jsonResponse({
        authenticated: true,
        user: { id: 1, username: 'local-user', email: 'local@example.test', role: 'admin' },
      }));
    }

    if (path === '/auth/desktop/challenge') {
      return route.fulfill(jsonResponse({ nonce: 'app-readiness-nonce' }));
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

    if (path === '/gateway/providers') {
      return route.fulfill(jsonResponse({
        providers: [{ id: 'provider-openai', name: 'OpenAI', type: 'openai', model: 'gpt-5.6-sol', is_default: true }],
      }));
    }

    if (path === '/settings/ai') {
      return route.fulfill(jsonResponse({ ai_processing_enabled: true, store_chat_history: true }));
    }

    if (path === '/storage/health') {
      const service = { healthy: true, is_cloud: false, url: 'local' };
      return route.fulfill(jsonResponse({
        mode: 'local',
        services: {
          postgres: service,
          redis: service,
          neo4j: service,
          vector: service,
          object: service,
        },
      }));
    }

    if (path === '/storage/databases/autostart') {
      return route.fulfill(jsonResponse({ enabled: true }));
    }

    if (path === '/storage/cloud-config') {
      return route.fulfill(jsonResponse({ success: true, cloud_config: {} }));
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

    if (path === '/gateway/sessions') return route.fulfill(jsonResponse({ sessions: [] }));
    if (path === '/gateway/offline-queue') {
      return route.fulfill(jsonResponse({
        items: [{
          id: 'queue-e2e-12345678',
          status: 'pending',
          failure_class: 'network',
          created_at: '2026-07-14T10:00:00Z',
          expires_at: '2026-07-17T10:00:00Z',
          attempts: 0,
          payload_bytes: 128,
          encrypted: true,
        }],
        counts: { pending: 1 },
        snapshot_at: '2026-07-14T10:01:00Z',
      }));
    }
    if (path === '/pillars' || path === '/nodes' || path === '/edges') return route.fulfill(jsonResponse([]));
    if (path.startsWith('/trace/runs')) return route.fulfill(jsonResponse({ runs: [] }));
    if (path === '/simulations') return route.fulfill(jsonResponse([]));

    return route.fulfill(jsonResponse({ success: true }));
  });
}

test.afterAll(async () => {
  const reportPath = resolve(__dirname, '..', '..', '..', 'reports', 'app-readiness', 'playwright-app-readiness-report.json');
  mkdirSync(resolve(reportPath, '..'), { recursive: true });
  writeFileSync(
    reportPath,
    `${JSON.stringify({ generated_at: new Date().toISOString(), evidence }, null, 2)}\n`,
    'utf8',
  );
});

test.describe('Application readiness evidence', () => {
  test.beforeEach(async ({ page }) => {
    await mockBaseApi(page);
  });

  test('privacy export completes as a user-visible download', async ({ page }) => {
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
    await expect(page.getByRole('button', { name: /export my data/i })).toBeVisible();

    await page.getByRole('button', { name: /export my data/i }).click();
    await expect.poll(() => exportRequested).toBe(true);
    await expect(page.getByText(/data export started successfully/i)).toBeVisible();
    record('data export flow', 'Privacy page starts a JSON export download and shows success feedback.');
  });

  test('privacy export rate-limit failure is surfaced to the user', async ({ page }) => {
    await page.route('**/api/v1/user/data/export', async (route) => {
      await route.fulfill(jsonResponse({ error: 'Rate limit exceeded' }, 429));
    });

    await page.goto('/settings/privacy', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: /export my data/i })).toBeVisible();
    await page.getByRole('button', { name: /export my data/i }).click();

    await expect(page.getByText(/failed to export data/i)).toBeVisible();
    record('rate-limit UX', '429 response from data export endpoint leaves the user on-page with visible error feedback.');
  });

  test('profile deletion requires confirmation and calls the destructive endpoint', async ({ page }) => {
    let deleteBody = '';
    await page.route('**/api/v1/user/data/delete', async (route) => {
      deleteBody = route.request().postData() || '';
      await route.fulfill(jsonResponse({
        success: true,
        data: { deleted_user_id: 1, simulations_deleted: 0 },
        message: 'Your profile and associated data have been permanently deleted.',
      }));
    });

    await page.goto('/settings/privacy', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: /delete my account/i })).toBeVisible();
    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toMatch(/permanently delete/i);
      await dialog.accept();
    });
    await page.getByRole('button', { name: /delete my account/i }).click();

    await expect.poll(() => deleteBody).toContain('"confirm":"DELETE"');
    record('data deletion flow', 'Delete action opens browser confirmation and posts confirm=DELETE to the profile deletion endpoint.');
  });

  test('cloud outage is reported on storage settings without route failure', async ({ page }) => {
    await page.route('**/api/v1/storage/health', async (route) => {
      await route.fulfill(jsonResponse({ success: false, error: 'Storage backend unavailable' }, 503));
    });

    await page.goto('/settings', { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: /^storage$/i }).click();

    await expect(page.getByText(/failed to fetch storage health/i).first()).toBeVisible();
    await expect(page.getByRole('heading', { name: /page not found/i })).toHaveCount(0);
    record('cloud outage UX', 'Storage health failure displays an error while preserving the settings route.');
  });

  test('AI provider failure is visible during model test', async ({ page }) => {
    await page.route('**/api/v1/gateway/providers/provider-openai/test', async (route) => {
      await route.fulfill(jsonResponse({ success: false, error: 'Provider unavailable' }, 503));
    });

    await page.goto('/settings', { waitUntil: 'domcontentloaded' });
    await page.getByRole('tab', { name: /ai models/i }).click();
    await page.getByRole('button', { name: /test provider model/i }).click();

    await expect(page.getByText(/provider model test failed/i)).toBeVisible();
    record('AI provider failure UX', 'Provider test failure is surfaced in the AI model settings UI.');
  });

  test('auth failure on privacy export is visible without losing page state', async ({ page }) => {
    await page.route('**/api/v1/user/data/export', async (route) => {
      await route.fulfill(jsonResponse({ error: 'Session expired' }, 401));
    });

    await page.goto('/settings/privacy', { waitUntil: 'domcontentloaded' });
    await expect(page.getByRole('button', { name: /export my data/i })).toBeVisible();
    await page.getByRole('button', { name: /export my data/i }).click();

    await expect(page.getByText(/failed to export data/i)).toBeVisible();
    await expect(page.getByRole('heading', { name: /privacy & data management/i })).toBeVisible();
    record('auth failure E2E', '401 response from export endpoint leaves the privacy page stable with visible error feedback.');
  });

  test('offline queue metadata can be reviewed, exported, and replayed through policy', async ({ page }) => {
    let replayRequested = false;
    await page.route('**/api/v1/gateway/offline-queue/replay', async (route) => {
      replayRequested = true;
      await route.fulfill(jsonResponse({
        replayed: 1,
        results: [{ id: 'queue-e2e-12345678', status: 'completed' }],
        queue: {
          items: [],
          counts: { completed: 1 },
          snapshot_at: '2026-07-14T10:02:00Z',
        },
      }));
    });

    await page.goto('/chat', { waitUntil: 'domcontentloaded' });
    await page.getByRole('button', { name: /review offline replay queue, 1 pending/i }).click();
    await expect(page.getByText(/queue-e2e-12345678/i)).toBeVisible();
    await expect(page.getByText(/encrypted payload/i)).toBeVisible();

    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: /export redacted metadata/i }).click();
    const download = await downloadPromise;
    expect(download.suggestedFilename()).toMatch(/^datalogic-offline-queue-.*\.json$/);

    page.once('dialog', async (dialog) => {
      expect(dialog.message()).toMatch(/current policy and budget checks/i);
      await dialog.accept();
    });
    await page.getByRole('button', { name: /replay pending/i }).click();
    await expect.poll(() => replayRequested).toBe(true);
    await expect(page.getByText(/offline replay queue is empty/i)).toBeVisible();
    record('offline replay queue', 'Redacted queue metadata is reviewable and exportable; replay invokes the policy-enforced backend lifecycle.');
  });
});
