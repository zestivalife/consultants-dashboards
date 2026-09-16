import test from 'node:test';
import assert from 'node:assert/strict';
import { chooseRandomFive, chooseRecommendedFive, isExactSelection, mergeCandidateOptions, sameOptionIds, verifyPersistedSelection } from '../lib/commonFoodSelectionLifecycle.mjs';

const heads = ['a','b'];
const options = heads.flatMap((mealHead) => Array.from({ length: 7 }, (_, index) => ({ combinationId: `${mealHead}${index}`, mealHead })));

test('candidate refresh retains saved options without changing selection truth', () => {
  const merged = mergeCandidateOptions(options.slice(0, 3), options);
  assert.equal(merged.length, 14);
  assert.deepEqual(merged.slice(0, 3).map((item) => item.combinationId), options.slice(0, 3).map((item) => item.combinationId));
});

test('random five are unique and meal-local', () => {
  const selected = chooseRandomFive(options.filter((item) => item.mealHead === 'a'), () => 0.4);
  assert.equal(selected.length, 5);
  assert.equal(new Set(selected).size, 5);
  assert.ok(selected.every((id) => id.startsWith('a')));
});

test('recommended five only uses the backend-approved ranking', () => {
  const meal = options.filter((item) => item.mealHead === 'a');
  assert.deepEqual(chooseRecommendedFive(meal), []);
  assert.deepEqual(chooseRecommendedFive(meal, ['a6', 'a3', 'a1', 'a5', 'a2']), ['a6', 'a3', 'a1', 'a5', 'a2']);
});

test('verified saved state requires exact IDs, version, and five per meal', () => {
  const persisted = options.filter((item) => Number(item.combinationId.slice(1)) < 5);
  const requested = new Set(persisted.map((item) => item.combinationId));
  assert.equal(isExactSelection(persisted, requested, heads), true);
  assert.equal(verifyPersistedSelection({ requestedIds: requested, responseOptions: persisted, expectedPlanVersionId: 'v1', responsePlanVersionId: 'v1', mealHeads: heads }), true);
  assert.equal(verifyPersistedSelection({ requestedIds: requested, responseOptions: persisted.slice(1), expectedPlanVersionId: 'v1', responsePlanVersionId: 'v1', mealHeads: heads }), false);
  assert.equal(verifyPersistedSelection({ requestedIds: requested, responseOptions: persisted, expectedPlanVersionId: 'v1', responsePlanVersionId: 'v2', mealHeads: heads }), false);
  assert.equal(sameOptionIds(requested, new Set([...requested].reverse())), true);
});
