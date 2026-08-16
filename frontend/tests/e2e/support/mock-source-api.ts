import type { Page } from '@playwright/test';

export async function installSourceApiMocks(page: Page) {
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');
    let payload: unknown = {};

    if (path === '/auth/check' || path === '/auth/desktop/auto-login') {
      payload = {
        authenticated: true,
        user: { id: 1, username: 'local-user', email: 'local@example.test', role: 'admin', is_admin: true },
      };
    } else if (path === '/auth/desktop/challenge') {
      payload = { nonce: 'source-smoke-nonce' };
    } else if (path === '/health') {
      payload = { status: 'ok' };
    } else if (path === '/feature-flags') {
      payload = { flags: {} };
    } else if (path === '/gateway/sessions') {
      payload = { sessions: [] };
    } else if (path === '/knowledge/pillar-levels' || path === '/pillar-levels' || path === '/nodes' || path === '/edges' || path === '/simulations') {
      payload = [];
    } else if (path.startsWith('/trace/runs')) {
      payload = { runs: [] };
    } else if (path === '/analytics/activity') {
      payload = [];
    } else if (path === '/analytics/summary' || path === '/analytics/overview') {
      payload = {};
    } else if (path === '/analytics/mcp') {
      payload = { servers: 0, tools: 0, resources: 0 };
    } else if (path === '/user/data/summary') {
      payload = { user_id: 1, username: 'local-user', data_summary: {}, available_actions: [] };
    } else if (path === '/system/diagnostics/summary') {
      payload = {
        schema_version: 'dle.diagnostics.v1',
        status: 'ok',
        runtime: { phase: 'ready', ready: true, services: {} },
        requests: { total: 12, inflight: 1, uptime_seconds: 60 },
        logging: { schema_version: 'dle.log.v1', format: 'json', redaction: 'best_effort_redacted' },
        external_telemetry: { opted_in: false, enabled: false, provider: 'none', state_code: null },
        support_bundle: {
          schema_version: 'dle.support-bundle.v1',
          content_policy: 'redacted_diagnostics_only',
          user_content_included: false,
          generic_reports_included: false,
          preview_required: true,
          encryption_available_via_cli: true,
        },
        correlation_id: 'source-smoke-diagnostics',
        timestamp: new Date().toISOString(),
      };
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
