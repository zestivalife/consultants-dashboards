import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const api = fs.readFileSync(new URL('../lib/practiceOperationsApi.js', import.meta.url), 'utf8');

test('missing client records use specific plain-language messages', () => {
  for (const message of [
    'No measurements have been recorded for this client yet.',
    'The client has not completed a nutrition assessment yet.',
    'The client has not completed the profession-specific intake questionnaire yet.',
    'No additional profile details have been recorded for this client yet.',
    'No client activity has been recorded yet.',
  ]) assert.match(api, new RegExp(message.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')));
  assert.doesNotMatch(api, /The requested practice record could not be found/);
});
