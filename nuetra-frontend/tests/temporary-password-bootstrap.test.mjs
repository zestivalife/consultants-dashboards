import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

import {
  getExternalTemporaryPasswordIdentifier,
  getTemporaryPasswordBootstrapView,
  isExternalTemporaryPasswordUser,
  isSameTemporaryPasswordUser,
  TEMPORARY_PASSWORD_BOOTSTRAP_TIMEOUT_MS,
  TEMPORARY_PASSWORD_BOOTSTRAP_VIEW,
} from '../lib/temporaryPasswordBootstrap.js';

const pageSource = readFileSync(new URL('../pages/auth/change-temporary-password.js', import.meta.url), 'utf8');
const authSource = readFileSync(new URL('../context/AuthContext.js', import.meta.url), 'utf8');

test('valid temporary-password authority renders immediately without waiting for auth/me', () => {
  assert.equal(
    getTemporaryPasswordBootstrapView({ user: { id: 'qa-internal' }, isLoading: true, timedOut: false }),
    TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.FORM
  );
});

test('bootstrap remains loading only during the bounded authentication window', () => {
  assert.equal(TEMPORARY_PASSWORD_BOOTSTRAP_TIMEOUT_MS, 10000);
  assert.equal(
    getTemporaryPasswordBootstrapView({ user: null, isLoading: true, timedOut: false }),
    TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.LOADING
  );
});

test('unavailable auth/me becomes a controlled error instead of an infinite loader', () => {
  assert.equal(
    getTemporaryPasswordBootstrapView({ user: null, isLoading: true, timedOut: true }),
    TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.ERROR
  );
});

test('missing or expired temporary authority fails closed', () => {
  assert.equal(
    getTemporaryPasswordBootstrapView({ user: null, isLoading: false, timedOut: false }),
    TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.ERROR
  );
});

test('temporary password setup does not depend on tenant, assignment, or workspace bootstrap', () => {
  for (const role of ['consultant', 'senior_consultant', 'external_consultant']) {
    assert.equal(
      getTemporaryPasswordBootstrapView({ user: { id: `qa-${role}`, role }, isLoading: true, timedOut: false }),
      TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.FORM
    );
  }
  assert.doesNotMatch(pageSource, /tenant|assignment|workspaceReady|getFiteatsyConsultantOnboarding/);
  assert.match(authSource, /const accountActionRoute = getAccountActionRoute\(user\);/);
  assert.match(authSource, /if \(accountActionRoute\) return accountActionRoute;/);
});

test('legacy onboarding cannot invalidate an authenticated session', () => {
  assert.doesNotMatch(authSource, /getFiteatsyConsultantOnboarding/);
  assert.match(authSource, /return getPostLoginPath\(user\);/);
});

test('controlled failure exposes retry and return-to-login actions', () => {
  assert.match(pageSource, />\s*Retry\s*</);
  assert.match(pageSource, />\s*Back to login\s*</);
  assert.match(pageSource, /window\.location\.reload\(\)/);
  assert.match(pageSource, /onClick=\{logout\}/);
});

test('successful password change persists the replacement session and routes by governed role', () => {
  assert.match(authSource, /authAPI\.changeTemporaryPassword/);
  assert.match(authSource, /persistSession\(session, rememberMe\)/);
  assert.match(authSource, /router\.replace\(getPostAuthPathForUser\(nextUser\)\)/);
});

test('only External consultant roles use the release-safe authority recovery', () => {
  for (const role of ['consultant', 'external_consultant', 'provider', 'dietician', 'dietitian']) {
    assert.equal(isExternalTemporaryPasswordUser({ role }), true);
  }
  for (const role of ['superuser', 'internal_super_admin', 'senior_consultant', 'practice_admin']) {
    assert.equal(isExternalTemporaryPasswordUser({ role }), false);
  }
});

test('External authority recovery is bound to the exact user identity', () => {
  const user = { id: 'external-1', email: 'qa@example.invalid' };
  assert.equal(getExternalTemporaryPasswordIdentifier(user), 'qa@example.invalid');
  assert.equal(isSameTemporaryPasswordUser(user, { id: 'external-1' }), true);
  assert.equal(isSameTemporaryPasswordUser(user, { id: 'external-2' }), false);
});

test('External temporary-password change reauthenticates before replacement without changing Internal flow', () => {
  assert.match(authSource, /if \(isExternalTemporaryPasswordUser\(user\)\)/);
  assert.match(authSource, /await authAPI\.login\(identifier, currentPassword\)/);
  assert.match(authSource, /isSameTemporaryPasswordUser\(user, authenticatedUser\)/);
  assert.match(authSource, /getAccountActionRoute\(authenticatedUser\) !== '\/auth\/change-temporary-password'/);
});
