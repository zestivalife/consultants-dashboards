import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const workspace = await readFile(
  new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url),
  'utf8'
);

test('client roster never presents an API failure as a confirmed zero assignment count', () => {
  assert.match(workspace, /Assigned client roster is temporarily unavailable\./);
  assert.match(workspace, /Loading assigned client roster…/);
  assert.match(
    workspace,
    /totalCount=\{fiteatsyClientsLoading \|\| fiteatsyClientsError \? null : clients\.length\}/
  );
  assert.match(workspace, /isRealFiteatsy && hasConfirmedTotal && !errorMessage/);
});

test('confirmed empty roster still reports the canonical zero count', () => {
  assert.match(workspace, /`\$\{totalCount\} clients assigned to your consultant workspace\.`/);
});
