#!/usr/bin/env node

import { chromium } from 'playwright';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, '..', '..');
const frontendRoot = resolve(__dirname, '..');
const axeSourcePath = join(frontendRoot, 'node_modules', 'axe-core', 'axe.min.js');

const defaultRoutes = [
  '/',
  '/about',
  '/about/ai-limitations',
  '/about/cloud-services',
  '/legal/privacy',
  '/login',
  '/register',
  '/dashboard',
  '/chat',
  '/settings',
  '/settings/privacy',
  '/admin/mcp/servers',
];

function normalizeRoute(route) {
  if (!route) return '/';
  return route.startsWith('/') ? route : `/${route}`;
}

function jsonResponse(payload, status = 200, headers = {}) {
  return {
    status,
    contentType: 'application/json',
    headers,
    body: JSON.stringify(payload),
  };
}

async function mockApi(page) {
  await page.route('**/__a11y/axe.js', async (route) => {
    return route.fulfill({
      status: 200,
      contentType: 'application/javascript',
      body: axeSource,
    });
  });

  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    const path = url.pathname.replace('/api/v1', '');
    const method = route.request().method().toUpperCase();

    if (path === '/auth/check' || path === '/auth/desktop/auto-login') {
      return route.fulfill(jsonResponse({
        authenticated: true,
        user: { id: 1, username: 'local-user', email: 'local@example.test', role: 'admin' },
      }));
    }

    if (path === '/auth/desktop/challenge') {
      return route.fulfill(jsonResponse({ nonce: 'a11y-ci-nonce' }));
    }

    if (path === '/gateway/providers') {
      return route.fulfill(jsonResponse({
        providers: [{ id: 'provider-openai', name: 'OpenAI', type: 'openai', model: 'gpt-5.5', is_default: true }],
      }));
    }

    if (path === '/settings/ai') {
      return route.fulfill(jsonResponse({ ai_processing_enabled: true, store_chat_history: true }));
    }

    if (path === '/gateway/sessions') return route.fulfill(jsonResponse({ sessions: [] }));
    if (path === '/pillars' || path === '/nodes' || path === '/edges') return route.fulfill(jsonResponse([]));
    if (path === '/simulations') return route.fulfill(jsonResponse([]));
    if (path.startsWith('/trace/runs')) return route.fulfill(jsonResponse({ runs: [] }));
    if (path === '/analytics/activity') return route.fulfill(jsonResponse([]));
    if (path === '/analytics/summary' || path === '/analytics/overview') return route.fulfill(jsonResponse({}));
    if (path === '/analytics/mcp') return route.fulfill(jsonResponse({ servers: 0, tools: 0, resources: 0 }));

    if (path === '/mcp/servers') {
      return route.fulfill(jsonResponse({ servers: [], runtime_servers: [] }));
    }

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
        services: {
          postgres: service,
          redis: service,
          neo4j: service,
          vector: service,
          object: service,
        },
      }));
    }

    if (path === '/storage/databases/autostart') return route.fulfill(jsonResponse({ enabled: true }));
    if (path === '/storage/cloud-config') return route.fulfill(jsonResponse({ success: true, cloud_config: {} }));
    if (path.startsWith('/storage/health/')) return route.fulfill(jsonResponse({ healthy: true }));

    return route.fulfill(jsonResponse({ success: method === 'GET' ? true : undefined }));
  });
}

const baseUrl = (process.env.A11Y_BASE_URL || 'http://127.0.0.1:3200').replace(/\/$/, '');
const routes = (process.env.A11Y_ROUTES || defaultRoutes.join(','))
  .split(',')
  .map((route) => normalizeRoute(route.trim()))
  .filter(Boolean);

const reportPath = resolve(
  repoRoot,
  process.env.A11Y_REPORT_PATH || 'reports/app-readiness/a11y-ci-report.json',
);

const axeSource = await readFile(axeSourcePath, 'utf8');
const browser = await chromium.launch({
  headless: true,
  args: ['--disable-dev-shm-usage', '--disable-setuid-sandbox', '--no-sandbox'],
});

const context = await browser.newContext({
  extraHTTPHeaders: {
    'x-datalogic-desktop': 'true',
  },
  viewport: { width: 1440, height: 900 },
});

const results = [];
let failureCount = 0;

try {
  for (const route of routes) {
    const page = await context.newPage();
    await mockApi(page);
    const target = `${baseUrl}${route}`;
    console.log(`Running a11y scan: ${target}`);

    const response = await page.goto(target, { waitUntil: 'domcontentloaded' });
    await page.waitForLoadState('networkidle').catch(() => undefined);
    await page.addScriptTag({ url: '/__a11y/axe.js' });

    const axeResult = await page.evaluate(async () => {
      return window.axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'] },
      });
    });

    const violations = axeResult.violations.map((violation) => ({
      id: violation.id,
      impact: violation.impact,
      description: violation.description,
      help: violation.help,
      helpUrl: violation.helpUrl,
      nodes: violation.nodes.map((node) => ({
        target: node.target,
        html: node.html,
        failureSummary: node.failureSummary,
      })),
    }));

    failureCount += violations.length;
    results.push({
      route,
      url: target,
      status: response?.status() ?? null,
      violation_count: violations.length,
      violations,
    });

    await page.close();
  }
} finally {
  await browser.close();
}

const payload = {
  generated_at: new Date().toISOString(),
  base_url: baseUrl,
  routes,
  total_routes: routes.length,
  total_violations: failureCount,
  results,
};

await mkdir(dirname(reportPath), { recursive: true });
await writeFile(reportPath, `${JSON.stringify(payload, null, 2)}\n`, 'utf8');

if (failureCount > 0) {
  console.error(`A11y scan failed with ${failureCount} violation(s). Report: ${reportPath}`);
  process.exit(1);
}

console.log(`A11y scan passed for ${routes.length} route(s). Report: ${reportPath}`);
