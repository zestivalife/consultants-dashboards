import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const multi=readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx',import.meta.url),'utf8');
const marketplace=readFileSync(new URL('../components/external/ExternalMarketplace.jsx',import.meta.url),'utf8');
const dietApi=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const profileApi=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('multiple named plans are listed, selected, created and persisted by immutable plan id',()=>{
  for(const term of ['listExternalDietPlans','createExternalDietPlan','saveExternalDietPlanById','publishExternalDietPlanById','Create another Diet Plan','Selected Diet Plan'])assert.match(multi,new RegExp(term));
  assert.match(dietApi,/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/draft/);
  assert.match(dietApi,/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/publish/);
});

test('calorie and protein target boundaries are explicit client and API contract values',()=>{
  assert.match(multi,/Number\(form\.dailyCalories\) >= 800/);
  assert.match(multi,/Number\(form\.dailyCalories\) <= 6000/);
  assert.match(multi,/Number\(form\.dailyProtein\) >= 20/);
  assert.match(multi,/Number\(form\.dailyProtein\) <= 400/);
});

test('marketplace contact and photo forms use persistent APIs and reload after success',()=>{
  for(const term of ['saveMarketplaceContact','uploadMarketplaceProfilePhoto','onReload','country_iso2','national_number'])assert.match(marketplace,new RegExp(term));
  assert.match(profileApi,/marketplace\/contact/);
  assert.match(profileApi,/marketplace\/profile\/photo-upload/);
  assert.match(profileApi,/marketplace\/profile\/photo-finalise/);
});

test('profile save verifies the server projection before showing success',()=>{
  assert.match(marketplace,/await getMarketplaceProfile\(\)/);
  assert.match(marketplace,/server response did not match the submitted profile/i);
  assert.match(marketplace,/if\(saving\)return/);
});
