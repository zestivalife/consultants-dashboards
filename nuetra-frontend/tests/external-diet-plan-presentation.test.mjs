import assert from 'node:assert/strict';
import test from 'node:test';
import { externalDietOptionNutrition, externalDietOptionServing, externalDietOptionTitle, validateExternalDietOption } from '../lib/externalDietPlanPresentation.mjs';

const governedOption = {
  combinationId: 'combination-1',
  clientTitle: 'Poha + Curd',
  humanServingSummary: '1 bowl · 100 g',
  components: [
    { foodId: 'food-poha', foodDisplayNameSnapshot: 'Poha', servingDisplayNameSnapshot: '1 bowl' },
    { foodId: 'food-curd', foodDisplayNameSnapshot: 'Curd', servingDisplayNameSnapshot: '100 g' },
  ],
  nutrition: { kcal: 342, protein: 12.4, carbohydrate: 53.1, fat: 8.7 },
};

test('external presentation reads the governed Common Food snapshot contract', () => {
  assert.equal(externalDietOptionTitle(governedOption), 'Poha + Curd');
  assert.equal(externalDietOptionServing(governedOption), '1 bowl · 100 g');
  assert.deepEqual(externalDietOptionNutrition(governedOption), governedOption.nutrition);
  assert.deepEqual(validateExternalDietOption(governedOption).canonicalFoodIds, ['food-poha', 'food-curd']);
  assert.equal(validateExternalDietOption(governedOption).valid, true);
});

test('missing governed data never becomes a plausible placeholder or fabricated zero', () => {
  const presented = validateExternalDietOption({ combinationId: 'broken', components: [], nutrition: {} });
  assert.equal(presented.title, '');
  assert.equal(presented.nutrition.kcal, null);
  assert.equal(presented.valid, false);
});
