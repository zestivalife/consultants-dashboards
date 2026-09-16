export const COMMON_FOOD_EDITOR_STATES = Object.freeze({
  IDLE: 'IDLE', GENERATING: 'GENERATING', DIRTY: 'DIRTY', SAVING: 'SAVING',
  SAVED_VERIFIED: 'SAVED_VERIFIED', SAVE_FAILED: 'SAVE_FAILED',
  STALE_VERSION: 'STALE_VERSION', RELOADING: 'RELOADING', SUBMITTING: 'SUBMITTING',
  SUBMIT_FAILED: 'SUBMIT_FAILED',
});

const ids = (values) => [...values].map(String).sort();
export const sameOptionIds = (left, right) => JSON.stringify(ids(left)) === JSON.stringify(ids(right));
export const countSelections = (options, selectedIds, mealHeads) => Object.fromEntries(
  mealHeads.map((head) => [head, options.filter((option) => option.mealHead === head && selectedIds.has(option.combinationId)).length]),
);
export const isExactSelection = (options, selectedIds, mealHeads) => {
  const counts = countSelections(options, selectedIds, mealHeads);
  return selectedIds.size === mealHeads.length * 5 && mealHeads.every((head) => counts[head] === 5);
};
export const mergeCandidateOptions = (current, incoming) => [...new Map(
  [...current, ...incoming].map((option) => [option.combinationId, option]),
).values()];
export const chooseRecommendedFive = (options, recommendedIds = []) => {
  const ordered = recommendedIds.map((id) => options.find((option) => option.combinationId === id)).filter(Boolean);
  return ordered.slice(0, 5).map((option) => option.combinationId);
};
export const chooseRandomFive = (options, random = Math.random) => {
  const pool = [...options];
  for (let index = pool.length - 1; index > 0; index -= 1) {
    const swap = Math.floor(random() * (index + 1));
    [pool[index], pool[swap]] = [pool[swap], pool[index]];
  }
  return pool.slice(0, 5).map((option) => option.combinationId);
};
export const verifyPersistedSelection = ({ requestedIds, responseOptions, expectedPlanVersionId, responsePlanVersionId, mealHeads }) => {
  const responseIds = new Set(responseOptions.map((option) => option.combinationId));
  return responsePlanVersionId === expectedPlanVersionId
    && isExactSelection(responseOptions, responseIds, mealHeads)
    && sameOptionIds(requestedIds, responseIds);
};
