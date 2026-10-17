import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const resolver=fs.readFileSync(new URL('../lib/professionExperience.js',import.meta.url),'utf8');
const settings=fs.readFileSync(new URL('../components/external/ExternalPracticeSettings.jsx',import.meta.url),'utf8');
const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');

test('one central resolver defines every approved profession experience',()=>{
  for(const code of ['DIETITIAN','NUTRITIONIST','DIABETES_EDUCATOR','PSYCHOLOGIST','WELLNESS_CONSULTANT','HEALTH_COACH','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','PHYSIOTHERAPIST','MENTAL_WELLNESS_THERAPIST'])assert.match(resolver,new RegExp(`${code}:`));
  assert.match(resolver,/resolveProfessionExperience/);
});

test('settings and workspace consume the shared profession model',()=>{
  assert.match(settings,/PROFESSION_OPTIONS/);
  assert.match(workspace,/resolveProfessionExperience/);
  assert.match(workspace,/professionExperience\.care/);
  assert.match(workspace,/professionExperience\.terminology/);
});

test('profession empty states are explicit and do not fabricate records',()=>{
  for(const copy of ['No sessions recorded yet.','No physical assessments recorded yet.','No coaching check-ins yet.','No education sessions recorded yet.'])assert.match(resolver,new RegExp(copy.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
});
