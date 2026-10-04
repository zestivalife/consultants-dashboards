import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const read=(path)=>fs.readFileSync(new URL(`../${path}`,import.meta.url),'utf8');

test('public signup uses governed verification and resumable provisioning APIs',()=>{
  const page=read('pages/signup.js');
  const api=read('lib/api.js');
  assert.match(page,/startExternalSignup/);
  assert.match(page,/verifyExternalSignup/);
  assert.match(page,/resendExternalSignup/);
  assert.match(page,/INDEPENDENT_CONSULTANT/);
  assert.match(page,/PRACTICE_OWNER/);
  assert.match(api,/\/auth\/external-signup\/start/);
  assert.match(api,/\/auth\/external-signup\/verify/);
  assert.doesNotMatch(page,/localStorage|access_token|bearer/i);
});

test('login exposes signup without changing existing sign-in authority',()=>{
  const login=read('pages/login.js');
  assert.match(login,/href="\/signup"/);
  assert.match(login,/Create your workspace/);
  assert.match(login,/await login\(form\)/);
});
