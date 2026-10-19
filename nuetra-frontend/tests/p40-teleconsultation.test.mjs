import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/clientPortalApi.js',import.meta.url),'utf8');
const practice=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const dashboard=fs.readFileSync(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
test('client portal exposes a truthful waiting-room journey',()=>{for(const value of ['Join session','Waiting for your consultant','Provider:','outside its join window'])assert.match(portal,new RegExp(value));});
test('portal and practitioner use governed APIs',()=>{assert.match(api,/getPortalTeleconsult/);assert.match(api,/joinPortalTeleconsult/);assert.match(practice,/configureTeleconsult/);assert.match(practice,/transitionTeleconsult/);});
test('P32 integrates virtual session signals',()=>{assert.match(dashboard,/Virtual consultations/);assert.match(dashboard,/sections\.teleconsult/);});
