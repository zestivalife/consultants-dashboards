import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { calculateBmi, calculateInternalProfileCompleteness, calculateWaistHipRatio, composeInternalClientProfile, formatDateOnlyDDMMYYYY } from '../lib/internalClientProfile.mjs';

test('DOB uses date-only DD/MM/YYYY formatting without timezone conversion', () => {
  assert.equal(formatDateOnlyDDMMYYYY('1990-01-31'), '31/01/1990');
  assert.equal(formatDateOnlyDDMMYYYY(null), 'Not available');
});

test('BMI and waist-to-hip ratio derive only from valid source measurements', () => {
  assert.equal(calculateBmi(170,70),24.2);
  assert.equal(calculateBmi(null,70),null);
  assert.equal(calculateWaistHipRatio(80,100),0.8);
});

test('composition is immutable, source-aware, preserves explicit clears, and feeds diet context', () => {
  const base={client:{dateOfBirth:'1990-01-31'},onboarding:{height:160,weight:60,medicalConditions:'Base'},reports:[{id:'r1'}]};
  const composed=composeInternalClientProfile(base,{version:2,goals:['Better sleep'],medical_history_narrative:'',measurements:{height_cm:170,weight_kg:70,waist_cm:80,hip_cm:100},health_record_dates:{r1:{report_date:'2026-10-01',confirmation_date:'2026-10-02'}},provenance:{source:'INTERNAL_ENRICHMENT'}});
  assert.equal(base.onboarding.height,160);
  assert.deepEqual(composed.onboarding.goals,['Better sleep']);
  assert.equal(composed.onboarding.medicalHistoryNarrative,'');
  assert.equal(composed.onboarding.weight,70);
  assert.equal(composed.bodyMetrics.bmi,24.2);
  assert.equal(composed.bodyMetrics.waistHipRatio,0.8);
  assert.equal(composed.reports[0].enrichmentDates.confirmation_date,'2026-10-02');
  assert.equal(composed.fieldProvenance.internalEnrichment.source,'INTERNAL_ENRICHMENT');
});

test('stale enrichment measurements do not replace newer base measurements', () => {
  const base={onboarding:{height:180,weight:80,updatedAtISO:'2026-10-22T12:00:00Z'}};
  const composed=composeInternalClientProfile(base,{measurements:{height_cm:160,weight_kg:50,recorded_at:'2026-10-21T12:00:00Z'}});
  assert.equal(composed.onboarding.height,180);
  assert.equal(composed.onboarding.weight,80);
});

test('profile completeness uses one deterministic eight-field contract', () => {
  assert.equal(calculateInternalProfileCompleteness({client:{dateOfBirth:'2000-01-01'},onboarding:{height:170,weight:70,goals:['g'],medicalHistoryNarrative:'n',sleepStressNarrative:'n',bodyComposition:{waistCm:80,hipCm:90}}}),100);
});

test('Internal UI exposes all ten persisted profile changes and avoids fabricated report dates', () => {
  const workspace=fs.readFileSync(new URL('../components/platform/PlatformWorkspace.jsx',import.meta.url),'utf8');
  const panel=fs.readFileSync(new URL('../components/platform/InternalClientProfileEnrichmentPanel.jsx',import.meta.url),'utf8');
  for (const marker of ['maximum 3','dob_display_format','height_cm','weight_kg','waist_cm','hip_cm','neck_cm','Medical History','Sleep & Stress','health_record_dates']) assert.match(panel,new RegExp(marker,'i'));
  assert.match(workspace,/composeInternalClientProfile/);
  assert.match(workspace,/Waist-to-hip ratio/);
  assert.match(workspace,/internalProfileCompleteness/);
  assert.doesNotMatch(workspace,/report\.reportDate \|\| report\.createdAt \|\| report\.uploadedAt/);
});
