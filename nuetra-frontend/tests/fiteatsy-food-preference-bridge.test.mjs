import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');

test('saved Fiteatsy food preferences are projected into external Client 360',()=>{
  assert.match(api,/context\?\.foodPreferences\?\.profile/);
  assert.match(api,/foodPreferences:savedPreferences/);
  assert.match(client360,/client\.foodPreferences\?\.dietType/);
  assert.match(client360,/Preferred cuisines/);
  assert.match(client360,/Main-meal staple/);
});

test('missing profession intake copy explains the dependency in plain language',()=>{
  assert.match(api,/profession-specific intake questionnaire/);
  assert.doesNotMatch(api,/completed the professional intake yet/);
});
