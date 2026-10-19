import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';
const store=fs.readFileSync(new URL('../lib/savedConsultants.js',import.meta.url),'utf8');
const button=fs.readFileSync(new URL('../components/public-consultant/SaveConsultantButton.jsx',import.meta.url),'utf8');
const compare=fs.readFileSync(new URL('../pages/consultants/compare.js',import.meta.url),'utf8');
const directory=fs.readFileSync(new URL('../pages/consultants/index.js',import.meta.url),'utf8');
const profile=fs.readFileSync(new URL('../pages/consultants/[slug].js',import.meta.url),'utf8');
const homepage=fs.readFileSync(new URL('../components/public-consultant/HomepageConsultantShowcase.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/publicMarketplaceApi.js',import.meta.url),'utf8');

test('guest shortlist stores only validated public slugs within governed limits',()=>{assert.match(store,/SAVED_CONSULTANTS_LIMIT=10/);assert.match(store,/COMPARISON_LIMIT=4/);assert.match(store,/\^\[a-z0-9-\]/);assert.doesNotMatch(store,/email|phone|tenant|medical|credential/i);});
test('save actions are accessible and integrated across discovery surfaces',()=>{for(const source of [directory,profile,homepage])assert.match(source,/SaveConsultantButton/);assert.match(button,/aria-pressed/);assert.match(button,/Shortlist limit reached \(10\)/);assert.match(button,/Compare \{Math\.min\(items\.length,4\)\} Consultants/);});
test('comparison resolves live public data and handles stale profiles without false zero',()=>{assert.match(api,/\/compare\?/);for(const value of ['unavailable_count','no longer publicly available','Comparison data is unavailable','No consultants were treated as missing'])assert.match(compare,new RegExp(value,'i'));});
test('comparison is factual, neutral, and has no medical recommendation language',()=>{for(const value of ['Profession','Professional title','Specialisations','Experience','Languages','Consultation mode','Location','Services','Session duration','Starting fee','Accepting new clients','Next availability','Rating','Verified reviews','Verified qualifications','does not rank clinical quality'])assert.match(compare,new RegExp(value,'i'));assert.doesNotMatch(compare,/best match|recommended for|clinical score|effectiveness score/i);});
test('comparison supports desktop and mobile without a horizontal table dependency',()=>{assert.match(compare,/hidden overflow-hidden.*md:block/s);assert.match(compare,/md:hidden/);assert.match(compare,/Show differences only/);assert.match(compare,/min-h-11/);});
test('comparison analytics are explicit and never claim conversion',()=>{for(const value of ['CONSULTANT_SAVED','CONSULTANT_UNSAVED','COMPARISON_OPENED','COMPARE_PROFILE_CLICK','COMPARE_ENROL_CLICK'])assert.match(button+compare,new RegExp(value));assert.doesNotMatch(button+compare,/CONVERSION|SUCCESSFUL_BOOKING/);});
