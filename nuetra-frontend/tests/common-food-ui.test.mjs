import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { COMMON_FOOD_ERROR_MESSAGES, COMMON_FOOD_MEALS, formatNutrient, optionSummary } from '../lib/commonFoodUi.mjs';

const api = await readFile(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');

test('renders the exact seven governed meal heads', () => {
  assert.deepEqual(COMMON_FOOD_MEALS.map(([key]) => key), ['EARLY_MORNING', 'BREAKFAST', 'MID_MORNING', 'LUNCH', 'EVENING_SNACK', 'DINNER', 'BEDTIME']);
});

test('preserves unknown nutrient semantics', () => {
  assert.equal(formatNutrient(null), 'Not reported');
  assert.equal(formatNutrient(0), '0 g');
});

test('summarises a component-rich option without calling it a recipe', () => {
  const value = optionSummary({ components: [{ label: '2 × piece', foodDisplayNameSnapshot: 'Chapati' }, { label: '1 × katori', foodDisplayNameSnapshot: 'Curd' }] });
  assert.equal(value, '2 × piece Chapati · 1 × katori Curd');
  assert.doesNotMatch(value, /recipe/i);
});

test('maps safety, vegan and stale errors', () => {
  for (const code of ['ALLERGY_CONFLICT', 'INTOLERANCE_CONFLICT', 'HARD_AVOID_CONFLICT', 'DIET_PATTERN_CONFLICT', 'SERVING_INVALID', 'SERVING_NOT_FOUND', 'UNSAFE_OR_INELIGIBLE_FOOD', 'STALE_PLAN_VERSION', 'VEGAN_COMMON_FOOD_ENGINE_V1_NOT_SUPPORTED']) assert.ok(COMMON_FOOD_ERROR_MESSAGES[code]);
});

test('API client uses every accepted backend common-food route', () => {
  for (const fragment of ['/common-foods', '/common-food/generate', '/common-food/options', '/components/', '/serving']) assert.match(api, new RegExp(fragment.replaceAll('/', '\\/')));
  assert.doesNotMatch(api, /Math\.random/);
  assert.match(api, /\/v1\/consultants\/clients\/\$\{encodeURIComponent\(clientId\)\}/);
  assert.doesNotMatch(api, /\/v1\/consultants\/nutrition\/clients/);
});

test('single Diet Plan editor provides requested generation, shortage, explorer and all mutations', () => {
  for (const fragment of ['generationRequestId', 'of 5 valid options available', 'Food Explorer', 'Replace', 'Add food', 'Remove', 'Serving', 'Reload latest', 'Meal navigator']) assert.ok(editor.includes(fragment), fragment);
  assert.doesNotMatch(editor, /Generate 7×5|Common-food combinations|Common-food meal combinations/);
});

test('catalogue search is debounced, cancellable and paginated', () => {
  assert.match(editor, /setTimeout\([\s\S]*300/);
  assert.match(editor, /AbortController/);
  assert.match(editor, /hasMore/);
});

test('authoritative nutrition is never summed in the UI', () => {
  assert.doesNotMatch(editor, /reduce\([^)]*(kcal|protein|carbohydrate|fat|fibre)/);
  assert.match(editor, /updated and recalculated by Fiteatsy/);
});

test('common-food and rollback editors are mutually exclusive', async () => {
  const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
  assert.match(workspace, /CommonFoodPlanEditor/);
  assert.match(workspace, /commonFoodPlanActive/);
  assert.doesNotMatch(workspace, /Legacy Meal Plan Editor|Generate 7×5/);
  assert.match(workspace, /Generate Diet Plan/);
  assert.match(workspace, /commonFoodEditorRef\.current\?\.save/);
  assert.match(workspace, /commonFoodOptions/);
});
