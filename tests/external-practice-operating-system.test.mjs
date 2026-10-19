import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const moduleSource=fs.readFileSync(new URL('../nuetra-frontend/components/external/ExternalPracticeOperatingSystem.jsx',import.meta.url),'utf8');
const workspaceSource=fs.readFileSync(new URL('../nuetra-frontend/components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const routerSource=fs.readFileSync(new URL('../nuetra-frontend/pages/dashboard/consultant.js',import.meta.url),'utf8');
const tenantRouteSource=fs.readFileSync(new URL('../nuetra-frontend/components/external/ExternalConsultantWorkspaceRoute.jsx',import.meta.url),'utf8');

test('practice operating system prepares every governed frontend module without production fixtures',()=>{
  for(const label of [
    'Consultations','Follow-ups','Goals & Progress','Tasks','Notifications','Check-ins',
    'Communication','Templates','Assessments','Practice / Team','Calendar','Tele-consultation',
    'Referrals','Client Notes','Tags & Segments','Data Export','Billing & Packages',
    'Package Renewals','Analytics','Practice Audit','Settings & Branding','Progress Reports',
    'Pre-consultation Summary','Report Comparison','Attention Rules','Client Portal',
  ]) assert.match(moduleSource,new RegExp(label.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
  assert.match(moduleSource,/No client data is fabricated/);
  assert.match(moduleSource,/Capability pending/);
});

test('all module surfaces reuse the external shell and remain mobile-first',()=>{
  assert.match(workspaceSource,/PRACTICE_NAV/);
  assert.match(workspaceSource,/ExternalPracticeModule/);
  assert.match(moduleSource,/overflow-x-auto/);
  assert.match(moduleSource,/env\(safe-area-inset-bottom\)/);
  assert.match(moduleSource,/lg:hidden/);
  assert.match(moduleSource,/min-h-11/);
});

test('frozen internal routing remains isolated from the external operating system',()=>{
  assert.match(routerSource,/ExternalConsultantWorkspaceRoute/);
  assert.match(tenantRouteSource,/workspace === 'IN_HOUSE'/);
  assert.match(tenantRouteSource,/ConsultantWorkspace/);
  assert.match(tenantRouteSource,/ExternalSaaSWorkspace/);
  assert.doesNotMatch(routerSource,/ExternalPracticeOperatingSystem/);
});
