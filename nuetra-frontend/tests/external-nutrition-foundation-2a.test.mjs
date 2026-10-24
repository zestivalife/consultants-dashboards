import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const internal=readFileSync(new URL('../components/platform/InternalClientProfileEnrichmentPanel.jsx',import.meta.url),'utf8');

test('Phase 2A exposes only External Practice Operations assessment and lineage contracts',()=>{
  for(const name of ['getNutritionAssessment','createNutritionAssessment','reviewNutritionAssessment','markNutritionAssessmentStale','bindDietPlanAssessment','saveClinicalDocumentLineage','listClinicalDocumentLineage'])assert.match(api,new RegExp(`export function ${name}`));
  assert.match(api,/\/clients\/\$\{encodeURIComponent\(clientId\)\}\/nutrition-assessment/);
});

test('Phase 2A does not alter the frozen Internal Client Profile component',()=>{
  assert.ok(internal.includes('InternalClientProfileEnrichmentPanel'));
  assert.doesNotMatch(internal,/NutritionAssessment|diet-plan-assessment-links|clinical-document-links/);
});
