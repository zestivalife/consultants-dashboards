import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const ownerConsole = fs.readFileSync(new URL('../components/platform/OwnerConsoleModules.jsx', import.meta.url), 'utf8');
const schema = fs.readFileSync(new URL('../../services/auth-service/app/schemas/people_access.py', import.meta.url), 'utf8');

test('Owner Console exposes the governed synthetic Nutritionist fixture', () => {
  assert.match(ownerConsole, /\['NUTRITIONIST', 'QA External Nutritionist', 'qa\+external-nutritionist@zestiva\.test'/);
});

test('Auth accepts governed nutrition QA professions without accepting OTHER', () => {
  for (const profession of ['DIETITIAN', 'NUTRITIONIST', 'CLINICAL_NUTRITIONIST', 'SPORTS_NUTRITIONIST']) {
    assert.match(schema, new RegExp(`ExternalQaProfession = Literal\\[[^\\n]*"${profession}"`));
  }
  assert.doesNotMatch(schema, /ExternalQaProfession = Literal\[[^\n]*"OTHER"/);
});
