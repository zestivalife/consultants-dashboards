import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const read=path=>fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8');

test('signup exposes exactly the newly approved profession codes',()=>{
  const source=read('pages/signup.js');
  for(const role of ['WELLNESS_CONSULTANT','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','MENTAL_WELLNESS_THERAPIST'])assert.match(source,new RegExp(role));
});

test('profession intake uses dedicated public route without replacing legacy intake',()=>{
  const api=read('lib/professionIntakeApi.js');
  const page=read('pages/profession-intake/[token].js');
  assert.match(api,/api\/gateway\/api\/v1\/profession-intake/);
  assert.doesNotMatch(api,/v1\/external\/intake/);
  assert.match(page,/Save progress/);
  assert.match(page,/Submit intake/);
});

test('dashboard and Client360 consume the read-only canonical profession projection',()=>{
  const workspace=read('components/external/ExternalSaaSWorkspace.jsx');
  const client360=read('components/external/ExternalClient360.jsx');
  assert.match(workspace,/listProfessionIntakeProjections/);
  assert.match(workspace,/intakeState:projection.status/);
  assert.match(client360,/getClientProfessionIntake/);
  assert.match(client360,/createProfessionIntakeInvitation/);
  assert.match(client360,/professionIntake\?\.completion_percent/);
});
