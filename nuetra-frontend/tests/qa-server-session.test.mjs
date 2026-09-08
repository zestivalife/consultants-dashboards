import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
const read=file=>fs.readFileSync(new URL(`../${file}`,import.meta.url),'utf8');

test('QA bootstrap exchanges only in server-side rendering and sets a secure HttpOnly cookie',()=>{
  const source=read('pages/qa-handoff.js');
  const cookie=read('lib/qaServerSession.js');
  assert.match(source,/x-qa-bootstrap-secret/);
  assert.match(source,/getServerSideProps/);
  assert.match(source,/res\.setHeader\('Set-Cookie'/);
  assert.match(cookie,/HttpOnly; Secure; SameSite=Lax/);
  assert.doesNotMatch(source,/localStorage|sessionStorage|console\./);
});

test('handoff is consumed server-side and never enters rendered props or client JavaScript',()=>{
  const page=read('pages/qa-handoff.js');
  assert.match(page,/getServerSideProps/);
  assert.match(page,/Referrer-Policy.*no-referrer/);
  assert.match(page,/redirect:/);
  assert.doesNotMatch(page,/window\.|useEffect|fetch\('\/api\/qa\/bootstrap|props:\s*\{[^}]*code/);
  assert.equal(fs.existsSync(new URL('../pages/api/qa/bootstrap.js',import.meta.url)),false);
});

test('QA bootstrap fails closed outside the exact preview branch and QA backend',()=>{
  const page=read('pages/qa-handoff.js');
  assert.match(page,/VERCEL_ENV === 'preview'/);
  assert.match(page,/VERCEL_GIT_COMMIT_REF === QA_BRANCH/);
  assert.match(page,/qa-diet-builder-acceptance/);
  assert.match(page,/notFound: true/);
  assert.match(page,/body\?\.qaSession\?\.role/);
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
