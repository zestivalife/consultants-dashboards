import test from 'node:test';
import assert from 'node:assert/strict';
import {projectConnectedClient360} from '../lib/connectedClient360.mjs';

test('projects a consent-backed Fiteatsy connection into Client 360 without legacy external-client identity',()=>{
  const result=projectConnectedClient360({id:'fc_rest',displayName:'Rest fit',connectionId:'connection-1',status:'CONNECTED_CONSENT_ACTIVE',relationshipStatus:'CONNECTED_CONSENT_ACTIVE'}, {
    profile:{client:{name:'Rest fit',email:'test@fit.com',dob:'1988-01-01',gender:'MALE',status:'active'},onboarding:{height:178,weight:82,goal:'LOSE_WEIGHT',nutrition:{dietaryPreference:'NON_VEGETARIAN',preferredCuisines:['MAHARASHTRIAN'],foodAllergies:[]},lifestyle:{sleepHours:7},healthHistory:{medications:[]}}},
    measurements:{heightCm:178,weightKg:82},healthMetrics:{bmi:{status:'AVAILABLE',value:25.9}},reports:[],
  });
  assert.equal(result.overview.id,'fc_rest');
  assert.equal(result.overview.name,'Rest fit');
  assert.equal(result.sections.nutrition.dietPreference,'NON_VEGETARIAN');
  assert.equal(result.consent.status,'CONNECTED_CONSENT_ACTIVE');
  assert.equal(result.derived.bmi.value,25.9);
});

test('projects canonical Fiteatsy food preferences and assessment status without false missing states',()=>{
  const result=projectConnectedClient360({id:'fc_rest',displayName:'Rest fit',status:'CONNECTED_CONSENT_ACTIVE'}, {
    profile:{client:{name:'Rest fit'},onboarding:{nutrition:{dietaryPreference:'NON_VEGETARIAN',preferredCuisines:['LEGACY']}}},
    foodPreferences:{profile:{dietType:'non_vegetarian',proteins:['Eggs','Chicken'],cuisines:['Maharashtrian','North Indian'],foodsLiked:['Poha'],foodsDisliked:['Oats'],foodsAvoided:['Mushroom'],restrictions:['No onion after sunset'],staplePreference:'both',dairyPreference:'allowed',practicality:['Office-friendly']}},
    assessment:{type:'PSS10',status:'COMPLETED',completedAtISO:'2026-11-04T08:00:00.000Z',instrumentVersion:'PSS10_V1'},
  });
  assert.equal(result.sections.nutrition.dietPreference,'non_vegetarian');
  assert.deepEqual(result.sections.nutrition.proteins,['Eggs','Chicken']);
  assert.deepEqual(result.sections.nutrition.preferredCuisines,['Maharashtrian','North Indian']);
  assert.deepEqual(result.sections.nutrition.foodDislikes,['Oats']);
  assert.deepEqual(result.sections.nutrition.restrictions,['No onion after sunset']);
  assert.equal(result.overview.fiteatsyAssessment.status,'COMPLETED');
});
