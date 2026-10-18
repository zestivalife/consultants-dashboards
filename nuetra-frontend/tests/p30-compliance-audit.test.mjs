import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const ui=fs.readFileSync(new URL('../components/external/ExternalComplianceAudit.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('P30 presents operational evidence without legal certification claims',()=>{
  assert.match(ui,/not legal compliance certification/i);
  assert.match(ui,/Loading audit evidence/);
  assert.match(ui,/role="alert"/);
  assert.match(ui,/No audit evidence exists for this confirmed scope/);
});

test('P30 client export explicitly excludes private and internal notes',()=>{
  assert.match(ui,/Private notes, raw session notes, internal intelligence, and team notes are excluded/);
  assert.match(api,/compliance\/exports\/clients/);
  assert.match(api,/compliance\/audit/);
});
