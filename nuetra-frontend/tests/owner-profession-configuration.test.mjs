import assert from 'node:assert/strict';
import test from 'node:test';

import {
  LEGACY_PROFESSION_ACCESS_ROLES,
  PROFESSION_CATALOG,
  dietEligibilityLabel,
  professionOption,
} from '../lib/professionCatalog.mjs';

test('approved catalogue exposes exactly 18 canonical choices', () => {
  assert.equal(PROFESSION_CATALOG.length, 18);
  assert.equal(new Set(PROFESSION_CATALOG.map(({ id }) => id)).size, 18);
  assert.equal(PROFESSION_CATALOG.filter(({ eligibility }) => eligibility === 'ENABLED').length, 9);
  assert.equal(PROFESSION_CATALOG.filter(({ eligibility }) => eligibility === 'OPTIONAL').length, 3);
  assert.equal(PROFESSION_CATALOG.filter(({ eligibility }) => eligibility === 'DISABLED').length, 6);
});

test('nutrition specialisations remain compatible without becoming access roles', () => {
  assert.equal(professionOption('CLINICAL_NUTRITIONIST').id, 'DIETITIAN');
  assert.equal(professionOption('SPORTS_NUTRITIONIST').id, 'DIETITIAN');
  assert.equal(LEGACY_PROFESSION_ACCESS_ROLES.has('dietician'), true);
});

test('backend-derived eligibility is presented read-only and fail closed', () => {
  assert.equal(dietEligibilityLabel({ state: 'CONFIGURED', diet_chart_authoring_enabled: true }), 'Standard draft authoring eligible');
  assert.equal(dietEligibilityLabel({ state: 'CONFIGURED', diet_chart_eligibility: 'OPTIONAL' }), 'Administrator entitlement required');
  assert.equal(dietEligibilityLabel({ state: 'CONFIGURED', diet_chart_eligibility: 'DISABLED' }), 'Not eligible');
  assert.equal(dietEligibilityLabel({ state: 'UNCONFIGURED' }), 'Profession not configured');
});
