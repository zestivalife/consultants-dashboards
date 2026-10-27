import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const workspace = await readFile(new URL('../components/external/ExternalSaaSWorkspace.jsx', import.meta.url), 'utf8');
const client360 = await readFile(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');

test('UI-2 client list keeps authoritative onboarding truth and existing actions', () => {
  assert.match(workspace, /deriveOnboardingState\(client\)/);
  assert.match(workspace, /onboarding\.completionPercent/);
  assert.match(workspace, /onOpen\(client\)/);
  assert.match(workspace, /onAdd/);
  assert.match(workspace, /ProgressBar/);
  assert.match(workspace, /Client command centre/);
});

test('UI-2 Client360 preserves workflow tabs and callbacks', () => {
  for (const tab of ['Health Profile', 'Health Records', 'Diet Plan', 'Reports', 'Biomarkers', 'Timeline']) {
    assert.ok(client360.includes(`'${tab}'`), `missing ${tab} tab`);
  }
  assert.match(client360, /await onStatus\(event\.target\.value\)/);
  assert.match(client360, /openGeneralWhatsApp/);
  assert.match(client360, /setActive\('Diet Plan'\)/);
  assert.match(client360, /ClientCommandCentre/);
  assert.match(client360, /No upcoming-care source is loaded here/);
});

test('UI-2 is responsive and does not introduce unsupported priority scoring', () => {
  assert.match(workspace, /sm:grid-cols/);
  assert.match(client360, /xl:grid-cols-12/);
  assert.doesNotMatch(workspace + client360, /priorityScore|calculatePriority|P1 priority/);
});
