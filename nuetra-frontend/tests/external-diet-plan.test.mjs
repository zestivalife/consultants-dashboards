import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const shell=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');
const multi=readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx',import.meta.url),'utf8');
const practiceApi=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('Client 360 exposes the Practice Operations Diet Plan action and dedicated tab',()=>{const active=workspace.split('function LegacyExternalDietPlan')[0];assert.match(active,/Open Diet Plans/);assert.match(active,/active === 'Diet Plan'/);assert.match(active,/ExternalMultiDietPlan/);assert.doesNotMatch(active,/getExternalDietPlan\(client\.id\)/);});
test('Diet Plans landing page exposes a primary creation action even when no plan exists',()=>{assert.match(shell,/function PlanHistory/);assert.match(shell,/Create Diet Plan/);assert.match(shell,/label="Generate Diet Plan"/);assert.match(shell,/action=\{firstClient\?\(\)=>onOpen\(firstClient\):undefined\}/);});
test('external authoring uses seven governed meal heads and versioned Practice Operations persistence',()=>{assert.match(multi,/COMMON_FOOD_MEALS/);assert.match(multi,/flatMap\(\(meal\) => meal\.options\)/);assert.match(practiceApi,/saveConsultantDietPlan/);assert.match(practiceApi,/\/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/draft/);});
test('external plan history renders backend snapshot fields without placeholder nutrition',()=>{assert.match(multi,/nutrition_snapshot\?\.option_count/);assert.doesNotMatch(multi,/Governed food option/);assert.doesNotMatch(multi,/option\.totals/);});
test('consultant can approve the exact version directly before publication',()=>{assert.doesNotMatch(multi,/Submit for review|Senior Consultant review/);assert.match(multi,/Approve exact version/);assert.match(multi,/Publish to Client App/);assert.match(multi,/expected_version:refreshed\.plan\.current_version/);});
test('DOCX export uses the governed Practice Operations endpoint rather than a browser-built approximation',()=>{assert.match(multi,/downloadConsultantDietPlan/);assert.match(multi,/Download DOCX/);assert.match(practiceApi,/diet-plans\/\$\{encodeURIComponent\(planId\)\}\/download/);assert.doesNotMatch(multi,/Packer\.toBlob|new Document/);});
test('Diet Requirements uses an accessible consolidated modal and existing scoped questionnaire contracts',()=>{
  assert.match(multi,/Open Diet Requirements/);
  assert.match(multi,/role="dialog"/);
  assert.match(multi,/aria-modal="true"/);
  assert.match(multi,/aria-labelledby="diet-requirements-title"/);
  assert.match(multi,/event\.key === 'Escape'/);
  assert.match(multi,/getClientInformationCompleteness\(clientId\)/);
  assert.match(multi,/createClientInformationRequest\(clientId/);
  assert.match(multi,/field_ids:\s*requestedFields/);
  assert.match(multi,/expires_in_hours:\s*168/);
  assert.match(multi,/Request Missing Information/);
});
test('Diet Requirements keeps clinical context read-only and does not derive professional targets',()=>{
  for(const label of ['Client nutrition context','Measurements and evidence','Meals per day','Typical food intake','Medical conditions','Supplements'])assert.match(multi,new RegExp(label));
  assert.match(multi,/not prescribed automatically from BMI or assessment completeness/);
  assert.doesNotMatch(multi,/setForm\([^\n]+bmi/i);
  assert.match(multi,/Authoring permitted/);
  assert.match(multi,/Missing information is advisory/);
});
test('completed intake optional sections are not presented as missing requirements',()=>{assert.match(workspace,/Optional information not provided/);assert.match(workspace,/Missing required information/);});
test('external Diet Plan reuses the full Internal Common Food editor through an injected adapter',()=>{
  assert.match(multi,/CommonFoodPlanEditor/);
  assert.match(multi,/authoringApi=\{authoringApi\}/);
  assert.match(multi,/templatesEnabled=\{false\}/);
  for(const operation of ['searchExternalCommonFoods','replaceSelection','replaceComponent','addComponent','removeComponent','updateServing'])assert.match(multi,new RegExp(operation));
});
test('external Common Food search uses the backend-authorised consultant client contract',()=>{
  assert.match(api,/searchExternalCommonFoods[\s\S]*\/v1\/consultants\/clients\/\$\{encodeURIComponent\(clientId\)\}\/common-foods/);
  assert.doesNotMatch(api,/searchExternalCommonFoods[\s\S]{0,500}\/v1\/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/common-foods/);
});
