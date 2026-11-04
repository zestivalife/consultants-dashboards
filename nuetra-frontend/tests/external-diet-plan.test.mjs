import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const shell=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const multi=readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx',import.meta.url),'utf8');
const practiceApi=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('Client 360 exposes the governed Diet Plan workspace and dedicated tab',()=>{assert.match(workspace,/Open Diet Plans/);assert.match(workspace,/active === 'Diet Plan'/);assert.match(workspace,/ExternalMultiDietPlan/);});
test('Diet Plans landing page exposes a primary creation action even when no plan exists',()=>{assert.match(shell,/function PlanHistory/);assert.match(shell,/Create Diet Plan/);assert.match(shell,/label="Generate Diet Plan"/);assert.match(shell,/action=\{firstClient\?\(\)=>onOpen\(firstClient\):undefined\}/);});
test('external authoring uses seven governed meal heads and versioned Practice Operations persistence',()=>{assert.match(multi,/COMMON_FOOD_MEALS/);assert.match(multi,/flatMap\(\(meal\) => meal\.options\)/);assert.match(practiceApi,/saveConsultantDietPlan/);assert.match(practiceApi,/\/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/draft/);});
test('external plan history renders backend snapshot fields without placeholder nutrition',()=>{assert.match(multi,/nutrition_snapshot\?\.option_count/);assert.doesNotMatch(multi,/Governed food option/);assert.doesNotMatch(multi,/option\.totals/);});
test('consultant can approve the exact version directly before publication',()=>{assert.doesNotMatch(multi,/Submit for review|Senior Consultant review/);assert.match(multi,/Approve exact version/);assert.match(multi,/Publish approved version/);assert.match(multi,/expected_version:refreshed\.plan\.current_version/);});
test('DOCX export uses the governed Practice Operations endpoint rather than a browser-built approximation',()=>{assert.match(multi,/downloadConsultantDietPlan/);assert.match(multi,/Download DOCX/);assert.match(practiceApi,/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/download/);assert.doesNotMatch(multi,/Packer\.toBlob|new Document/);});
test('completed intake optional sections are not presented as missing requirements',()=>{assert.match(workspace,/Optional information not provided/);assert.match(workspace,/Missing required information/);});
test('external Diet Plan reuses the full Internal Common Food editor through an injected adapter',()=>{
  assert.match(multi,/CommonFoodPlanEditor/);
  assert.match(multi,/authoringApi=\{authoringApi\}/);
  assert.match(multi,/templatesEnabled=\{false\}/);
  for(const operation of ['searchExternalCommonFoods','replaceSelection','replaceComponent','addComponent','removeComponent','updateServing'])assert.match(multi,new RegExp(operation));
});
test('external Common Food API remains on external tenant-authority routes',()=>{
  assert.match(api,/externalCommonFoodPath/);
  assert.match(api,/\/v1\/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/common-foods/);
  assert.doesNotMatch(api,/externalCommonFoodPath[^\n]+\/v1\/consultants/);
});
