import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { buildMealAuthoringPool, previousOptionReuseState } from '../lib/commonFoodUi.mjs';

const component = (foodId) => ({ foodId, servingId: `serving-${foodId}`, multiplier: 1 });
const option = (id, source = 'generated', extra = {}) => ({
  combinationId: id,
  displayName: id,
  mealHead: 'BREAKFAST',
  components: [component(id)],
  nutrition: { kcal: 200, protein: 10, carbohydrate: 20, fat: 5, fibre: 3 },
  optionHash: `${source}-${id}`,
  ...extra,
});

test('zero generated plus five governed previous options exposes five reusable options', () => {
  const pool = buildMealAuthoringPool([], Array.from({ length: 5 }, (_, index) => option(`previous-${index}`)));
  assert.equal(pool.length, 5);
  assert.ok(pool.every((item) => item.authoringSource === 'PREVIOUS_PLAN'));
});

test('two generated plus three previous options yields five active authoring choices', () => {
  const pool = buildMealAuthoringPool([option('generated-1'), option('generated-2')], [option('previous-1'), option('previous-2'), option('previous-3')]);
  assert.equal(pool.length, 5);
  assert.deepEqual(pool.map((item) => item.authoringSource), ['GENERATED', 'GENERATED', 'PREVIOUS_PLAN', 'PREVIOUS_PLAN', 'PREVIOUS_PLAN']);
});

test('semantic duplicates do not consume authoring slots', () => {
  const current = option('generated', 'generated', { components: [component('same-food')] });
  const previous = option('previous', 'previous', { components: [component('same-food')] });
  assert.equal(buildMealAuthoringPool([current], [previous]).length, 1);
});

test('unsafe, corrupt, or unmapped historical choices remain visible but are not reusable', () => {
  assert.equal(previousOptionReuseState(option('allergy', 'previous', { hardConstraintViolation: 'ALLERGY' })).reusable, false);
  assert.equal(previousOptionReuseState(option('corrupt', 'previous', { corrupt: true })).reusable, false);
  assert.equal(previousOptionReuseState(option('unmapped', 'previous', { components: [] })).reusable, false);
});

test('ranking and diversity metadata never block governed previous-option reuse', () => {
  const previous = option('low-rank', 'previous', { overallScore: -999, rankingState: 'DIVERSITY_REJECTED' });
  assert.equal(previousOptionReuseState(previous).reusable, true);
});

test('editor exposes empty-slot authoring, inline previous reuse, preservation, and atomic save paths', async () => {
  const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
  for (const contract of [
    "explorer.mode === 'create'",
    'saveFiteatsyCommonFoodOption',
    'Previous plan options available now',
    '+ Add Food',
    '+ Build Meal',
    'Generate alternatives',
    'buildMealAuthoringPool',
    'replaceFiteatsyCommonFoodSelection',
    'retainedSelection',
    '35 persisted',
  ]) assert.ok(editor.includes(contract), contract);
  assert.ok(!editor.includes('Only ${coverage.available || 0} suitable options are available for this meal.'));
});
