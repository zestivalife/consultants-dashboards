import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const apiSource = fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const workspaceSource = fs.readFileSync(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');

test('Leads client sends authoritative search, filters, ordering and pagination', () => {
  assert.match(apiSource, /listFiteatsyIntakeLeads\(\{ query = '', status = 'all', order = 'desc', page = 1, pageSize = 20 \}/);
  for (const parameter of ['q: query', 'status', 'order', 'page: String(page)', 'pageSize: String(pageSize)']) {
    assert.ok(apiSource.includes(parameter));
  }
  assert.match(apiSource, /pagination: body\?\.pagination/);
  assert.match(apiSource, /diagnostic: body\?\.diagnostic/);
});

test('owner registry always uses the authoritative all-records Leads API', () => {
  assert.match(apiSource, /apiRequest\(`\/platform\/fiteatsy\/leads\?\$\{params\.toString\(\)\}`/);
  assert.doesNotMatch(apiSource.slice(apiSource.indexOf('export async function listFiteatsyIntakeLeads'), apiSource.indexOf('export async function issueFiteatsyTemporaryLoginPin')), /fiteatsy-client-directory/);
});

test('Platform Owner Leads UI exposes all discovery and state controls', () => {
  for (const label of [
    'Search name, email or mobile',
    'All statuses',
    'Newest first',
    'Oldest first',
    'Registration diagnostic',
    'Loading registrations…',
    'No eligible completed registrations match these filters.',
    'Previous',
    'Next',
    'Refresh',
    'Protected identity',
    'Assignment protected',
    'Review assignment',
    'Issue temporary Login PIN',
    'Not assigned',
    'Not configured',
    'Deletion protected',
    'Permanent deletion requires verified erasure workflow',
  ]) {
    assert.ok(workspaceSource.includes(label), `missing Leads UI state: ${label}`);
  }
});

test('Leads actions use accessible icon controls and do not expose unsafe erasure', () => {
  assert.match(workspaceSource, /<UserRoundCog[^>]+aria-hidden="true"/);
  assert.match(workspaceSource, /<KeyRound[^>]+aria-hidden="true"/);
  assert.match(workspaceSource, /<Trash2[^>]+aria-hidden="true"/);
  assert.match(workspaceSource, /aria-label=\{lead\.assignable \? `Review assignment for/);
  assert.match(workspaceSource, /aria-label=\{lead\.assignable \? `Issue temporary Login PIN for/);
  assert.match(workspaceSource, /<button type="button" title=\{lead\.permanentlyDeletable[^>]+disabled className=/);
  assert.doesNotMatch(workspaceSource, /Lead status<\/p>/);
});
