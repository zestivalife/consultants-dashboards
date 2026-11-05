import assert from 'node:assert/strict';
import { execFileSync } from 'node:child_process';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const registry = JSON.parse(readFileSync(path.join(frontendRoot, 'contracts/external-consultant-api-registry.json'), 'utf8'));
const inventory = JSON.parse(readFileSync(path.join(frontendRoot, 'contracts/provider-route-inventory.json'), 'utf8'));
const providerRoot = path.resolve(process.env.FITEATSY_ROOT || process.argv[2] || '');
assert.notEqual(providerRoot, path.parse(providerRoot).root, 'FITEATSY_ROOT must identify an explicit checkout');

const baselineSha = registry.provider_baselines.fiteatsy;
const expectedSha = process.env.FITEATSY_CANDIDATE_SHA || baselineSha;
const actualSha = execFileSync('git', ['rev-parse', 'HEAD'], { cwd: providerRoot, encoding: 'utf8' }).trim();
assert.equal(actualSha, expectedSha, `Fiteatsy checkout must match the requested provider SHA ${expectedSha}`);
assert.equal(inventory.generated_from.fiteatsy, baselineSha, 'route inventory and registry must use the same baseline Fiteatsy SHA');

const read = (relative) => readFileSync(path.join(providerRoot, relative), 'utf8');
const server = read('backend/src/server.ts');
const delegatedRoutes = read('backend/src/modules/external-consultants/external-consultant-access.routes.ts');
const nutritionRoutes = read('backend/src/modules/nutrition/nutrition.routes.ts');
const mobileClient = read('src/services/nutritionPlanService.ts');
const mobileTypes = read('src/types/index.ts');

const operations = inventory.operations.filter((operation) => operation.provider === 'fiteatsy');
assert.deepEqual(operations.map(({ method, path: operationPath }) => [method, operationPath]), [
  ['GET', '/v1/internal/external-consultant-access/{userId}/health-context'],
  ['GET', '/v1/platform/nutrition-plan'],
]);

assert.match(server, /app\.use\('\/v1\/internal\/external-consultant-access', externalConsultantAccessRouter\)/);
assert.match(delegatedRoutes, /externalConsultantAccessRouter\.get\('\/:userId\/health-context', requireDelegatedAuthority\('fiteatsy\.external\.health\.read', 'external_consultant_health'\)/);
for (const field of ['connectionId', 'profile', 'foodPreferences', 'assessment', 'measurements', 'reports', 'biomarkers', 'wearables', 'generatedAt']) {
  assert.match(delegatedRoutes, new RegExp(`\\b${field}\\b`), `delegated health response is missing ${field}`);
}

assert.match(server, /app\.use\('\/v1\/platform', platformNutritionRouter\)/);
assert.match(nutritionRoutes, /platformNutritionRouter\.use\(requireAuthenticatedAccount\)/);
assert.match(nutritionRoutes, /platformNutritionRouter\.get\('\/nutrition-plan'/);
assert.match(nutritionRoutes, /return res\.status\(200\)\.json\(\{\s*\.\.\.payload,\s*today:/s);
assert.match(mobileClient, /apiFetch<PublishedNutritionPlan>\('\/v1\/platform\/nutrition-plan'/);
for (const field of ['plan', 'version', 'today']) {
  assert.match(mobileTypes, new RegExp(`export type PublishedNutritionPlan = \\{[\\s\\S]*?\\n  ${field}:`), `mobile response type is missing ${field}`);
}

console.log(JSON.stringify({ provider: 'fiteatsy', sha: actualSha, baselineSha, operations: operations.length, status: 'compatible' }));
