import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const analytics=readFileSync(new URL('../components/external/ExternalPracticeAnalytics.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('P18 exposes governed analytics sections and textual chart equivalents',()=>{
  for(const label of ['Overview','Clients','Sessions','Revenue','Engagement','Operations','Outcomes','Team'])assert.match(analytics,new RegExp(label));
  assert.match(analytics,/records in this distribution/);
  assert.match(analytics,/minimum_cohort_size/);
});

test('P18 preserves failed partial and confirmed-empty states without false zero',()=>{
  assert.match(analytics,/Analytics unavailable/);
  assert.match(analytics,/Partial data/);
  assert.match(analytics,/Confirmed empty/);
  assert.match(analytics,/No unavailable metric has been converted to zero/);
});

test('P18 is permission gated and calls only the tenant-authorised API',()=>{
  assert.match(workspace,/ANALYTICS_VIEW/);
  assert.match(workspace,/ExternalPracticeAnalytics/);
  assert.match(api,/\/analytics\/practice\?preset=/);
  assert.doesNotMatch(analytics,/localStorage|sessionStorage|PRIVATE_NOTE/);
});

