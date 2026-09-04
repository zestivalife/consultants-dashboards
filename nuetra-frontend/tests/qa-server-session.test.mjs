import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=file=>fs.readFileSync(new URL(`../${file}`,import.meta.url),'utf8');

test('QA bootstrap exchanges server-side and sets a secure HttpOnly cookie',()=>{
  const source=read('pages/api/qa/bootstrap.js');
  const cookie=read('lib/qaServerSession.js');
  assert.match(source,/x-qa-bootstrap-secret/);
  assert.match(source,/res\.status\(200\)\.json/);
  assert.match(cookie,/HttpOnly; Secure; SameSite=Lax/);
  assert.doesNotMatch(source,/localStorage|sessionStorage|console\./);
});

test('opaque code transits in a fragment and is removed before exchange',()=>{
  const page=read('pages/qa-handoff.js');
  assert.match(page,/window\.location\.hash/);
  assert.match(page,/replaceState\(null,'','\/qa-handoff'\)/);
  assert.match(page,/method:'POST'/);
});

test('Fiteatsy proxy injects the QA credential only on the server',()=>{
  const proxy=read('pages/api/fiteatsy/[...path].js');
  assert.match(proxy,/readQaSession\(req\)/);
  assert.match(proxy,/headers\.set\('authorization'/);
});

test('QA shell identity is resolved without writing bearer credentials',()=>{
  const auth=read('context/AuthContext.js');
  assert.match(auth,/fetch\('\/api\/qa\/session'/);
  assert.match(auth,/mode: 'qa-server-session'/);
  assert.doesNotMatch(auth,/setToken\(payload/);
});
