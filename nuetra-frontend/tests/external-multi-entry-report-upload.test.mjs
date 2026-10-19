import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const intake=readFileSync(new URL('../components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const analyzer=readFileSync(new URL('../components/external/ExternalTransientReportAnalyzer.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/externalTransientReportApi.js',import.meta.url),'utf8');

test('global Reports requires an authorised client before analysis',()=>{assert.match(workspace,/Select an authorised client, analyze the report transiently/);assert.match(workspace,/required aria-label="Select client for report"/);assert.match(workspace,/Choose a client first/);assert.match(workspace,/Report analysis is always scoped to one authorised External client/);});
test('all report entry points converge on the external transient analysis API',()=>{assert.match(workspace,/ExternalTransientReportAnalyzer clientId=\{selected\.id\}/);assert.match(client360,/ExternalTransientReportAnalyzer clientId=\{client\.id\}/);assert.match(intake,/analyzeExternalClientIntakeReport\(token,file\)/);assert.equal((api.match(/export const analyzeExternalClientReport=/g)||[]).length,1);assert.equal((api.match(/export const analyzeExternalClientIntakeReport=/g)||[]).length,1);});
test('duplicate handling is owned by the single transient backend contract',()=>{assert.match(api,/\/report-analyses/);assert.match(analyzer,/setDialogError\(error\.message\|\|/);assert.doesNotMatch(analyzer,/uploadExternalClientDocument/);});
test('reviewed results remain joined to Client 360 biomarker history without retaining source files',()=>{assert.match(workspace,/Open Client 360/);assert.match(client360,/getExternalTransientBiomarkers/);assert.match(client360,/getExternalTransientBiomarkerHistory/);assert.match(analyzer,/source file was not retained/);assert.match(analyzer,/Confirm all & save/);});
test('client-uploaded analyses surface before review and never become a false zero',()=>{assert.match(client360,/getPendingExternalReportAnalyses/);assert.match(client360,/Lab report ready for consultant review/);assert.match(client360,/Review extracted biomarkers/);assert.match(client360,/Report review status unavailable/);assert.match(client360,/No empty or zero state has been inferred/);});
test('biomarker-capable external workspaces retain explicit Biomarkers access',()=>{const tabs=readFileSync(new URL('../lib/client360Capabilities.mjs',import.meta.url),'utf8');assert.match(tabs,/'Biomarkers'/);assert.match(tabs,/LAB_ANALYSIS/);assert.match(client360,/resolveClient360Navigation/);});
