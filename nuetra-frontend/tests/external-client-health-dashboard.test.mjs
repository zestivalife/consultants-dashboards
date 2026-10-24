import assert from 'node:assert/strict';
import test from 'node:test';
import {buildHealthTimeline,buildReviewPriorities,currentMeasurementRows,measurementSeries,measurementTrend} from '../lib/externalClientHealthDashboard.mjs';

const row=(id,type,value,date,version=1,series=id)=>({id,series_id:series,measurement_type:type,value,unit:type==='WEIGHT_KG'?'kg':'cm',measured_at:date,created_at:date,version,source:'PROFESSIONALLY_RECORDED'});

test('measurement history keeps current corrections and chronological same-day entries',()=>{
  const history=[row('old','WEIGHT_KG',70,'2026-01-01T08:00:00Z',1,'series-1'),row('corrected','WEIGHT_KG',71,'2026-01-01T08:00:00Z',2,'series-1'),row('later','WEIGHT_KG',72,'2026-01-01T18:00:00Z')];
  assert.deepEqual(currentMeasurementRows(history).map(item=>item.id),['corrected','later']);
  assert.equal(measurementSeries(history).WEIGHT_KG.length,2);
  assert.deepEqual(measurementTrend(measurementSeries(history).WEIGHT_KG),{latest:history[2],previous:history[1],absoluteChange:1,percentageChange:1.41});
});

test('invalid and unsupported measurements are excluded without false zeroes',()=>{
  const history=[row('zero','WAIST_CM',0,'2026-01-01T00:00:00Z'),row('bad','WAIST_CM','invalid','2026-01-02T00:00:00Z'),row('unsupported','BODY_FAT',20,'2026-01-03T00:00:00Z')];
  assert.deepEqual(currentMeasurementRows(history),[]);
  assert.equal(measurementTrend([]).latest,null);
});

test('timeline uses only source-backed timestamps and sorts newest first',()=>{
  const events=buildHealthTimeline({enrichment:{version:2,provenance:{updated_at:'2026-01-03T00:00:00Z',source:'PROFILE'}},measurements:{history:[row('w','WEIGHT_KG',72,'2026-01-02T00:00:00Z')]},biomarkers:[{id:'b',name:'HbA1c',value:5.4,unit:'%',status:'CONFIRMED',observationDate:'2026-01-04'}],documents:[{id:'no-date',name:'Undated'}]});
  assert.deepEqual(events.map(event=>event.type),['BIOMARKER','PROFILE_UPDATE','MEASUREMENT']);
  assert.equal(events.some(event=>event.id==='document-no-date'),false);
});

test('review priorities are factual and identify stale or missing records',()=>{
  const stale=buildReviewPriorities({missingChecklist:[{label:'Medical history',category:'medicalBackground'}],measurements:{history:[row('w','WEIGHT_KG',70,'2025-01-01T00:00:00Z')]},pendingReports:2,now:Date.parse('2026-01-01T00:00:00Z')});
  assert.deepEqual(stale.map(item=>item.code),['MISSING_MEDICAL_HISTORY','STALE_MEASUREMENTS','UNREVIEWED_REPORTS']);
  const empty=buildReviewPriorities({measurements:{history:[]}});
  assert.equal(empty[0].code,'MISSING_MEASUREMENTS');
});
