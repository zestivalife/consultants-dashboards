import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { canonicalPhoneDisplay, normaliseWaterIntake, validDateOfBirth, validatePdfFile, WATER_INTAKE_OPTIONS } from '../lib/externalIntakeCorrections.mjs';

const intake=fs.readFileSync(new URL('../components/external/ExternalClientHealthIntake.jsx',import.meta.url),'utf8');
const plans=fs.readFileSync(new URL('../components/external/ExternalMultiDietPlan.jsx',import.meta.url),'utf8');
const client360=fs.readFileSync(new URL('../components/external/ExternalClient360.jsx',import.meta.url),'utf8');
const practiceApi=fs.readFileSync(new URL('../lib/practiceOperationsApi.js',import.meta.url),'utf8');
const proxy=fs.readFileSync(new URL('../pages/api/fiteatsy/[...path].js',import.meta.url),'utf8');
const profileEnhancements=fs.readFileSync(new URL('../components/external/ExternalClientProfileEnhancements.jsx',import.meta.url),'utf8');

test('DOB, Indian trunk phone and exact hydration choices are canonical',()=>{
  assert.equal(validDateOfBirth('1990-02-28'),true);
  assert.equal(validDateOfBirth('2990-01-01'),false);
  assert.equal(validDateOfBirth('2023-02-29'),false);
  assert.equal(canonicalPhoneDisplay('09762006688'),'+919762006688');
  assert.equal(WATER_INTAKE_OPTIONS.length,11);
  assert.deepEqual(WATER_INTAKE_OPTIONS[0],['1000','1 ltr']);
  assert.deepEqual(WATER_INTAKE_OPTIONS.at(-1),['6000','6 ltr']);
  assert.equal(normaliseWaterIntake({waterIntake:'1_1_5_L'}),'');
  assert.equal(normaliseWaterIntake({waterIntakeMl:2500}),'2500');
});

test('Client360 header renders canonical Indian E.164 phone identity',()=>{
  assert.match(client360,/canonicalPhoneDisplay\(overview\?\.primaryContact\|\|client\.mobile/);
  assert.equal(canonicalPhoneDisplay('09762006688'),'+919762006688');
});

test('measurement history distinguishes loading, failure and successful empty states',()=>{
  assert.match(client360,/measurementState/);
  assert.match(client360,/loadMeasurements/);
  assert.match(profileEnhancements,/measurementState\.status==='loading'/);
  assert.match(profileEnhancements,/measurementState\.status==='failed'/);
  assert.match(profileEnhancements,/measurementState\.status==='ready'/);
  assert.match(profileEnhancements,/no empty history has been inferred/);
  assert.match(profileEnhancements,/Retry measurement history/);
  assert.match(profileEnhancements,/value="CLIENT_REPORTED"/);
  assert.match(profileEnhancements,/value="DOCUMENT_DERIVED"/);
  assert.doesNotMatch(profileEnhancements,/value="SELF_REPORTED"/);
  assert.doesNotMatch(profileEnhancements,/value="IMPORTED"/);
});

test('blood report intake accepts PDF only and uses persisted document contract',async()=>{
  const pdf=new File([new TextEncoder().encode('%PDF-1.7')],'report.pdf',{type:'application/pdf'});
  const image=new File([new Uint8Array([1,2,3])],'report.png',{type:'image/png'});
  assert.equal(await validatePdfFile(pdf),'');
  assert.match(await validatePdfFile(image),/Only PDF/);
  assert.match(intake,/accept="application\/pdf,\.pdf"/);
  assert.doesNotMatch(intake,/analyzeExternalClientIntakeReport/);
  assert.doesNotMatch(intake,/image\/jpeg|image\/png/);
  assert.match(intake,/uploadExternalClientIntakeDocument\(token,'LAB_REPORT',file,idempotencyKey\)/);
  assert.match(intake,/crypto\.subtle\.digest\('SHA-256'/);
  assert.match(proxy,/validateExternalIntakePdfUpload/);
  assert.match(proxy,/content-type:\\s\*application\\\/pdf/);
  assert.match(proxy,/body\.includes\('%PDF-'\)/);
});

test('Diet Plan UI loads and fail-closes on server readiness',()=>{
  assert.match(plans,/getNutritionAssessment\(clientId\)/);
  assert.match(plans,/readiness\.outcome !== 'READY'/);
  assert.match(plans,/bindDietPlanAssessment/);
  assert.doesNotMatch(plans,/Assessment review required/);
  assert.match(plans,/Generate Diet Chart/);
  assert.match(plans,/Promise\.allSettled/);
  assert.match(plans,/Diet plans could not be loaded/);
  assert.match(plans,/No independent Diet Plans have been created/);
  assert.match(plans,/>Retry</);
  assert.match(client360,/Client 360 loaded, but/);
  assert.match(practiceApi,/Your session has expired/);
  assert.match(practiceApi,/x-correlation-id/);
});
