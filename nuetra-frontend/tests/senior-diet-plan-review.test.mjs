import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');

test('Senior Consultant review renders the submitted version snapshot without authoring access', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.ok(reviewStart > -1 && reviewEnd > reviewStart);
  assert.match(reviewPage, /listFiteatsyDietPlanReviews/);
  assert.match(reviewPage, /initialOptions=\{review\.version\.commonFoodOptions\}/);
  assert.match(reviewPage, /legacyMealPlan=\{review\.version\?\.content\?\.mealPlan\}/);
  assert.match(reviewPage, /<CommonFoodPlanEditor[\s\S]*readOnly/);
  assert.doesNotMatch(reviewPage, /readFiteatsyCommonFoodOptions/);
});

test('read-only submitted snapshots never reload through the Consultant authoring endpoint', () => {
  assert.match(editor, /if \(!readOnly\) return;[\s\S]*setOptions\(submittedOptions\)/);
  assert.match(editor, /setSelectedIds\(submittedIds\)/);
  assert.match(editor, /setPersistedIds\(submittedIds\)/);

  assert.match(
    editor,
    /useEffect\(\(\) => \{\s*if \(!dietPlanId\) return;\s*if \(readOnly\) return;[\s\S]*?void reload\(\);\s*\}, \[dietPlanId, generate, generationRequestId, lifecycle, planVersionId, readOnly, reload\]\);/,
  );
});

test('Senior Consultant review actions remain separate from Consultant editing and publishing', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.match(reviewPage, /approveFiteatsyConsultantDietPlan/);
  assert.match(reviewPage, /requestFiteatsyConsultantDietPlanChanges/);
  assert.doesNotMatch(reviewPage, /publishFiteatsyConsultantDietPlan/);
  assert.doesNotMatch(reviewPage, /generateFiteatsyCommonFoodPlan/);
});
