import assert from 'node:assert/strict';
import test from 'node:test';
import {calculateCalendarAge,composeExternalClientProfile,measurementValues} from '../lib/externalClientProfile.mjs';

test('calendar age is date-based and future dates stay unavailable',()=>{
  assert.equal(calculateCalendarAge('2000-10-25',new Date('2026-10-24T00:00:00Z')),25);
  assert.equal(calculateCalendarAge('2000-10-24',new Date('2026-10-24T00:00:00Z')),26);
  assert.equal(calculateCalendarAge('2027-01-01',new Date('2026-10-24T00:00:00Z')),null);
});

test('measurement projection composes authoritative latest values and derivations',()=>{
  const projection={latest:{HEIGHT_CM:{value:170},WEIGHT_KG:{value:68},WAIST_CM:{value:80}},calculations:{bmi:{value:23.5,methodology:'bmi.metric.v1'}}};
  assert.deepEqual(measurementValues(projection),{height:170,heightCm:170,weight:68,weightKg:68,waistCm:80});
  const result=composeExternalClientProfile({overview:{primaryContact:'demo@example.invalid'},sections:{}},{date_of_birth:'2000-10-24'},projection);
  assert.equal(result.sections.measurements.weightKg,68);
  assert.equal(result.derived.bmi.value,23.5);
  assert.equal(result.derived.bmi.methodology,'bmi.metric.v1');
});

test('completeness exposes missing checklist and does not count absent clinical evidence',()=>{
  const result=composeExternalClientProfile({overview:{primaryContact:'demo@example.invalid'},sections:{}},{},{});
  assert.ok(result.overview.profileCompleteness<100);
  assert.ok(result.overview.completeness.missingChecklist.some(item=>item.label==='Date of birth'));
  assert.equal(result.overview.completeness.clinicalEvidenceOptional,true);
});
