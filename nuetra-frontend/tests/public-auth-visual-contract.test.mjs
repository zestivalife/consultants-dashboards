import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';

const read=(path)=>readFileSync(new URL(path,import.meta.url),'utf8');
const login=read('../pages/login.js'),signup=read('../pages/signup.js'),landing=read('../components/public-consultant/ConsultantLanding.jsx');
const header=read('../components/public-consultant/PublicHeader.jsx'),story=read('../components/public-consultant/AuthStoryPanel.jsx'),logo=read('../components/public-consultant/ZestivaLogo.jsx');

test('root and auth surfaces share the exact approved Zestiva asset',()=>{
  assert.match(logo,/src="\/zestiva\.svg"/);
  assert.match(logo,/width=\{336\} height=\{86\}/);
  assert.match(landing,/ZestivaLogo/);
  assert.match(landing,/href=\{ROOT\} aria-label="Zestiva Consultant home"/);
  assert.match(header,/ZestivaLogo/);
  assert.match(login,/PublicHeader/);
  assert.match(signup,/PublicHeader/);
});

test('auth layouts preserve task-first mobile order and approved desktop ratios',()=>{
  assert.match(login,/lg:grid-cols-\[minmax\(0,1\.35fr\)_minmax\(420px,0\.9fr\)\]/);
  assert.match(login,/max-w-\[560px\]/);
  assert.match(signup,/lg:grid-cols-\[minmax\(0,1fr\)_minmax\(560px,1fr\)\]/);
  assert.match(signup,/max-w-\[820px\]/);
  assert.match(login,/order-2 min-w-0 lg:order-1/);
  assert.match(signup,/order-2 min-w-0 self-start lg:order-1/);
});

test('auth header preserves exact public navigation and reciprocal actions',()=>{
  for(const hash of ['#product','#intelligence','#health','#solutions','#security'])assert.ok(header.includes(hash));
  assert.match(header,/https:\/\/consultant\.nuetra\.in\/login/);
  assert.match(header,/https:\/\/consultant\.nuetra\.in\/signup/);
  assert.match(header,/const ROOT='https:\/\/consultant\.nuetra\.in\/'/);
});

test('login has the new practice story and old wellness story is removed',()=>{
  assert.match(login,/AuthStoryPanel mode="login"/);
  for(const old of ['Adaptive wellness operations','Operational prioritization','Indian-native plan logic','Role-aware maturity'])assert.equal(login.includes(old),false);
  for(const copy of ['Your intelligent practice operating system.','Needs attention','Client360','Progress'])assert.ok(story.includes(copy));
});

test('signup keeps governed form contracts and adds interactive product context',()=>{
  assert.match(signup,/AuthStoryPanel mode="signup"/);
  assert.equal(signup.includes('Fiteatsy Consultant SaaS'),false);
  for(const field of ['fullName','mobileNumber','email','password','confirmPassword','professionalRole','accountType','yearsExperience','activeClientRange'])assert.ok(signup.includes(field));
  for(const capability of ['Client360','Priorities','Progress','Communication'])assert.ok(story.includes(capability));
  assert.match(signup,/canonicalMobile\(form\.mobileNumber\)/);
  assert.match(signup,/registerExternalConsultant/);
});
