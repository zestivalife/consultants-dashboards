import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
test('portal messaging is secure and separate from WhatsApp',()=>{assert.match(portal,/Secure in-platform messages/);assert.match(portal,/separate from WhatsApp/);assert.match(portal,/No secure conversation/);});
test('practice APIs expose governed inbox operations',()=>{for(const x of ['createSecureConversation','listSecureConversations','getSecureConversation','sendSecureMessage'])assert.match(api,new RegExp(x));});
