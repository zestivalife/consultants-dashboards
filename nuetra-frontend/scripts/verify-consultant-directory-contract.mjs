import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';

const sourceUrl = new URL('../components/platform/PlatformWorkspace.jsx', import.meta.url);
const source = await readFile(sourceUrl, 'utf8');

assert.equal(
  (source.match(/title: 'Assigned clients'/g) || []).length,
  1,
  'The Consultant directory must expose exactly one canonical Assigned clients queue control.',
);
assert.equal(
  source.includes('Show all assigned clients'),
  false,
  'The removed duplicate Assigned clients control must not be restored.',
);
assert.equal(
  source.includes("packageLabel: 'Not assigned'"),
  false,
  'Subscription presentation must not use assignment terminology.',
);
assert.match(
  source,
  /client\.subscriptionActive === true && client\.subscriptionPlanName[\s\S]*?'No active subscription'/,
  'The Consultant roster must render a plan only for a canonical active subscription.',
);

console.log('Consultant directory contract: 4/4 PASS');
