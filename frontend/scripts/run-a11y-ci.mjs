#!/usr/bin/env node

import { spawnSync } from 'node:child_process';

const defaultRoutes = [
  '/',
  '/about',
  '/about/ai-limitations',
  '/about/cloud-services',
  '/legal/privacy',
  '/login',
  '/register',
];

function normalizeRoute(route) {
  if (!route) return '/';
  return route.startsWith('/') ? route : `/${route}`;
}

const baseUrl = (process.env.A11Y_BASE_URL || 'http://127.0.0.1:3200').replace(/\/$/, '');
const routes = (process.env.A11Y_ROUTES || defaultRoutes.join(','))
  .split(',')
  .map((route) => normalizeRoute(route.trim()))
  .filter(Boolean);

// Extra Chrome flags for headless CI environments (ubuntu-24.04).
// --disable-dev-shm-usage prevents crashes when /dev/shm is small.
// --disable-setuid-sandbox pairs with --no-sandbox on restricted hosts.
// CHROME_TEST_PATH must also be set so @axe-core/cli adds --no-sandbox.
const CI_CHROME_OPTS = process.env.CI
  ? ' --chrome-options=disable-dev-shm-usage,disable-setuid-sandbox'
  : '';

for (const route of routes) {
  const target = `${baseUrl}${route}`;
  // Run axe per route to keep failing URL explicit in CI output.
  // Use shell execution for Windows compatibility in CI agents.
  // --tags wcag2a,wcag2aa checks WCAG 2.0 A/AA rules; excludes best-practice
  // noise that would otherwise produce false positives on CI.
  console.log(`Running a11y scan: ${target}`);
  const result = spawnSync(
    `npx axe ${target} --exit --tags wcag2a,wcag2aa${CI_CHROME_OPTS}`,
    { stdio: 'inherit', shell: true },
  );

  if (result.error) {
    console.error(`A11y scan failed to execute for ${target}:`, result.error);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
