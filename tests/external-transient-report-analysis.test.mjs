import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const component=readFileSync(new URL('../nuetra-frontend/components/external/ExternalBiomarkerReview.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const intake=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../nuetra-frontend/components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../nuetra-frontend/lib/externalTransientReportApi.js',import.meta.url),'utf8');

test('report UX exposes a staged transient analysis flow',()=>{
  for(const copy of ['Reading report','Extracting health parameters','Validating extracted values','Organising biomarkers','Preparing results for review'])assert.match(component,new RegExp(copy));
  assert.match(component,/source file not retained/);
  assert.match(component,/Confirm/);
  assert.match(component,/Correct/);
  assert.match(component,/Reject/);
  assert.match(component,/decision:'PENDING'/);
  assert.match(component,/Confirm all valid/);
  assert.match(component,/Save to Client Profile/);
  assert.match(component,/item\.decision==='PENDING'&&item\.bulkConfirmEligible/);
  assert.match(component,/Only confirmed or corrected results are saved\./);
  assert.match(component,/Biomarkers were not saved/);
});

test('bulk confirmation is restricted to source-traceable eligible markers',()=>{
  assert.match(component,/bulkConfirmEligible/);
  assert.match(component,/correctionIncomplete/);
  assert.match(component,/disabled=\{busy\|\|!counts\.ready\|\|correctionIncomplete\}/);
  assert.match(component,/decision==='PENDING'&&item\.bulkConfirmEligible/);
  for(const control of ['Search biomarker','Filter biomarkers','Sort biomarkers'])assert.match(component,new RegExp(control));
});

test('new lab reports use report-analyses and save structured review output',()=>{
  assert.match(api,/\/report-analyses/);
  assert.match(api,/saveExternalReportBiomarkers/);
  assert.match(component,/analyzeExternalClientReport/);
  assert.match(component,/saveExternalReportBiomarkers/);
});

test('historical stored records stay available while primary analysis is additive',()=>{
  assert.match(client360,/ExternalTransientReportAnalyzer/);
  assert.match(client360,/Historical stored documents/);
  assert.match(client360,/Source files from transient analysis are not retained/);
});

test('all three report entry points converge on the transient analysis contract',()=>{
  assert.match(intake,/analyzeExternalClientIntakeReport/);
  assert.match(intake,/source not retained/);
  assert.match(client360,/ExternalTransientReportAnalyzer/);
  assert.match(workspace,/ExternalTransientReportAnalyzer/);
  assert.match(api,/getPendingExternalReportAnalyses/);
});

test('confirmed transient biomarkers remain visible when the legacy source fails',()=>{
  assert.match(client360,/Promise\.allSettled\(\[getExternalClientBiomarkers\(client\.id\),getExternalTransientBiomarkers\(client\.id\)\]\)/);
  assert.match(client360,/legacyResult\.status==='rejected'&&transientResult\.status==='rejected'/);
  assert.match(client360,/transientResult\.status==='fulfilled'\?transientResult\.value:\{latest:\[\],pendingReviewCount:0\}/);
});
