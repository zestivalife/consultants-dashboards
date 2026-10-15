import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const workspace = fs.readFileSync(
  new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url),
  'utf8',
);

test('internal client allocation never reports an empty pool when availability failed', () => {
  assert.match(
    workspace,
    /loading \? <p[^>]*>Loading Client Pool\.\.\.<\/p> : error \? \(/,
  );
  assert.match(workspace, /Client Pool availability could not be confirmed\. Retry safely\./);
});

test('internal Senior review queue never reports an empty queue when availability failed', () => {
  assert.match(
    workspace,
    /loading \? <p[^>]*>Loading review queue\.\.\.<\/p> : error \? \(/,
  );
  assert.match(workspace, /Review queue availability could not be confirmed\. Retry safely\./);
});
