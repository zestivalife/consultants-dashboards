import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { client360CapabilityState, connectedClient360Configuration, resolveClient360Navigation, resolveClient360Tabs } from '../lib/client360Capabilities.mjs';

const component=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');

for (const profession of ['DIETITIAN','NUTRITIONIST','CLINICAL_NUTRITIONIST','SPORTS_NUTRITIONIST']) {
  test(`${profession} exposes governed nutrition Client360 composition`, () => {
    const configuration={profession,professionWorkspace:true,capabilities:['DIET_PLAN','BIOMARKERS','MEASUREMENTS','RESOURCE_LIBRARY','GOALS_PROGRESS','PROGRESS_REPORTS','PRACTICE_TEAM','BILLING']};
    const navigation=resolveClient360Navigation(configuration);
    assert.equal(navigation.length,5);
    assert.equal(navigation[2].label,'Nutrition & Care');
    assert.deepEqual(navigation[1].modules,['Health Profile','Biomarkers','Health Records','Measurements','Reports']);
    for(const required of ['Overview','Health Profile','Health Records','Nutrition','Diet Plan','Measurements','Reports','Biomarkers','Goals / Progress','Timeline','Documents','Resources & Homework']) assert.ok(resolveClient360Tabs(configuration).includes(required),required);
  });
}

test('Health Coach fallback remains truthful and does not expose diet or biomarkers',()=>{
  const navigation=resolveClient360Navigation({profession:'HEALTH_COACH',professionWorkspace:true,capabilities:['CONSULTATIONS','GOALS_PROGRESS','HABIT_PLAN','RESOURCE_LIBRARY','HOMEWORK']});
  const tabs=navigation.flatMap(section=>section.modules);
  assert.equal(navigation[2].label,'Care');
  assert.equal(tabs.includes('Diet Plan'),false);
  assert.equal(tabs.includes('Nutrition'),false);
  assert.equal(tabs.includes('Biomarkers'),false);
  assert.ok(tabs.includes('Profession'));
  assert.ok(tabs.includes('Resources & Homework'));
});

test('Psychologist and Physiotherapist never inherit nutrition-only modules',()=>{
  for(const profession of ['PSYCHOLOGIST','PHYSIOTHERAPIST']){
    const tabs=resolveClient360Tabs({profession,professionWorkspace:true,capabilities:['CONSULTATIONS','GOALS_PROGRESS','RESOURCE_LIBRARY','HOMEWORK']});
    assert.equal(tabs.includes('Diet Plan'),false);
    assert.equal(tabs.includes('Nutrition'),false);
    assert.equal(tabs.includes('Biomarkers'),false);
  }
});

test('registry-controlled Diabetes Educator capabilities are respected',()=>{
  const enabled=client360CapabilityState({profession:'DIABETES_EDUCATOR',capabilities:['BIOMARKERS','DIET_PLAN_AUTHORING']});
  assert.deepEqual(enabled,{dietPlan:true,biomarkers:true,measurements:false});
});

test('production Client360 uses bounded primary and responsive secondary navigation',()=>{
  assert.match(component,/resolveClient360Navigation/);
  assert.match(component,/Client 360 primary sections/);
  assert.match(component,/Client 360 primary section/);
  assert.match(component,/grid-cols-5/);
  assert.match(component,/lg:flex-wrap/);
  assert.doesNotMatch(component,/Client 360 sections[^\n]+overflow-x-auto/);
});

test('an authorised Fiteatsy connection exposes only its consented clinical modules',()=>{
  const configuration=connectedClient360Configuration({profession:'OTHER',capabilities:[]},{
    connectionId:'connection-1',healthDataAuthorized:true,consentedScopes:['BIOMARKERS','MEASUREMENTS'],
  });
  const state=client360CapabilityState(configuration);
  assert.deepEqual(state,{dietPlan:false,biomarkers:true,measurements:true});
  assert.deepEqual(resolveClient360Navigation(configuration)[1].modules,['Health Profile','Biomarkers','Health Records','Measurements','Reports']);
});

test('connection consent never fabricates diet authority or survives revoked health access',()=>{
  const active=connectedClient360Configuration({profession:'OTHER',capabilities:[]},{
    connectionId:'connection-1',healthDataAuthorized:true,consentedScopes:['BIOMARKERS','MEASUREMENTS','DIET_PLAN'],
  });
  assert.equal(client360CapabilityState(active).dietPlan,false);
  const revoked=connectedClient360Configuration({profession:'OTHER',capabilities:[]},{
    connectionId:'connection-1',healthDataAuthorized:false,consentedScopes:['BIOMARKERS','MEASUREMENTS'],
  });
  assert.deepEqual(client360CapabilityState(revoked),{dietPlan:false,biomarkers:false,measurements:false});
});

test('unauthorised Care explains the backend capability requirement without mounting diet authoring',()=>{
  assert.match(component,/data-testid="diet-plan-unavailable"/);
  assert.match(component,/Client consent allows approved data access, but does not grant diet-authoring authority/);
  assert.match(component,/active === 'Diet Plan' && capabilityState\.dietPlan && <ExternalMultiDietPlan/);
});
