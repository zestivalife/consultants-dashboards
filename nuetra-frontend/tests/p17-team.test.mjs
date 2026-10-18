import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import test from 'node:test';

const team=readFileSync(new URL('../components/external/ExternalTeam.jsx',import.meta.url),'utf8');
const workspace=readFileSync(new URL('../components/external/ExternalSaaSWorkspace.jsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const client360=readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const calendar=readFileSync(new URL('../components/external/ExternalCalendarWorkspace.jsx',import.meta.url),'utf8');

test('P17 team navigation and actions are permission gated',()=>{
  assert.match(workspace,/permissions\?\.includes\('TEAM_VIEW'\)/);
  assert.match(team,/permissions\.includes\('TEAM_MANAGE'\)/);
  assert.match(team,/Invite member/);
});

test('P17 team workspace has governed members invitations and role summaries',()=>{
  for(const label of ['Members','Invitations','Roles & access','Practice owner','Practice admin','Practitioner','Assistant','Receptionist'])assert.match(team,new RegExp(label));
  assert.match(team,/Private notes are not included/);
  assert.match(team,/Team access unavailable/);
});

test('P17 frontend routes every mutation through protected practice APIs',()=>{
  for(const route of ['/team/access','/team/invitations','/team/members/','/clients/'])assert.ok(api.includes(route));
  assert.doesNotMatch(team,/localStorage|sessionStorage|password_hash/);
});

test('P17 role changes require an explicit impact confirmation',()=>{
  assert.match(team,/Impact summary/);assert.match(team,/I understand this access impact/);assert.match(team,/SELF_ROLE_ESCALATION|Confirm access change/);
});

test('P17 exposes governed Client360 care team and team calendar surfaces',()=>{
  assert.match(client360,/Care Team/);assert.match(team,/ClientCareTeam/);assert.match(team,/Primary practitioner/);
  assert.match(calendar,/My Calendar/);assert.match(calendar,/Team Calendar/);assert.match(calendar,/CALENDAR_MANAGE/);
});
