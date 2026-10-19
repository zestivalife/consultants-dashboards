import test from 'node:test';
import assert from 'node:assert/strict';
import { client360CapabilityState, resolveClient360Tabs } from '../lib/client360Capabilities.mjs';

for (const profession of ['DIETITIAN','NUTRITIONIST','CLINICAL_NUTRITIONIST','SPORTS_NUTRITIONIST']) {
  test(`${profession} exposes governed nutrition Client360 modules`, () => {
    const tabs=resolveClient360Tabs({profession,capabilities:['DIET_PLAN','BIOMARKERS','MEASUREMENTS']});
    for(const required of ['Overview','Health Profile','Health Records','Nutrition','Diet Plan','Measurements','Reports','Biomarkers','Goals / Progress','Timeline','Documents','Resources & Homework']) assert.ok(tabs.includes(required),required);
  });
}

test('Diet Plan is not globally exposed',()=>{
  const tabs=resolveClient360Tabs({profession:'PSYCHOLOGIST',professionWorkspace:true,capabilities:['CONSULTATIONS','GOALS_PROGRESS']});
  assert.equal(tabs.includes('Diet Plan'),false);
  assert.equal(tabs.includes('Biomarkers'),true);
});

test('registry-controlled Diabetes Educator capabilities are respected',()=>{
  const enabled=client360CapabilityState({profession:'DIABETES_EDUCATOR',capabilities:['BIOMARKERS','DIET_PLAN_AUTHORING']});
  assert.deepEqual(enabled,{dietPlan:true,biomarkers:true,measurements:false});
});
