import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
const workspace = await readFile(new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url), 'utf8');
const api = await readFile(new URL('../lib/fiteatsyConsultantsApi.js', import.meta.url), 'utf8');

test('Senior Consultant review renders the submitted version snapshot without authoring access', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.ok(reviewStart > -1 && reviewEnd > reviewStart);
  assert.match(reviewPage, /listFiteatsyDietPlanReviews/);
  assert.match(reviewPage, /initialOptions=\{review\.version\.commonFoodOptions\}/);
  assert.match(reviewPage, /legacyMealPlan=\{review\.version\?\.content\?\.mealPlan\}/);
  assert.match(reviewPage, /mode="senior-review"/);
  assert.match(reviewPage, /<CommonFoodPlanEditor[\s\S]*readOnly/);
  assert.doesNotMatch(reviewPage, /readFiteatsyCommonFoodOptions/);
});

test('Senior review mode suppresses Consultant authoring controls and permission errors', () => {
  assert.match(editor, /const isSeniorReview = mode === 'senior-review'/);
  assert.match(editor, /!readOnly && !isSeniorReview \? <button[\s\S]*Generate alternatives[\s\S]*: null/);
  assert.match(editor, /!readOnly && !isSeniorReview && error \? <p role="alert"/);

  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.doesNotMatch(reviewPage, />Save</);
  assert.doesNotMatch(reviewPage, />Edit</);
  assert.doesNotMatch(reviewPage, />Publish</);
  assert.match(reviewPage, /'Request Changes'/);
  assert.match(reviewPage, /'Approve'/);
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

  assert.match(reviewPage, /approveFiteatsySeniorDietPlanReview\(review\.dietPlanId, review\.version\.id\)/);
  assert.match(reviewPage, /requestFiteatsySeniorDietPlanReviewChanges\(review\.dietPlanId, review\.version\.id/);
  assert.doesNotMatch(reviewPage, /publishFiteatsyConsultantDietPlan/);
  assert.doesNotMatch(reviewPage, /generateFiteatsyCommonFoodPlan/);
  assert.doesNotMatch(reviewPage, /approveFiteatsyConsultantDietPlan\(/);
  assert.match(api, /\/v1\/consultants\/diet-plan-reviews\/\$\{encodeURIComponent\(dietPlanId\)\}\/approve/);
  assert.match(api, /body: \{ versionId \}/);
});

test('Senior review mutations are single-flight, clear stale errors, refetch, and expose completion state', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.match(reviewPage, /const \[pendingAction, setPendingAction\] = useState\(null\)/);
  assert.match(reviewPage, /if \(pendingAction\) return/);
  assert.match(reviewPage, /setError\(''\)/);
  assert.match(reviewPage, /await approveFiteatsySeniorDietPlanReview[\s\S]*await refresh\(\)[\s\S]*setSuccess\('Diet plan approved/);
  assert.match(reviewPage, /await requestFiteatsySeniorDietPlanReviewChanges[\s\S]*await refresh\(\)[\s\S]*setSuccess\('Changes requested/);
  assert.match(reviewPage, /disabled=\{pendingAction !== null\}/);
  assert.match(reviewPage, /aria-busy=\{pendingAction === `approve:\$\{review\.dietPlanId\}`\}/);
  assert.match(reviewPage, /aria-busy=\{pendingAction === `changes:\$\{review\.dietPlanId\}`\}/);
  assert.match(reviewPage, /role="status"/);
});

test('Diet Plan Review does not auto-load the separate Food Proposal review workflow', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.match(reviewPage, /const \[foodProposalReviewOpen, setFoodProposalReviewOpen\] = useState\(false\)/);
  assert.match(reviewPage, /aria-expanded=\{foodProposalReviewOpen\}/);
  assert.match(reviewPage, /foodProposalReviewOpen \? <SeniorFoodProposalReviewPanel \/> : null/);
  assert.doesNotMatch(reviewPage, /^\s*<SeniorFoodProposalReviewPanel \/>\s*$/m);
});

test('Senior review full workspace mount does not run or render Consultant-only operations bootstrap', () => {
  const workspaceStart = workspace.indexOf('function PlatformWorkspace({ forcedRole })');
  const workspacePage = workspace.slice(workspaceStart);

  assert.ok(workspaceStart > -1);
  assert.match(workspacePage, /const isSeniorConsultant = String\(resolvedRole\)\.toLowerCase\(\) === 'senior_consultant'/);
  assert.match(workspacePage, /if \(roleKind !== 'consultant' \|\| isSeniorConsultant\) return;[\s\S]*listFiteatsyConsultantOperations\(\)[\s\S]*getFiteatsyConsultantAvailability\(\)/);
  assert.match(workspacePage, /\}, \[isSeniorConsultant, roleKind\]\);/);
  assert.match(workspacePage, /roleKind === 'consultant' && !isSeniorConsultant && consultantOperationsError/);
  assert.match(workspacePage, /isSeniorConsultant && nav === 'diet-plan-reviews'[\s\S]*<DietPlanReviewQueuePage \/>/);
});

test('Senior review page load is single-flight under Strict Mode and cannot retain a competing assignment error', () => {
  const reviewStart = workspace.indexOf('function DietPlanReviewQueuePage()');
  const reviewEnd = workspace.indexOf('function ConsultantOperationalOverview', reviewStart);
  const reviewPage = workspace.slice(reviewStart, reviewEnd);

  assert.match(reviewPage, /const initialRefreshStartedRef = useRef\(false\)/);
  assert.match(reviewPage, /const refreshInFlightRef = useRef\(null\)/);
  assert.match(reviewPage, /if \(refreshInFlightRef\.current\) return refreshInFlightRef\.current/);
  assert.match(reviewPage, /refreshInFlightRef\.current = request/);
  assert.match(reviewPage, /refreshInFlightRef\.current = null/);
  assert.match(reviewPage, /if \(initialRefreshStartedRef\.current\) return/);
  assert.match(reviewPage, /initialRefreshStartedRef\.current = true/);
  assert.match(reviewPage, /void refresh\(\)\.catch\(\(\) => undefined\)/);
  assert.doesNotMatch(reviewPage, /useEffect\(\(\) => \{ void refresh\(\); \}, \[refresh\]\)/);
});
