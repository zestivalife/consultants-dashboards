import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const api=fs.readFileSync(new URL('../lib/assessmentApi.js',import.meta.url),'utf8');const ui=fs.readFileSync(new URL('../components/external/ExternalAssessments.jsx',import.meta.url),'utf8');const shell=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
test('P2 assessment API covers library assignment history save and completion',()=>{for(const value of ['definitions','assignAssessment','listClientAssessments','saveAssessment','completeAssessment'])assert.match(api,new RegExp(value))});
test('P2 UI distinguishes loading error confirmed empty and history',()=>{for(const value of ["'loading'","'error'",'No assessments assigned yet.','AssessmentHistory','AssessmentCard'])assert.match(ui,new RegExp(value.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')))});
test('assessment workspace is integrated without Diet Plan modification',()=>{assert.match(shell,/ExternalAssessments/);assert.doesNotMatch(ui,/Diet Plan|Common Food|biomarker/i)});
test('assessment navigation is capability-gated on desktop and mobile',()=>{
  assert.match(shell,/id==='assessments'.*capabilities\.has\('ASSESSMENTS'\).*capabilities\.has\('assessments'\)/s);
  assert.match(shell,/professionNav\.map/);
  assert.match(shell,/\.\.\.NAV,\.\.\.professionNav/);
  assert.doesNotMatch(shell,/SECONDARY_NAV\.map/);
  assert.doesNotMatch(shell,/\.\.\.NAV,\.\.\.SECONDARY_NAV/);
});
