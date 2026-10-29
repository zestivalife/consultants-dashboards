import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import {
  BUILD_GATE_STATE,
  buildControlledReloadUrl,
  classifyFrontendBuild,
} from '../lib/frontendBuildResilience.js';

const shaA = 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa';
const shaB = 'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb';
const gateSource = readFileSync(new URL('../components/FrontendBuildGate.jsx', import.meta.url), 'utf8');
const authSource = readFileSync(new URL('../context/AuthContext.js', import.meta.url), 'utf8');

test('matching exact bundle and runtime SHAs allow authentication bootstrap', () => {
  assert.equal(classifyFrontendBuild({ bundleSha: shaA, runtimeSha: shaA }), BUILD_GATE_STATE.CURRENT);
});

test('a stale tab receives one controlled current-build transition', () => {
  assert.equal(classifyFrontendBuild({ bundleSha: shaA, runtimeSha: shaB }), BUILD_GATE_STATE.STALE);
  const url = buildControlledReloadUrl('https://consultant.nuetra.in/dashboard/owner?view=users', shaB);
  assert.equal(new URL(url).searchParams.get('__nuetra_build'), shaB);
});

test('the same unresolved mismatch stops automatic reload looping', () => {
  assert.equal(
    classifyFrontendBuild({ bundleSha: shaA, runtimeSha: shaB, attemptedRuntimeSha: shaB }),
    BUILD_GATE_STATE.RECOVERY_REQUIRED
  );
});

test('manual recovery clears the one-shot marker and performs a controlled reload', () => {
  assert.match(gateSource, /const retryCurrentRuntime = useCallback/);
  assert.match(gateSource, /sessionStorage\.removeItem\(BUILD_RELOAD_ATTEMPT_KEY\)/);
  assert.match(gateSource, /<RecoveryScreen onRetry=\{retryCurrentRuntime\}/);
  assert.doesNotMatch(gateSource, /checkRuntime\(\{ allowReload: false \}\)/);
});

test('unverifiable runtime identity fails into controlled recovery', () => {
  assert.equal(classifyFrontendBuild({ bundleSha: shaA, runtimeSha: 'unknown' }), BUILD_GATE_STATE.RUNTIME_UNAVAILABLE);
});

test('stale-build handling preserves tokens, sessions, and backend authority', () => {
  assert.match(gateSource, /cache:\s*'no-store'/);
  assert.match(gateSource, /sessionStorage\.setItem\(BUILD_RELOAD_ATTEMPT_KEY/);
  assert.match(gateSource, /window\.location\.replace\(buildControlledReloadUrl/);
  assert.match(gateSource, /BroadcastChannel\(BUILD_SYNC_CHANNEL\)/);
  assert.doesNotMatch(gateSource, /clearTokens|clearBrowserSessionState|logout|authAPI\.logout/);
});

test('legacy onboarding is not a secondary authentication dependency', () => {
  assert.doesNotMatch(authSource, /getFiteatsyConsultantOnboarding/);
  assert.match(authSource, /return getPostLoginPath\(user\);/);
});

test('build gate runs before AuthProvider and workspace bootstrap', () => {
  const appSource = readFileSync(new URL('../pages/_app.js', import.meta.url), 'utf8');
  assert.ok(appSource.indexOf('<FrontendBuildGate>') < appSource.indexOf('<AuthProvider>'));
});
