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

for (const route of routes) {
  const target = `${baseUrl}${route}`;
  // Run axe per route to keep failing URL explicit in CI output.
  // Use shell execution for Windows compatibility in CI agents.
  console.log(`Running a11y scan: ${target}`);
  const result = spawnSync(`npx axe ${target} --exit`, {
    stdio: 'inherit',
    shell: true,
  });

  if (result.error) {
    console.error(`A11y scan failed to execute for ${target}:`, result.error);
    process.exit(1);
  }

  if (result.status !== 0) {
    process.exit(result.status ?? 1);
  }
}
