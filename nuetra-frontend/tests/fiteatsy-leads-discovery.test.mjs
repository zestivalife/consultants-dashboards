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
  ]) {
    assert.ok(workspaceSource.includes(label), `missing Leads UI state: ${label}`);
  }
});
