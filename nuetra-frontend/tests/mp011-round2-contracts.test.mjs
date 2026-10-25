import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read=path=>readFileSync(new URL(path,import.meta.url),'utf8');
const care=read('../components/external/ExternalCareOperations.jsx');
const consultation=read('../components/external/EmbeddedConsultationForm.jsx');
const profile=read('../components/external/ExternalClientProfileEnhancements.jsx');
const marketplace=read('../components/external/ExternalMarketplace.jsx');
const publicProfile=read('../pages/consultants/[slug].js');
const resources=read('../components/external/ExternalResourcesHomework.jsx');
const account=read('../components/external/ExternalAccountMenu.jsx');
const api=read('../lib/practiceOperationsApi.js');

test('health profile uses ordinary governed fields and a single server save',()=>{
  for(const value of ['Known allergies','Family history','Daily activity','Water intake (ml)','Medicines','Supplements','Smoking','Alcohol'])assert.equal(profile.includes(value),true,value);
  assert.match(profile,/onSave\(Object\.fromEntries/);
  assert.doesNotMatch(profile,/JSON\.parse/);
});

test('tasks and consultations carry client, due date, priority and notes through the persisted resource API',()=>{
  for(const value of ["resource:'tasks'",'client_id:form.client_id','due_at:form.due_at','priority:form.priority','notes:form.notes'])assert.equal(care.includes(value),true,value);
  assert.match(consultation,/createPracticeResource\('consultations'/);
  assert.match(consultation,/onSaved/);
  assert.match(api,/Idempotency-Key/);
});

test('professional profile and public preview share the marketplace projection',()=>{
  for(const value of ['My professional profile','Qualifications','Previous workplaces','Professional biography','Public preview'])assert.equal(marketplace.includes(value),true,value);
  for(const value of ['professional_title','experience_years','specialisations','bio'])assert.equal(publicProfile.includes(value),true,value);
  assert.equal(account.includes("onNavigate?.('marketplace')"),true);
});

test('custom resources expose only the approved authoring fields and use governed private document storage',()=>{
  for(const value of ['Title','Description','Tags','Attachment upload','uploadVaultDocument','downloadVaultDocument','CARE_TEAM_SHARED','vault-document:'])assert.equal(resources.includes(value),true,value);
  const editor=resources.slice(resources.indexOf("{editor&&"),resources.indexOf("{assign&&"));
  assert.doesNotMatch(editor,/Scope<|Type<select|Content reference/);
});
