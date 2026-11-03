import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const projection=readFileSync(new URL('../../services/practice-operations-service/app/client_directory.py',import.meta.url),'utf8');
const directory=readFileSync(new URL('../../services/practice-operations-service/app/main.py',import.meta.url),'utf8');

test('authoritative directory includes active remote assignments without granting health consent',()=>{
  assert.match(directory,/list_assigned_fiteatsy_clients\(ctx\)/);
  assert.match(directory,/SELECT client_id FROM remote_assignments/);
  assert.match(directory,/ASSIGNED_CONNECTION_PENDING/);
  assert.match(projection,/healthDataAuthorized/);
  assert.match(projection,/consentedScopes/);
});

test('assignment-only clients are visible but cannot enter Client 360',()=>{
  assert.match(workspace,/ASSIGNED_CONNECTION_PENDING: 'Assigned'/);
  assert.match(workspace,/function AssignedClientAccessView/);
  assert.match(workspace,/Assignment alone does not expose health data/);
  assert.match(workspace,/selected\.relationshipStatus==='ASSIGNED_CONNECTION_PENDING'/);
});
