import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';

const home=fs.readFileSync(new URL('../components/external/ExternalIntelligentHome.jsx',import.meta.url),'utf8');
const workspace=fs.readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');

test('command centre exposes the agreed consultant journey',()=>{
  for(const label of ['Daily brief','Start my day','My work','Today\'s schedule','Session brief','Confirmed session evidence','Post-session actions','Clients needing attention','Recent changes','Continue working','New client onboarding','Lead attention','Marketplace signals','Renewal opportunities','Revenue attention','Automation actions waiting','Notification digest']) assert.match(home,new RegExp(label,'i'));
  for(const tab of ['TODAY','UPCOMING','OVERDUE','COMPLETED']) assert.match(home,new RegExp(tab));
  assert.match(home,/operational priorities from confirmed data/i);
  assert.match(home,/No clinical-risk scoring/i);
  for(const source of ['schedule.items','sections.leads','sections.marketplace','sections.renewals','sections.automation_confirmations','DOCUMENT']) assert.match(home,new RegExp(source.replace('.','\\.')));
  for(const action of ['Complete session note','Assign homework','Share resource','Create follow-up','Book next appointment','Update goal','Prepare message','Create invoice','Generate report']) assert.match(home,new RegExp(action,'i'));
});

test('failed, loading, restricted and confirmed-empty states remain truthful',()=>{
  assert.match(home,/FAILED_TO_LOAD/);
  assert.match(home,/CONFIRMED_EMPTY/);
  assert.match(home,/Section unavailable/);
  assert.match(home,/No empty or zero state is inferred/);
  assert.match(home,/Not available for this role/);
  assert.match(home,/LoadingSkeleton/);
});

test('global search and create foundations are permission-aware',()=>{
  assert.match(workspace,/Global command search/);
  assert.match(workspace,/Search clients, modules or actions/);
  assert.match(workspace,/navigationItems=\{navigationItems\}/);
  for(const domain of ['clients','leads','calendar','tasks','billing','resources','forms','referrals','progress-reports']) assert.match(workspace,new RegExp(`'${domain}'`));
});

test('frontend consumes only the dedicated read-model endpoint',()=>{
  assert.match(api,/dashboard\/command-centre/);
  assert.match(workspace,/getDashboardCommandCentre/);
});
