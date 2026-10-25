import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const marketplace=readFileSync(new URL('../components/external/ExternalMarketplace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('core consultant profile remains editable when optional marketplace dependencies fail',()=>{
  assert.match(marketplace,/Promise\.allSettled/);
  assert.match(marketplace,/getMarketplaceProfile\(false\)/);
  assert.match(marketplace,/Your core profile remains editable/);
  assert.match(api,/include_analytics/);
});

test('consultant profile explains the governed approval and public-directory lifecycle',()=>{
  for(const text of ['Complete your consultant profile','Super Admin approval','Zestiva Consultants directory','Submit for review','Preview draft'])assert.match(marketplace,new RegExp(text));
});
