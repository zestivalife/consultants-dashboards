import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';
import test from 'node:test';

const providerRoot = process.env.FITEATSY_ROOT;

test('pinned Fiteatsy checkout satisfies executable route, authorization and response contracts', { skip: !providerRoot }, () => {
  assert.ok(existsSync(path.join(providerRoot, '.git')) || existsSync(path.join(providerRoot, 'backend')));
  const output = execFileSync(process.execPath, ['scripts/verify-fiteatsy-contracts.mjs', providerRoot], {
    cwd: path.resolve(import.meta.dirname, '..'), encoding: 'utf8', env: process.env,
  });
  const result = JSON.parse(output.trim());
  assert.equal(result.status, 'compatible');
  assert.equal(result.operations, 2);
});

test('cross-repository verification is mandatory in exact-SHA CI', () => {
  const workflow = readFileSync(path.resolve(import.meta.dirname, '..', '..', '.github/workflows/frontend-exact-sha-ci.yml'), 'utf8');
  assert.match(workflow, /repository: zestivalife\/Fiteatsy-mobile/);
  assert.match(workflow, /FITEATSY_ROOT:/);
  assert.match(workflow, /verify-fiteatsy-contracts\.mjs/);
  assert.match(workflow, /external-consultant-health-context\.api\.test\.ts/);
  assert.match(workflow, /fiteatsy_contract_ci/);
});
