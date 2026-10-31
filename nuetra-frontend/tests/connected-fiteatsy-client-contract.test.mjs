import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');
const connectedView = readFileSync(new URL('../components/external/ConnectedFiteatsyClient360.jsx', import.meta.url), 'utf8');
const legacyView = readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../components/external/ExternalConsultantWorkspace.jsx', import.meta.url), 'utf8');

test('connected client rows keep every identity namespace explicit', () => {
  assert.match(api, /fiteatsyAccountId/);
  assert.match(api, /practiceClientId/);
  assert.match(api, /connectionId:String\(connection\.id\)/);
  assert.match(api, /accessState:'CONNECTED'/);
});

test('connected client detail is fetched only through the consented connection contract', () => {
  assert.match(connectedView, /getFiteatsyConnectionHealthContext\(connectionId\)/);
  assert.match(connectedView, /downloadFiteatsyConnectionReport\(connectionId,report\.id\)/);
  assert.doesNotMatch(connectedView, /getExternalClient360/);
  assert.doesNotMatch(connectedView, /getProfessionClient360/);
  assert.doesNotMatch(connectedView, /client\?\.id\).*health/i);
  assert.match(connectedView, /profile\?\.healthProfile/);
  assert.match(connectedView, /state\.data\?\.wearables/);
  assert.match(connectedView, /profile\?\.onboarding/);
});

test('all connected-client entry points select the connection-scoped view', () => {
  assert.match(legacyView, /props\.client\?\.accessState === 'CONNECTED'/);
  assert.match(legacyView, /<ConnectedFiteatsyClient360 client=\{props\.client\}/);
  assert.match(workspace, /<ExternalClient360 client=\{selected\}/);
});

test('assigned-only clients remain visibly distinct from consented connections', () => {
  assert.match(api, /accessState:'ASSIGNED'/);
  assert.match(api, /connectionId:null/);
  assert.match(api, /assignmentState:'NEW_ASSIGNED'/);
  assert.match(connectedView, /no active consented connection/i);
});
