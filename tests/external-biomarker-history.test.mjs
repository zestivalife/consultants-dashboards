import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const component=readFileSync(new URL('../nuetra-frontend/components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../nuetra-frontend/lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('Client 360 adds Biomarkers without replacing Reports or existing health tabs',()=>{for(const tab of ['Health Profile','Nutrition','Measurements','Reports','Biomarkers','Timeline'])assert.ok(component.includes(tab));});
test('lab reports expose explicit processing and reprocessing states',()=>{for(const contract of ['Process report','Reprocess report','Processing…','processingStatus','processExternalClientReport'])assert.ok(component.includes(contract));});
test('latest biomarker cards expose source-linked history and review actions',()=>{for(const contract of ['Latest result per biomarker','View history','Source report','Confirm','Correct','Reject','pendingReviewCount'])assert.ok(component.includes(contract));});
test('correction UI states raw evidence is preserved and requires a reason',()=>{assert.match(component,/raw evidence is preserved/);assert.match(component,/required aria-label="Correction reason"/);});
test('API client covers process, extraction, latest, history, confirm, correction and rejection',()=>{for(const endpoint of ['/process','/extraction','/biomarkers','/history','/confirm','/reject'])assert.ok(api.includes(endpoint));});
