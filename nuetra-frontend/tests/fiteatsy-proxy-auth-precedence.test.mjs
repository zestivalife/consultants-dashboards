import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import test from 'node:test';

const proxy = await readFile(new URL('../pages/api/fiteatsy/[...path].js', import.meta.url), 'utf8');

test('authenticated browser bearer cannot be replaced by a QA cookie', () => {
  assert.match(proxy, /qaToken && !headers\.has\('authorization'\)/);
  assert.doesNotMatch(proxy, /if \(qaToken\) headers\.set\('authorization'/);
});
