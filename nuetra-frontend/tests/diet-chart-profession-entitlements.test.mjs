import test from 'node:test';
import assert from 'node:assert/strict';
import { client360CapabilityState, resolveClient360Navigation } from '../lib/client360Capabilities.mjs';

const enabled = ['DIETITIAN_NUTRITIONIST','HEALTH_COACH','WELLNESS_COACH','FITNESS_TRAINER','DIABETES_EDUCATOR','WOMENS_HEALTH_PRACTITIONER','LIFESTYLE_MEDICINE_PRACTITIONER','DOCTOR_PHYSICIAN','WELLNESS_CONSULTANT'];
const optional = ['PHYSIOTHERAPIST','YOGA_MEDITATION_COACH','OTHER'];
const disabled = ['PSYCHOLOGIST','COUNSELLOR','MENTOR','BEHAVIOURAL_THERAPIST','OCCUPATIONAL_THERAPIST','MENTAL_WELLNESS_THERAPIST'];

test('all approved enabled registration professions render Diet Plan from backend capability', () => {
  for (const profession of enabled) {
    const configuration = { profession, diet_chart_eligibility: 'ENABLED', capabilities: ['DIET_PLAN'] };
    assert.equal(client360CapabilityState(configuration).dietPlan, true, profession);
    assert.ok(resolveClient360Navigation(configuration).find(section => section.id === 'care').modules.includes('Diet Plan'), profession);
  }
});

test('optional professions require and immediately reflect explicit entitlement', () => {
  for (const profession of optional) {
    const denied = { profession, diet_chart_eligibility: 'OPTIONAL', capabilities: [] };
    assert.equal(client360CapabilityState(denied).dietPlan, false, profession);
    assert.equal(client360CapabilityState(denied).dietPlanEntitlementRequired, true, profession);
    const granted = { ...denied, capabilities: ['DIET_PLAN'] };
    assert.equal(client360CapabilityState(granted).dietPlan, true, profession);
    assert.equal(client360CapabilityState({ ...granted, capabilities: [] }).dietPlan, false, profession);
  }
});

test('disabled professions are not advertised when backend denies capability', () => {
  for (const profession of disabled) {
    const configuration = { profession, diet_chart_eligibility: 'DISABLED', capabilities: [] };
    const state = client360CapabilityState(configuration);
    assert.equal(state.dietPlan, false, profession);
    assert.equal(state.dietPlanEntitlementRequired, false, profession);
    assert.ok(!resolveClient360Navigation(configuration).find(section => section.id === 'care').modules.includes('Diet Plan'), profession);
  }
});

test('External Consultant assignment authority bypasses only profession eligibility presentation', () => {
  const configuration = { profession: 'OTHER', diet_chart_eligibility: 'DISABLED', capabilities: [] };
  assert.equal(client360CapabilityState(configuration).dietPlan, false);
  const external = client360CapabilityState(configuration, { externalConsultant: true });
  assert.equal(external.dietPlan, true);
  assert.equal(external.dietPlanEntitlementRequired, false);
  assert.ok(resolveClient360Navigation(configuration, { externalConsultant: true }).find(section => section.id === 'care').modules.includes('Diet Plan'));
});
