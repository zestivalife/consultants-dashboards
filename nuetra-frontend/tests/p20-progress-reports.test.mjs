import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';
const reports=readFileSync(new URL('../components/external/ExternalProgressReports.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const portal=readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('P20 report wizard covers type period sections preview generate and share',()=>{
  for(const label of ['Type','Period','Sections','Preview','Generate','Share'])assert.match(reports,new RegExp(label));
  for(const type of ['CLIENT_PROGRESS_REPORT','REHAB_PROGRESS_REPORT','THERAPY_PROGRESS_REPORT','OT_PROGRESS_REPORT'])assert.match(reports,new RegExp(type));
});
test('P20 exposes immutable PDF DOCX and source provenance safety',()=>{
  assert.match(reports,/immutable PDF \+ DOCX/);assert.match(reports,/PRACTITIONER_ENTERED|provenance/);
  assert.match(reports,/Private notes, raw session notes, draft plans, and internal intelligence are excluded/);
  assert.match(api,/artifacts\/\$\{encodeURIComponent\(format\)\}/);
});
test('P20 is permission gated and shared reports alone reach the portal',()=>{
  assert.match(workspace,/REPORT_VIEW/);assert.match(workspace,/ExternalProgressReports/);assert.match(client360,/Progress Reports/);
  assert.match(portal,/Shared progress reports/);assert.match(portal,/data\.sharedReports/);assert.doesNotMatch(portal,/progress-reports.*DRAFT/);
});
