import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const workspace=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('Client 360 exposes the external Diet Plan action and dedicated tab',()=>{assert.match(workspace,/Create Diet Plan/);assert.match(workspace,/active === 'Diet Plan'/);assert.match(workspace,/getExternalDietPlan/);});
test('external authoring uses seven-head Common Food result and exact 35-option persistence',()=>{assert.match(workspace,/snapshot\.meals\.map/);assert.match(workspace,/meal\.options\.map/);assert.match(workspace,/flatMap\(meal=>meal\.options\)/);assert.match(api,/diet-plan\/generate/);assert.match(api,/diet-plan\/draft/);});
test('external cards and DOCX use real governed snapshot fields without placeholder fallbacks',()=>{assert.match(workspace,/validateExternalDietOption/);assert.doesNotMatch(workspace,/Governed food option/);assert.doesNotMatch(workspace,/option\.totals/);assert.doesNotMatch(workspace,/option\.items/);});
test('publication is explicit and does not expose a Senior approval action',()=>{assert.match(workspace,/Publish this exact Diet Plan version to the client/);assert.match(workspace,/External Consultant self-publish workflow/);assert.doesNotMatch(workspace,/Submit for Senior|Request Senior/);});
test('DOCX export uses the governed backend template rather than a browser-built approximation',()=>{assert.match(workspace,/downloadExternalDietPlan/);assert.match(workspace,/Export DOCX/);assert.match(api,/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/diet-plan\/download/);assert.doesNotMatch(workspace,/Packer\.toBlob|new Document/);});
test('completed intake optional sections are not presented as missing requirements',()=>{assert.match(workspace,/Optional information not provided/);assert.match(workspace,/Missing required information/);});
test('external Diet Plan reuses the full Internal Common Food editor through an injected adapter',()=>{
  assert.match(workspace,/CommonFoodPlanEditor/);
  assert.match(workspace,/authoringApi=\{externalAuthoringApi\}/);
  assert.match(workspace,/templatesEnabled=\{false\}/);
  for(const operation of ['searchExternalCommonFoods','replaceExternalCommonFoodSelection','replaceExternalCommonFoodComponent','addExternalCommonFoodComponent','removeExternalCommonFoodComponent','updateExternalCommonFoodServing'])assert.match(workspace,new RegExp(operation));
});
test('external Common Food API remains on external tenant-authority routes',()=>{
  assert.match(api,/externalCommonFoodPath/);
  assert.match(api,/\/v1\/external\/clients\/\$\{encodeURIComponent\(clientId\)\}\/common-foods/);
  assert.doesNotMatch(api,/externalCommonFoodPath[^\n]+\/v1\/consultants/);
});
