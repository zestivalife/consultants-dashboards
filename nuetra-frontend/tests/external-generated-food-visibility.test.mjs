import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { COMMON_FOOD_MEALS, governedGenerationCandidates, optionTitle } from '../lib/commonFoodUi.mjs';

const productionCompatibleResponse = {
  planVersionId: '34e27db1-adcb-4225-82a7-9a4b86942e11',
  meals: COMMON_FOOD_MEALS.map(([mealHead, label], mealIndex) => ({
    mealHead,
    options: Array.from({ length: 5 }, (_, optionIndex) => ({
      combinationId: `${mealHead}-${optionIndex + 1}`,
      mealHead,
      clientTitle: `${label} governed option ${optionIndex + 1}`,
      humanServingSummary: '1 governed portion',
      components: [{
        foodId: `FOOD-${mealIndex}-${optionIndex}`,
        servingId: `SERVING-${mealIndex}-${optionIndex}`,
        multiplier: 1,
        foodDisplayNameSnapshot: `${label} food ${optionIndex + 1}`,
        nutrition: { kcal: 100 + optionIndex, protein: 5, carbohydrate: 12, fat: 3, fibre: 2 },
      }],
      nutrition: { kcal: 100 + optionIndex, protein: 5, carbohydrate: 12, fat: 3, fibre: 2 },
    })),
  })),
};

test('production-compatible seven-meal response supplies 35 named selectable editor candidates', () => {
  const projection = governedGenerationCandidates(productionCompatibleResponse);
  assert.equal(projection.meals.length, 7);
  assert.equal(projection.options.length, 35);
  for (const [mealHead] of COMMON_FOOD_MEALS) {
    const options = projection.options.filter((option) => option.mealHead === mealHead);
    assert.equal(options.length, 5);
    for (const option of options) {
      assert.notEqual(optionTitle(option), 'Structured meal');
      assert.ok(option.components.every((component) => component.foodId && component.servingId));
      assert.ok(Number.isFinite(option.nutrition.kcal));
    }
  }
});

test('newly created draft requests generation once while existing empty and immutable plans remain explicit', async () => {
  const workspace = await readFile(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
  const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
  assert.match(workspace, /if \(loaded\.preferredLoaded\)[\s\S]*setGenerationRequest\(\{ planId: result\.id/);
  assert.match(workspace, /generationRequest\.planId === selected\.id/);
  assert.match(workspace, /onGenerationRequestHandled=\{handleGenerationRequestHandled\}/);
  assert.match(editor, /onGenerationRequestHandled\?\.\(generationRequestId\)/);
  assert.match(workspace, /generateMissingOnLoad=\{false\}/);
  assert.match(editor, /\['draft', 'changes_requested'\]\.includes\(lifecycle\)/);
});
