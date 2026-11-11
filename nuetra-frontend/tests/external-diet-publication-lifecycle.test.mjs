import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';
import { canPublishExternalDietVersion, externalDietEditorState } from '../lib/dietPlanWorkspaceState.mjs';

test('saved draft lifecycle remains editable without implicit generation', () => {
  assert.deepEqual(externalDietEditorState('DRAFT'), { lifecycle: 'draft', readOnly: false, generationRequestId: 0 });
  assert.deepEqual(externalDietEditorState('SAVED'), { lifecycle: 'draft', readOnly: false, generationRequestId: 0 });
  assert.deepEqual(externalDietEditorState('CHANGES_REQUESTED'), { lifecycle: 'changes_requested', readOnly: false, generationRequestId: 0 });
});

test('approved and published versions load as immutable persisted snapshots', () => {
  assert.deepEqual(externalDietEditorState('APPROVED'), { lifecycle: 'approved', readOnly: true, generationRequestId: 0 });
  assert.deepEqual(externalDietEditorState('PUBLISHED'), { lifecycle: 'published', readOnly: true, generationRequestId: 0 });
  assert.deepEqual(externalDietEditorState('ARCHIVED'), { lifecycle: 'published', readOnly: true, generationRequestId: 0 });
});

test('publication requires the exact approved version with no local edits', () => {
  assert.equal(canPublishExternalDietVersion({ status: 'APPROVED', dirty: false }), true);
  assert.equal(canPublishExternalDietVersion({ status: 'APPROVED', dirty: true }), false);
  assert.equal(canPublishExternalDietVersion({ status: 'SAVED', dirty: false }), false);
  assert.equal(canPublishExternalDietVersion({ status: 'PUBLISHED', dirty: false }), false);
});

test('external editor avoids implicit reload generation and only requests generation for a newly created draft', async () => {
  const workspace = await readFile(new URL('../components/external/ExternalMultiDietPlan.jsx', import.meta.url), 'utf8');
  const editor = await readFile(new URL('../components/platform/CommonFoodPlanEditor.jsx', import.meta.url), 'utf8');
  assert.match(workspace, /generationRequestId=\{generationRequest\.planId === selected\.id \? generationRequest\.id : editorState\.generationRequestId\}/);
  assert.match(workspace, /if \(loaded\.preferredLoaded\)[\s\S]*setGenerationRequest/);
  assert.match(workspace, /onGenerationRequestHandled=\{handleGenerationRequestHandled\}/);
  assert.match(workspace, /generateMissingOnLoad=\{false\}/);
  assert.doesNotMatch(workspace, /generationRequestId=\{1\}/);
  assert.match(editor, /generateMissingOnLoad && isCommonFoodCombinationEngineEnabled/);
  assert.match(editor, /Generate alternatives/);
  assert.match(editor, /Select at least one governed meal option before saving the Diet Plan/);
  assert.match(editor, /persistedPlanVersionId = response\?\.planVersionId/);
  assert.match(editor, /expectedPlanVersionId: persistedPlanVersionId/);
  assert.match(workspace, /onProgressChange=\{setEditorProgress\}/);
  assert.match(workspace, /!editorProgress\.canSave/);
  assert.match(editor, /currentPlanVersionId/);
  assert.match(editor, /setCurrentPlanVersionId\(persistedPlanVersionId\)/);
  assert.match(editor, /canSave: dirty && selectedTotal > 0/);
  assert.match(workspace, /action==='approve'&&editorDirty/);
  assert.match(workspace, /Add and save at least one governed meal option before approval/);
});
