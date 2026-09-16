import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const api = await readFile(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');

test('Diet foods retain exact meal, option, component, food and serving association', () => {
  assert.match(editor, /mealHead: option\.mealHead/);
  assert.match(editor, /optionId/);
  assert.match(editor, /combinationId/);
  assert.match(editor, /foodId, servingId, multiplier/);
  assert.match(editor, /for \(const optionId of targets\)/);
  assert.match(editor, /Component added independently/);
});

test('Apply This, Selected and All 5 retain independent mutation paths', () => {
  for (const label of ['This option', 'Selected options', 'All 5 options', 'Edit quantity']) assert.ok(editor.includes(label), label);
  assert.match(editor, /addFiteatsyCommonFoodComponent\(clientId, dietPlanId, optionId/);
  assert.match(editor, /updateFiteatsyCommonFoodServing\(clientId, dietPlanId, explorer\.option\.combinationId/);
});

test('all three guidance sections and governed categories remain first-class', () => {
  for (const label of ['What Can I Eat Now?', 'Eating Out', 'Cravings', 'Chinese', 'North Indian', 'South Indian', 'Continental', 'Indian Fast Food', 'Street Food', 'Café / Bakery', 'Other', 'Sweet', 'Salty', 'Spicy', 'Crunchy']) assert.ok(workspace.includes(label), label);
});

test('guidance loads full category candidates and preserves category-scoped search', () => {
  assert.match(workspace, /void onSearch\(path, searches\[label\] \|\| ''\)/);
  assert.match(workspace, /available · \{enabledCount\} included/);
  assert.match(workspace, /candidates\[label\]\.map/);
  assert.match(api, /optional-guidance\/candidates/);
  assert.match(api, /category, context/);
});

test('primary guidance UI is calorie-isolated and contains no contract identifier', () => {
  assert.match(workspace, /Optional choices are not included in the prescribed daily calorie total unless added to the Diet Plan/);
  assert.doesNotMatch(workspace, /FITEATSY-CALORIE-MACRO-ALLOCATION-CONTRACT-v1/);
});
