import test from 'node:test';
import assert from 'node:assert/strict';
import {CONSULTANT_FEATURE_VISIBILITY,filterConsultantNavigation,isConsultantViewVisible,resolveConsultantFeatureVisibility} from '../lib/consultantFeatureVisibility.mjs';

const navigation=[['clients','Clients'],['reports','Reports'],['automations','Automations'],['settings','Settings']];

test('MP-011 hides configured consultant surfaces without deleting definitions',()=>{
  assert.deepEqual(filterConsultantNavigation(navigation).map(([id])=>id),['clients']);
  assert.equal(isConsultantViewVisible('reports'),false);
  assert.equal(CONSULTANT_FEATURE_VISIBILITY.neckMeasurement,false);
});

test('MP-011 features are restored through configuration only',()=>{
  const enabled=resolveConsultantFeatureVisibility({standaloneReports:true,automations:true,practiceSettings:true,neckMeasurement:true,governedPermissionCounts:true,personalHealthProfileFields:true});
  assert.deepEqual(filterConsultantNavigation(navigation,enabled).map(([id])=>id),['clients','reports','automations','settings']);
  assert.equal(enabled.neckMeasurement,true);
});
