import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const auth = fs.readFileSync(new URL('../context/AuthContext.js', import.meta.url), 'utf8');
const workspace = fs.readFileSync(new URL('../components/external/ExternalConsultantWorkspace.jsx', import.meta.url), 'utf8');
const api = fs.readFileSync(new URL('../lib/api.js', import.meta.url), 'utf8');
const withAuth = fs.readFileSync(new URL('../hocs/withAuth.js', import.meta.url), 'utf8');

test('External Consultant account menu exposes one canonical logout control', () => {
  assert.match(workspace, /aria-label="Account menu"/);
  assert.match(workspace, />Profile<\/Link>/);
  assert.match(workspace, />Practice Settings<\/Link>/);
  assert.match(workspace, /loggingOut\?'Logging out…':'Log out'/);
  assert.match(workspace, /await logout\(\)/);
});

test('logout revokes the refresh session then clears all browser authority', () => {
  assert.match(auth, /await authAPI\.logout\(refreshToken\)/);
  assert.match(auth, /clearBrowserSessionState\(\)/);
  assert.match(api, /localStorage\.removeItem\('access_token'\)/);
  assert.match(api, /sessionStorage\.removeItem\('refresh_token'\)/);
  assert.match(auth, /clearStoredSession\(\)/);
  assert.match(auth, /clearExternalWorkspaceCaches\(\)/);
  assert.match(auth, /window\.location\.replace\('\/login'\)/);
});

test('logout is fail-safe when server revocation is temporarily unavailable', () => {
  const logoutBlock = auth.match(/async function logout\(\) \{[\s\S]*?\n  \}/)?.[0] || '';
  assert.match(logoutBlock, /try \{[\s\S]*await authAPI\.logout/);
  assert.match(logoutBlock, /catch \{[\s\S]*Best effort logout/);
  assert.match(logoutBlock, /clearBrowserSessionState\(\)/);
});

test('cross-tab logout clears stale tenant, role, and client authority', () => {
  assert.match(auth, /LOGOUT_EVENT_KEY/);
  assert.match(auth, /window\.addEventListener\('storage', handleRemoteLogout\)/);
  assert.match(auth, /setUser\(null\)/);
  assert.match(auth, /EXTERNAL_WORKSPACE_CACHE_PREFIXES/);
});

test('protected navigation cannot restore the logged-out workspace from browser history', () => {
  assert.match(auth, /window\.location\.replace\('\/login'\)/);
  assert.doesNotMatch(auth, /router\.push\('\/login'\)/);
  assert.match(withAuth, /if \(!isLoading && !user\)/);
  assert.match(withAuth, /router\.replace\('\/login'\)/);
});
