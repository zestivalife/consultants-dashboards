import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const readSource = (path) => readFile(new URL(path, import.meta.url), 'utf8');

test('runtime version endpoint exposes the deployed Vercel commit identity', async () => {
  const [versionSource, endpointSource] = await Promise.all([
    readSource('../lib/buildVersion.js'),
    readSource('../pages/api/version.js'),
  ]);

  assert.match(versionSource, /commit_sha:\s*firstEnv\('VERCEL_GIT_COMMIT_SHA'/);
  assert.match(endpointSource, /getFrontendVersion\(\)/);
  assert.match(endpointSource, /res\.status\(200\)\.json/);
});

test('production UI visibly reports the exact browser bundle commit', async () => {
  const [badgeSource, appSource] = await Promise.all([
    readSource('../components/ProductionVersionBadge.jsx'),
    readSource('../pages/_app.js'),
  ]);

  assert.match(badgeSource, /data-testid="production-version-badge"/);
  assert.match(badgeSource, /Build \{shortSha\(browserBundle\.commit_sha\)\}/);
  assert.match(badgeSource, /Browser bundle commit:/);
  assert.match(appSource, /<ProductionVersionBadge\s*\/>/);
});
