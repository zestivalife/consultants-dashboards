import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api = readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');
const workspace = readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');
const leads = readFileSync(new URL('../components/external/ExternalLeads.jsx', import.meta.url), 'utf8');
const backend = readFileSync(new URL('../../services/practice-operations-service/app/main.py', import.meta.url), 'utf8');
const migration = readFileSync(new URL('../../services/practice-operations-service/alembic/versions/0064_external_practice_clients.py', import.meta.url), 'utf8');

test('active external workspace creates clients through authoritative Practice Operations', () => {
  assert.match(api, /createPracticeClient/);
  assert.match(api, /request\('\/clients'/);
  assert.match(api, /Idempotency-Key/);
  assert.match(workspace, /createPracticeClient/);
  assert.doesNotMatch(workspace, /createExternalClient/);
  assert.match(leads, /createPracticeClient/);
});

test('client creation is tenant scoped, assigned and idempotent', () => {
  assert.match(backend, /@app\.post\("\/api\/v1\/practice-operations\/clients"/);
  assert.match(backend, /_team_guard\(request,db,ctx,"CLIENT_CREATE"\)/);
  assert.match(backend, /idempotency_key/);
  assert.match(backend, /external_client_team_assignments/);
  assert.match(migration, /UNIQUE \(tenant_id, idempotency_key\)/);
  assert.match(migration, /uq_external_practice_client_email/);
  assert.match(migration, /uq_external_practice_client_mobile/);
});

test('assignment remains separate from health-data consent', () => {
  assert.match(backend, /"healthDataAuthorized":False/);
  assert.doesNotMatch(backend, /consented_scopes.*CLIENT_CREATED/);
});
