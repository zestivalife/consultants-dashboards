import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const intake=fs.readFileSync(new URL('../components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const api=fs.readFileSync(new URL('../lib/fiteatsyConsultantsApi.js',import.meta.url),'utf8');

test('DOB is canonical, editable only when absent, and never rendered through arbitrary Date parsing',()=>{
  assert.match(intake,/formatCanonicalDob/);
  assert.match(intake,/Date needs review/);
  assert.doesNotMatch(intake,/new Date\(`\$\{value\.dateOfBirth\}T00:00:00`\)/);
  for(const label of ['First name','Last name','Mobile number','Email'])assert.match(intake,new RegExp(`ReadOnlyValue label="${label}"`));
  assert.match(intake,/value\.dateOfBirth\?<ReadOnlyValue label="Date of birth"/);
  assert.match(intake,/<Text label="Date of birth" required type="date"/);
});

test('location is structured while legacy location remains readable',()=>{
  for(const field of ['locationCountry','locationRegion','locationCity'])assert.match(intake,new RegExp(field));
  assert.match(intake,/Previous location/);
});

test('one canonical completion value drives the progress bar',()=>{
  assert.match(intake,/const progress=completion/);
  assert.doesNotMatch(intake,/Math\.max\(Math\.round\(index\*100\/applicable\.length\),completion\)/);
});

test('Client 360 renders canonical enums through a product presentation layer',()=>{
  for(const label of ['Non-Vegetarian','1–2 times/week','5+'])assert.match(client360,new RegExp(label));
  assert.match(client360,/\^\[A-Z0-9_\]\+\$/);
});

test('external intake uses tenant branding fallback and never exposes raw server failures',()=>{
  const upload=api.match(/export async function uploadExternalClientDocument[\s\S]*?\n}\n/)?.[0]||'';
  assert.match(intake,/practiceName='Your consultant'/);
  assert.match(intake,/safeExternalMessage/);
  assert.match(intake,/data\?\.safe_message/);
  assert.match(upload,/body\?\.safe_message/);
  assert.match(upload,/response\.status < 500/);
  assert.doesNotMatch(upload,/body\?\.message \|\| body\?\.error \|\| `Upload failed/);
});
