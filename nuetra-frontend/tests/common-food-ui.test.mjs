import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { COMMON_FOOD_ERROR_MESSAGES, COMMON_FOOD_MEALS, commonFoodOptionType, formatNutrient, legacyOptionsForUnifiedPlan, optionSummary, optionTitle } from '../lib/commonFoodUi.mjs';

const api = await readFile(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');
const featureFlags = await readFile(new URL('../lib/dietFeatureFlags.js', import.meta.url), 'utf8');
const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');

test('renders the exact seven governed meal heads', () => {
  assert.deepEqual(COMMON_FOOD_MEALS.map(([key]) => key), ['EARLY_MORNING', 'BREAKFAST', 'MID_MORNING', 'LUNCH', 'EVENING_SNACK', 'DINNER', 'BEDTIME']);
});

test('preserves unknown nutrient semantics', () => {
  assert.equal(formatNutrient(null), 'Not reported');
  assert.equal(formatNutrient(0), '0 g');
  assert.equal(formatNutrient(0.21999999999999997), '0.2 g');
  assert.equal(formatNutrient(164.94, 'kcal'), '164.9 kcal');
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
  assert.match(api, /method: 'PUT'/);
});

test('single Diet Plan editor provides requested generation, shortage, explorer and all mutations', () => {
  for (const fragment of ['generationRequestId', 'available', 'Food Explorer', 'Replace', 'Add food', 'Remove', 'Serving', 'Reload latest', 'Meal navigator']) assert.ok(editor.includes(fragment), fragment);
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

test('all editable plans use one unified editor without the legacy fallback', async () => {
  const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
  assert.match(workspace, /CommonFoodPlanEditor/);
  assert.doesNotMatch(workspace, /COMMON_FOOD_COMBINATION_ENGINE_V1_ENABLED/);
  assert.match(workspace, /isCommonFoodCombinationEngineEnabled/);
  assert.doesNotMatch(workspace, /No verified meal-library matches|Select recommended 5|commonFoodPlanActive \?/);
  assert.doesNotMatch(workspace, /Legacy Meal Plan Editor|Generate 7×5/);
  assert.match(workspace, /Generate Diet Plan/);
  assert.match(workspace, /commonFoodEditorRef\.current\?\.save/);
  assert.match(workspace, /commonFoodOptions/);
});

test('one build-time feature flag source fails safely without undeclared globals', () => {
  assert.match(featureFlags, /process\.env\.NEXT_PUBLIC_COMMON_FOOD_COMBINATION_ENGINE_V1/);
  assert.match(featureFlags, /COMMON_FOOD_FLAG !== 'false'/);
  assert.doesNotMatch(editor, /process\.env\.NEXT_PUBLIC_COMMON_FOOD_COMBINATION_ENGINE_V1|COMMON_FOOD_COMBINATION_ENGINE_V1_ENABLED/);
  assert.match(editor, /savedOptions\.length < 35/);
  assert.match(editor, /await generate\(\)/);
});

test('legacy, validated recipe and generated combination normalize into one editor without identity collisions', () => {
  const legacy = legacyOptionsForUnifiedPlan({ breakfast: { options: [{ id: 'legacy-1', meal: 'Vegetable upma', portion: '1 katori', approxKcal: 240, proteinGrams: 7 }] } });
  const recipe = { combinationId: 'recipe-1', mealHead: 'BREAKFAST', sourceType: 'VALIDATED_RECIPE', components: [] };
  const generated = { combinationId: 'generated-1', mealHead: 'BREAKFAST', components: [{ sourceType: 'COMMON_FOOD' }] };
  const mixed = [...legacy, { ...recipe, sourceType: commonFoodOptionType(recipe) }, { ...generated, sourceType: commonFoodOptionType(generated) }];
  assert.deepEqual(mixed.map((option) => option.sourceType), ['LEGACY', 'VALIDATED_RECIPE', 'GENERATED_COMBINATION']);
  assert.equal(new Set(mixed.map((option) => option.combinationId)).size, 3);
  assert.equal(legacy[0].nutrition.kcal, 240);
});

test('mixed-plan compatibility is rendered inside the existing Diet Plan surface', () => {
  for (const fragment of ['legacyMealPlan', 'legacyOptionsForUnifiedPlan', 'Legacy option', 'data-option-type']) assert.ok(editor.includes(fragment), fragment);
});

test('generated candidates require an explicit exact-five selection before persistence', () => {
  for (const fragment of ['AVAILABLE', 'SELECTED', 'SAVED', 'selectedIds', 'Select exactly five options for every meal', 'data-selection-state']) assert.ok(editor.includes(fragment), fragment);
  assert.match(editor, /selected\.filter\(\(option\) => option\.mealHead === head\)\.length !== 5/);
  assert.match(editor, /replaceFiteatsyCommonFoodSelection/);
  assert.match(editor, /options: selected\.map/);
  assert.match(editor, /useImperativeHandle[\s\S]*selectedIds/);
});

test('semantic meal UX leads with client-ready titles, human servings, progress and truthful shortage', () => {
  assert.equal(optionTitle({ clientTitle: 'Chapati + Moong Dal + Bhindi Sabji + Curd' }), 'Chapati + Moong Dal + Bhindi Sabji + Curd');
  assert.equal(optionTitle({ clientTitle: 'Option 1' }), 'Structured meal');
  for (const fragment of ['35 selected', 'selections remaining', 'Preview as Client', 'Build Meal', 'No suitable options are available']) assert.ok(editor.includes(fragment), fragment);
  assert.doesNotMatch(editor, /<p className="text-sm font-semibold">Option \{index \+ 1\}<\/p>/);
  assert.match(editor, /optionTitle\(option\)/);
});

test('v17.22 uses compact progressive-disclosure cards and a client-only preview', () => {
  for (const fragment of ['Structured meal components', 'exact equivalent', 'Choose any one', 'never the candidate pool', 'Good calorie fit', 'Good protein fit']) assert.ok(editor.includes(fragment), fragment);
  assert.match(editor, /aria-expanded/);
  assert.match(editor, /ClientPreview/);
});

test('v17.22 exposes role-safe component editing, locks and auto-balance', () => {
  for (const fragment of ['Edit Meal', 'Adjust serving', 'Keep this serving fixed during Auto-Balance', 'Auto-Balance', '+ Build Meal']) assert.ok(editor.includes(fragment), fragment);
  assert.match(editor, /componentRole\(component\)/);
  assert.match(editor, /lockedFoodIds/);
});

test('v17.22 progress and shortage language are explicit and accessible', () => {
  for (const fragment of ['selections remaining', 'All seven meals are complete', 'selected', 'source-governance requirements', 'aria-live="assertive"']) assert.ok(editor.includes(fragment), fragment);
  assert.doesNotMatch(editor, />Generated combination</);
});

test('v17.22 workspace separates workflow stages and removes noisy guidance controls', async () => {
  const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
  for (const fragment of ["'Diet Plan', 'Optional Guidance', 'Review & Submit'", 'Download Active Plan', 'Plan readiness', 'Add Recommended', 'Select up to 5', 'Feedback applies to', 'Publish to Client']) assert.ok(workspace.includes(fragment), fragment);
  assert.doesNotMatch(workspace, /Select all eligible/);
  assert.doesNotMatch(workspace, />Move up</);
});

test('v17.23 explorer separates scope, uses serving nutrition and sends a governed draft snapshot', () => {
  assert.match(editor, /Recommended for \$\{context\.mealLabel\}/);
  assert.match(editor, /All eligible foods/);
  assert.match(editor, /food\.defaultServing\?\.nutrition/);
  assert.doesNotMatch(editor, /prefix="Per 100 g/);
  assert.match(editor, /const draft = \{ mealHead: explorer\.option\.mealHead/);
  assert.match(editor, /expectedPlanVersionId: planVersionId, draft, component/);
  assert.match(editor, /\['PULSE', 'Dal & pulses'\]/);
});
