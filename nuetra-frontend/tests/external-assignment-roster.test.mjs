import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');
const bridge = readFileSync(new URL('../../services/practice-operations-service/app/fiteatsy_connections.py', import.meta.url), 'utf8');

test('external client roster merges authoritative assignments with consented connections', () => {
  assert.match(api, /ledger\?\.assigned_clients/);
  assert.match(api, /clientsByUserId/);
  assert.match(api, /accessState:'ASSIGNED'/);
  assert.match(api, /consentedScopes:\[\]/);
  assert.match(api, /profileAvailable:false/);
  assert.match(api, /assignment\?\.displayName/);
  assert.match(api, /assignmentState:'NEW_ASSIGNED'/);
  assert.match(api, /Promise\.allSettled\(active\.map/);
  assert.match(api, /profileError:result\.reason\?\.message/);
  assert.match(api, /assignmentByUserId/);
  assert.match(workspace, /selected\.accessState==='ASSIGNED'\?<AssignedClientAccessView/);
  assert.match(workspace, /New assigned/);
  assert.match(workspace, /No missing or zero data is inferred/);
});

test('practice operations requests a short-lived purpose-bound roster delegation', () => {
  assert.match(bridge, /fiteatsy\.external\.assignment\.read/);
  assert.match(bridge, /external_consultant_assignment_roster/);
  assert.match(bridge, /canonical_professional_id/);
  assert.match(bridge, /assigned_clients/);
  assert.match(bridge, /FITEATSY_ASSIGNMENT_ROSTER_FAILED/);
});
