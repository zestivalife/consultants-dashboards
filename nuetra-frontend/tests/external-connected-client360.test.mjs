import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

import { externalClient360Base, externalConnectedBiomarkerHistory, externalConnectedBiomarkers, externalConnectedHealthRecords } from '../lib/externalClientProfile.mjs';
import { contentDispositionFilename } from '../lib/contentDisposition.mjs';

const component = fs.readFileSync(new URL('../components/external/ExternalClient360.jsx', import.meta.url), 'utf8');
const enhancements = fs.readFileSync(new URL('../components/external/ExternalClientProfileEnhancements.jsx', import.meta.url), 'utf8');

test('connected external Client 360 uses the consented Practice Operations health context', () => {
  assert.match(component, /loadAuthorizedClient360\(client,getFiteatsyConnectionHealthContext\)/);
  const initialLoad = component.match(/const load = async \(\) => \{[\s\S]*?\n  const loadPendingReportReviews/)?.[0] || '';
  assert.doesNotMatch(initialLoad, /getExternalClient360\(client\.id\)/);
});

test('directory and consented health data produce an explicit Client 360 base projection', () => {
  const result = externalClient360Base({
    id: 'client-1',
    displayName: 'QA Client',
    status: 'CONNECTED_CONSENT_ACTIVE',
    email: 'qa@example.test',
    consentedScopes: ['PROFILE', 'HEALTH_SUMMARY'],
  }, {
    generatedAt: '2026-11-01T12:00:00Z',
    profile: { dateOfBirth: '1990-01-02', gender: 'FEMALE' },
    healthProfile: { medicalHistory: { conditions: ['asthma'] } },
    reports: [{ id: 'report-1', reportType: 'medical_report' }],
    timeline: [{ id: 'event-1' }],
  });

  assert.equal(result.overview.name, 'QA Client');
  assert.equal(result.overview.documentCount, 1);
  assert.equal(result.basicProfile.name.value, 'QA Client');
  assert.equal(result.basicProfile.name.sourceLabel, 'Fiteatsy');
  assert.equal(result.sections.medicalHistory.conditions[0], 'asthma');
  assert.equal(result.documents[0].id, 'report-1');
  assert.equal(result.consent.source, 'FITEATSY_CONNECTION');
});

test('an unconnected directory client does not receive fabricated health data', () => {
  const result = externalClient360Base({ id: 'client-2', name: 'Directory Client' });
  assert.equal(result.overview.name, 'Directory Client');
  assert.deepEqual(result.documents, []);
  assert.deepEqual(result.sections.medicalHistory, {});
  assert.equal(result.consent.source, 'PRACTICE_DIRECTORY');
});

test('nested Fiteatsy profile, measurements and nutrition populate the original Client 360 contract', () => {
  const result = externalClient360Base({ displayName: 'Connected Client' }, {
    profile: {
      client: { dob: '1992-03-04', gender: 'FEMALE' },
      onboarding: {
        goal: 'Improve energy', activityLevel: 'ACTIVE', medicalConditions: ['asthma'],
        nutrition: { dietaryPreference: 'VEGETARIAN', foodAllergies: ['peanut'] },
        lifestyle: { sleepHours: 7, stressLevel: 'MODERATE' },
        healthHistory: { medications: ['inhaler'] },
      },
    },
    measurements: { heightCm: 165, weightKg: 62 },
  });
  assert.equal(result.overview.dateOfBirth, '1992-03-04');
  assert.deepEqual(result.sections.conditionsSymptoms.conditions, ['asthma']);
  assert.equal(result.sections.nutrition.dietaryPreference, 'VEGETARIAN');
  assert.deepEqual(result.sections.allergiesFamilyHistory.allergies, ['peanut']);
  assert.equal(result.sections.measurements.weightKg, 62);
});

test('consented Fiteatsy biomarkers retain clinical values in the original biomarker contract', () => {
  const result = externalConnectedBiomarkers({ biomarkers: [{ biomarkerId: 'hba1c', name: 'HbA1c', value: 5.6, unit: '%', clinicalStatus: 'NORMAL', testDate: '2026-10-01', referenceRange: '4.0–5.6' }] });
  assert.equal(result.length, 1);
  assert.equal(result[0].canonicalBiomarkerId, 'hba1c');
  assert.equal(result[0].observationDate, '2026-10-01');
  assert.equal(result[0].reviewStatus, 'CONFIRMED');
  assert.equal(result[0].source, 'FITEATSY_CONNECTION');
});

test('all 51 authorised biomarkers are projected without truncation', () => {
  const biomarkers=Array.from({length:51},(_,index)=>({biomarkerId:`marker-${index}`,name:`Marker ${index}`,value:index,unit:'unit'}));
  assert.equal(externalConnectedBiomarkers({biomarkers}).length,51);
});

test('connected biomarker history includes only supplied observations', () => {
  const context={biomarkers:[{biomarkerId:'hba1c',name:'HbA1c',value:5.6,unit:'%',testDate:'2026-10-27',previousValue:5.8,previousTestDate:'2026-09-27'}]};
  const rows=externalConnectedBiomarkerHistory(context,{canonicalBiomarkerId:'hba1c'});
  assert.deepEqual(rows.map(item=>item.value),[5.6,5.8]);
  assert.deepEqual(externalConnectedBiomarkerHistory({biomarkers:[context.biomarkers[0]]},{canonicalBiomarkerId:'missing'}),[]);
});

test('connected biomarker history preserves every authorised canonical history row', () => {
  const context={biomarkers:[{biomarkerId:'hba1c',name:'HbA1c',value:5.6,unit:'%',history:[
    {observationId:'obs-3',value:5.6,unit:'%',testDate:'2026-10-27',clinicalStatus:'NORMAL'},
    {observationId:'obs-2',value:5.8,unit:'%',testDate:'2026-09-27',clinicalStatus:'HIGH'},
    {observationId:'obs-1',value:6.1,unit:'%',testDate:'2026-08-27',clinicalStatus:'HIGH'},
  ]}]};
  const rows=externalConnectedBiomarkerHistory(context,{canonicalBiomarkerId:'hba1c'});
  assert.deepEqual(rows.map(item=>item.id),['obs-3','obs-2','obs-1']);
  assert.deepEqual(rows.map(item=>item.value),[5.6,5.8,6.1]);
  assert.equal(rows.every(item=>item.source==='FITEATSY_CONNECTION'),true);
});

test('connected profile retains the complete consented health and nutrition projection', () => {
  const result=externalClient360Base({display_name:'Canonical Client'}, {profile:{
    client:{dob:'1990-01-02',gender:'FEMALE'},
    onboarding:{
      bodyComposition:{goalWeightKg:58,waistCm:78,hipCm:94,armCircumferenceCm:27},
      work:{occupation:'Designer',workMode:'Hybrid'},
      nutrition:{regionalCuisine:'Maharashtrian',foodsLiked:['Poha'],foodIntolerances:['Lactose'],supplements:['Vitamin B12'],breakfastTime:'08:00'},
      healthHistory:{medications:['Vitamin D3']},
    },
  },healthMetrics:{bmr:{status:'AVAILABLE',value:1320,unit:'kcal/day'},tdee:{status:'AVAILABLE',value:1815,unit:'kcal/day'}}});
  assert.equal(result.overview.name,'Canonical Client');
  assert.equal(result.sections.aboutYou.occupation,'Designer');
  assert.equal(result.sections.measurements.goalWeightKg,58);
  assert.deepEqual(result.sections.nutrition.foodsLiked,['Poha']);
  assert.deepEqual(result.sections.medicationsSupplements.supplements,['Vitamin B12']);
  assert.equal(result.healthMetrics.tdee.value,1815);
  assert.match(enhancements,/label="BMR"/);
  assert.match(enhancements,/label="TDEE"/);
});

test('connected reports map to read-only dated evidence records with exact observations', () => {
  const records=externalConnectedHealthRecords({
    reports:[{report_id:'report-1',reportType:'LAB_ANALYSIS',reportDate:'2026-10-27'}],
    biomarkers:[{biomarkerId:'alt',name:'ALT',value:20,unit:'U/L',report_id:'report-1'}],
  });
  assert.equal(records[0].id,'report-1');
  assert.equal(records[0].biomarkerCount,1);
  assert.equal(records[0].observations[0].value,20);
  assert.equal(records[0].connectionScoped,true);
});

test('connected evidence records retain factual report lifecycle timestamps', () => {
  const records=externalConnectedHealthRecords({reports:[{
    id:'report-1',uploadedAt:'2026-10-27T15:30:00Z',completedAt:'2026-10-27T15:35:00Z',
  }]});
  assert.equal(records[0].reportDate,'2026-10-27T15:30:00Z');
  assert.equal(records[0].confirmedAt,'2026-10-27T15:35:00Z');
});

test('connected Client 360 binds health records and does not expose a mutable connection status selector', () => {
  assert.match(component,/documents=\{data\.documents\|\|\[\]\}/);
  assert.match(component,/!client\.connectionId&&<select aria-label="Client status"/);
  assert.match(component,/loadAuthorizedClient360\(client,getFiteatsyConnectionHealthContext\)/);
  assert.doesNotMatch(component,/getExternalClient360\(client\.id\)/);
});

test('connected report download uses the browser document instead of shadowing it with report data', () => {
  assert.match(component,/const downloadDocument=async\(report\)/);
  assert.match(component,/window\.document\.createElement\('a'\)/);
  assert.doesNotMatch(component,/downloadDocument=async\(document\)/);
});

test('connected report download preserves RFC 5987 and legacy response filenames', () => {
  assert.equal(contentDispositionFilename("attachment; filename*=UTF-8''Pitambar_Paunikar.pdf",'fallback.pdf'),'Pitambar_Paunikar.pdf');
  assert.equal(contentDispositionFilename('attachment; filename="Kirti%20Paunikar.pdf"','fallback.pdf'),'Kirti%20Paunikar.pdf');
  assert.equal(contentDispositionFilename('', 'fallback.pdf'),'fallback.pdf');
});

test('connected report identifiers and profile names support canonical API aliases', () => {
  const result=externalClient360Base({healthDataAuthorized:true},{
    profile:{client:{first_name:'Priyanshi',last_name:'Zestiva'}},
    reports:[{report_id:'report-1',fileName:'lab.pdf'}],
    consent:{status:'ACTIVE'},
  });
  assert.equal(result.overview.name,'Priyanshi Zestiva');
  assert.equal(result.documents[0].id,'report-1');
  assert.equal(result.consent.status,'ACTIVE');
});

test('authorised Fiteatsy profile name replaces directory placeholder without fabricating identity', () => {
  const named=externalClient360Base({displayName:'Unnamed client'}, {
    profile:{client:{name:'Kirti'}},
  });
  assert.equal(named.overview.name,'Kirti');
  assert.equal(named.basicProfile.name.value,'Kirti');

  const missing=externalClient360Base({displayName:'No contact provided'}, {
    profile:{client:{name:null,first_name:null,last_name:null}},
  });
  assert.equal(missing.overview.name,'Unnamed client');
});
