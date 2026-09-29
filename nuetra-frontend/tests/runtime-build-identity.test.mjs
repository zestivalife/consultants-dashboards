import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const readSource = (path) => readFile(new URL(path, import.meta.url), 'utf8');

test('runtime version endpoint exposes the deployed Vercel commit identity', async () => {
  const [versionSource, endpointSource] = await Promise.all([
    readSource('../lib/buildVersion.js'),
    readSource('../pages/api/version.js'),
  ]);

  assert.match(versionSource, /const BUILD_COMMIT_SHA =\s*[\s\S]*process\.env\.VERCEL_GIT_COMMIT_SHA[\s\S]*process\.env\.NEXT_PUBLIC_BUILD_COMMIT_SHA/);
  assert.match(versionSource, /commit_sha:\s*BUILD_COMMIT_SHA/);
  assert.match(versionSource, /branch:\s*BUILD_BRANCH/);
  assert.doesNotMatch(versionSource, /commit_sha:\s*firstEnv\(/);
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

test('CLI production deployment injects exact clean-worktree Git identity into the build', async () => {
  const [deploySource, packageSource] = await Promise.all([
    readSource('../scripts/deploy-production.mjs'),
    readSource('../package.json'),
  ]);

  assert.match(deploySource, /git\('rev-parse', 'HEAD'\)/);
  assert.match(deploySource, /git\('branch', '--show-current'\)/);
  assert.match(deploySource, /git\('status', '--short'\)/);
  assert.match(deploySource, /NEXT_PUBLIC_BUILD_COMMIT_SHA=\$\{commitSha\}/);
  assert.match(deploySource, /NEXT_PUBLIC_BUILD_BRANCH=\$\{branch\}/);
  assert.match(deploySource, /Production deployment requires a clean Git worktree/);
  assert.match(packageSource, /"deploy:production":\s*"node scripts\/deploy-production\.mjs"/);
});
