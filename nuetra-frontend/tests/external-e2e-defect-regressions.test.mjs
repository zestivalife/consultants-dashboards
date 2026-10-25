import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=(path)=>fs.readFileSync(new URL(path,import.meta.url),'utf8');

test('Client360 refreshes authoritative core projections after profile writes',()=>{
  const source=read('../components/external/ExternalClient360.jsx');
  assert.match(source,/const refreshCore=/);
  assert.match(source,/setProfileEnrichment\(next\);await refreshCore\(\)/);
  assert.match(source,/setMeasurementData\(next\);await refreshCore\(\)/);
});
