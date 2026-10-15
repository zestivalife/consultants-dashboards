import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const component=readFileSync(new URL('../nuetra-frontend/components/external/ExternalTransientReportAnalyzer.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const intake=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../nuetra-frontend/components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../nuetra-frontend/lib/externalTransientReportApi.js',import.meta.url),'utf8');

test('report UX exposes a staged transient analysis flow',()=>{
  for(const copy of ['Reading report','Extracting biomarkers','Mapping results','Preparing review'])assert.match(component,new RegExp(copy));
  assert.match(component,/source file was not retained/);
  assert.match(component,/Confirm/);
  assert.match(component,/Correct/);
  assert.match(component,/Reject/);
  assert.match(component,/decision:'PENDING'/);
  assert.match(component,/Confirm marker/);
  assert.match(component,/markers reviewed/);
  assert.match(component,/Save reviewed only/);
  assert.match(component,/Confirm all & save/);
  assert.match(component,/item\.decision==='PENDING'\?\{\.\.\.item,decision:'CONFIRMED',correction:null\}:item/);
  assert.match(component,/persistItems\(nextItems\)/);
  assert.match(component,/Corrections and rejections already made will be preserved\./);
  assert.match(component,/Biomarkers were not saved/);
});

test('individual save is gated while bulk save confirms only pending markers',()=>{
  assert.match(component,/reviewedCount=items\.filter\(item=>item\.decision!=='PENDING'\)\.length/);
  assert.match(component,/reviewComplete=items\.length>0&&reviewedCount===items\.length/);
  assert.match(component,/disabled=\{busy\|\|!reviewComplete\|\|correctionIncomplete\}/);
  assert.match(component,/confirmAllAndSave/);
  assert.match(component,/item\.decision==='PENDING'/);
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
