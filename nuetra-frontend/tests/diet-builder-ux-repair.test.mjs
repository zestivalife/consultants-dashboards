import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');

test('generation includes five choices for every meal by default', () => {
  assert.match(editor, /COMMON_FOOD_MEALS\.forEach/);
  assert.match(editor, /slice\(0, 5\)\.forEach/);
  assert.match(editor, /Generated options are included by default/);
  assert.match(editor, /Select all/);
  assert.match(editor, />Clear</);
});

test('compact cards expose serving, all macros and advisory calorie equivalence', () => {
  for (const text of ['Serving:', 'Fibre', 'Acceptable range', 'Within target', 'Below target', 'Above target', 'Remaining']) assert.ok(editor.includes(text), text);
  assert.match(editor, /target \* 0\.95/);
  assert.match(editor, /target \* 1\.05/);
  assert.match(editor, /variancePercent < -5/);
  assert.match(editor, /variancePercent > 5/);
  assert.doesNotMatch(editor, /FITEATSY-CALORIE-MACRO-ALLOCATION-CONTRACT-v1/);
});

test('Build Meal supports all slots and independent multi-option application', () => {
  for (const text of ['Staple', 'Protein / Pulse', 'Vegetable', 'Accompaniment', 'Optional Extra', 'This option', 'Selected options', 'All 5 options']) assert.ok(editor.includes(text), text);
  assert.match(editor, /for \(const optionId of targets\)/);
  assert.match(editor, /addFiteatsyCommonFoodComponent[\s\S]*optionId/);
  assert.match(editor, /Component added independently/);
  assert.match(editor, /Edit quantity/);
});

test('Nutrition workspace is compact and optional guidance is calorie-isolated', () => {
  for (const text of ['View Health Context', '35 persisted', 'guidance choices', 'Optional choices are not included in the prescribed daily calorie total unless added to the Diet Plan.']) assert.ok(workspace.includes(text), text);
  for (const text of ['Chinese', 'North Indian', 'South Indian', 'Continental', 'Indian Fast Food', 'Street Food', 'Café / Bakery', 'Other', 'Sweet', 'Salty', 'Spicy', 'Crunchy']) assert.ok(workspace.includes(text), text);
  assert.doesNotMatch(workspace, /Eating Out · \$\{key/);
  assert.doesNotMatch(workspace, /Prescribed plan option.*Verified catalogue/);
});

test('manual food access remains permissive and search remains compact', () => {
  assert.match(editor, /All Foods &amp; Dishes/);
  assert.match(editor, /Search bhindi, okra, lauki, ragi/);
  assert.match(editor, /primaryActionEnabled/);
  assert.doesNotMatch(editor, /disabled=.*generatorEligible/);
});

test('component mutations remain unsaved until the authoritative 35-selection replacement succeeds', () => {
  assert.match(editor, /Option updated and recalculated by Fiteatsy\. Save the Diet Plan to persist the complete selection\./);
  assert.match(editor, /Component added independently to \$\{updated\.length\} meal options\. Save the Diet Plan to persist the complete selection\./);
  assert.match(editor, /replaceFiteatsyCommonFoodSelection/);
  assert.match(editor, /setOptions\(persisted\); setSelectedIds\(nextIds\); setPersistedIds\(nextIds\); setDirty\(false\)/);
  assert.doesNotMatch(editor, /Option updated and recalculated by Fiteatsy\.['"]\); \}\s*catch/);
});

test('legacy partial drafts keep persisted selection truth separate from generated candidates', () => {
  assert.match(editor, /generate\(\{ autoSelect: false, baseOptions: savedOptions, selectedSeed: savedIds \}\)/);
  assert.match(editor, /if \(!autoSelect\) return new Set/);
  assert.match(editor, /Incomplete saved draft: \$\{savedOptions\.length\}\/35 persisted/);
  assert.match(editor, /Missing candidates loaded\. Existing saved selections were preserved/);
  assert.match(editor, /persistedTotal/);
  assert.match(editor, /persistedByMeal/);
});

test('review readiness and saved labels use authoritative persisted mappings', () => {
  assert.match(workspace, /persistedDietOptionCount/);
  assert.match(workspace, /effectiveCommonFoodDirty \|\| persistedDietOptionCount !== 35/);
  assert.match(workspace, /generated candidates are not saved selections/);
  assert.match(workspace, /persisted selections remaining before review/);
  assert.doesNotMatch(workspace, /disabled=\{nutritionActionLoading \|\| commonFoodDirty \|\| selectedDietOptionCount !== 35/);
});
