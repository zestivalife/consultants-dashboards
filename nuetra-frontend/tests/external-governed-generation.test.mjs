import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

test('external Diet Chart generation uses the Practice Operations governed generator', async () => {
  const component = await readFile(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
  const api = await readFile(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');

  assert.match(component, /generateConsultantDietPlanOptions\(planId,mealHeads\)/);
  assert.match(api, /diet-plans\/\$\{encodeURIComponent\(planId\)\}\/generate-options/);
  assert.ok(!component.includes("queries=['breakfast'"), 'legacy query fan-out must not return');
  assert.ok(!component.includes('normalOption'), 'frontend must not synthesize governed option nutrition');
});

test('empty governed generation is an explicit failure rather than a successful empty plan', async () => {
  const component = await readFile(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
  assert.match(component, /GOVERNED_FOOD_GENERATION_EMPTY/);
  assert.match(component, /No eligible governed Indian foods were generated/);
});
