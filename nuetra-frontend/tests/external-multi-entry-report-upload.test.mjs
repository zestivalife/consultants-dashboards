import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('global Reports requires an authorised client before upload',()=>{assert.match(workspace,/Select the authorised client before choosing/);assert.match(workspace,/required aria-label="Select client for report"/);assert.match(workspace,/disabled=\{busy\|\|!selected\|\|!file\}/);});
test('global Reports and Client 360 use the same canonical upload API',()=>{assert.match(workspace,/uploadExternalClientDocument\(selected\.id/);assert.match(client360,/uploadExternalClientDocument\(client\.id/);assert.equal((api.match(/export async function uploadExternalClientDocument/g)||[]).length,1);});
test('duplicate report response uses controlled product copy',()=>{assert.match(workspace,/This report has already been uploaded for this client\./);assert.match(workspace,/DOCUMENT_DUPLICATE/);});
test('reports remain joined to Client 360 and biomarker history',()=>{assert.match(workspace,/same secure repository, extraction pipeline, and biomarker history/);assert.match(workspace,/Open Client 360/);assert.match(client360,/getExternalClientBiomarkers/);assert.match(client360,/getExternalBiomarkerHistory/);});
