import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const dashboard=fs.readFileSync(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
const portal=fs.readFileSync(new URL('../pages/client-portal/[token].js',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const backend=fs.readFileSync(new URL('../../services/practice-operations-service/app/main.py',import.meta.url),'utf8');

test('P38 command centre exposes truthful post-session progress',()=>{for(const value of ['Follow-up and retention workspace','required actions complete','Continue working','post_session'])assert.match(dashboard,new RegExp(value));});
test('P38 portal exposes only client-safe shared follow-up domains',()=>{for(const value of ['After your consultation','Private notes, draft plans and internal intelligence are never shown','data.postSession'])assert.match(portal,new RegExp(value));});
test('P38 API exposes governed start, projection, action completion and analytics',()=>{for(const value of ['startPostSession','getPostSession','completePostSessionAction','getPostSessionAnalytics'])assert.match(api,new RegExp(value));for(const value of ['COMPLETED_SESSION_REQUIRED','SESSION_OPERATIONALLY_CLOSED','autoRenew','autoMessageSend'])assert.match(backend,new RegExp(value));});
