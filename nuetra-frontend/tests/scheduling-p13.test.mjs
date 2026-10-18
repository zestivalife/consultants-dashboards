import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const root=new URL('../',import.meta.url);
const calendar=readFileSync(new URL('components/external/ExternalCalendarWorkspace.jsx',root),'utf8');
const api=readFileSync(new URL('lib/practiceOperationsApi.js',root),'utf8');

test('P13 scheduling workspace exposes configuration, booking, waitlist, and attendance',()=>{
  for(const value of ['Appointment type','Add availability','Add waitlist','Attended','No-show'])assert.match(calendar,new RegExp(value));
  assert.match(calendar,/min-h-11/);
  assert.match(calendar,/role="alert"/);
});

test('P13 client requests remain routed through governed APIs',()=>{
  for(const path of ['/scheduling/appointment-types','/scheduling/availability','/scheduling/appointments','/scheduling/booking-links','/scheduling/waitlist'])assert.ok(api.includes(path));
  assert.doesNotMatch(calendar,/localStorage|sessionStorage/);
});
