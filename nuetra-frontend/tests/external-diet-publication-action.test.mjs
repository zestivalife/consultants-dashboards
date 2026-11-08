import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const plan = readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
const client360 = readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');

test('publication action is visible beside version, approval and download actions', () => {
  assert.match(plan, /Publish to Client App/);
  assert.match(plan, /Download DOCX/);
  assert.match(plan, /Download PDF/);
  assert.match(plan, /Save version/);
  assert.match(plan, /Approve exact version/);
  assert.match(plan, /flex flex-wrap items-center gap-2/);
});

test('publication confirms the assigned client and exact refreshed version', () => {
  assert.match(client360, /clientName=\{overview\?\.name\|\|client\.displayName\|\|client\.name\|\|'Client'\}/);
  assert.match(plan, /getConsultantDietPlan\(selected\.id\)/);
  assert.match(plan, /currentPlan\.status !== 'APPROVED'/);
  assert.match(plan, /currentPlan\.current_version/);
  assert.match(plan, /clientName\}'s Fiteatsy Nutrition screen/);
  assert.match(plan, /publication\.publication_id/);
});

test('unsaved edits cannot be published and backend remains publication authority', () => {
  assert.match(plan, /onDirtyChange=\{setEditorDirty\}/);
  assert.match(plan, /if \(editorDirty\) throw new Error\('Save the current Diet Plan changes before publishing/);
  assert.match(plan, /selected\.status!=='APPROVED'\|\|editorDirty/);
  assert.match(plan, /publishConsultantDietPlan\(selected\.id\)/);
  assert.match(api, /diet-plans\/\$\{encodeURIComponent\(planId\)\}\/publish/);
  assert.doesNotMatch(plan, /nutrition information.*access denied/i);
});

test('publication failures remain precise and success waits for the backend result', () => {
  assert.match(plan, /const publication = await publishConsultantDietPlan\(selected\.id\)/);
  assert.match(plan, /setMessage\(`Version \$\{publication\.version\} was published/);
  assert.match(plan, /The backend will verify the active Fiteatsy connection and Diet Plan publication consent/);
  assert.doesNotMatch(plan, /catch \([^)]*\) \{[^}]*published successfully/is);
});
