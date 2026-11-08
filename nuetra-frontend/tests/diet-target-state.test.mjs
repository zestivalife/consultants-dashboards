import test from 'node:test';
import assert from 'node:assert/strict';
import {applyEnergyEstimate,macroCalories,macroConsistencyAdvisory,targetPayload} from '../lib/dietTargetState.mjs';

test('energy estimate stays separate until explicitly applied',()=>{
  const form={dailyCalories:'1800',activityLevel:'light',energyAdjustment:'0',targetMethodology:'CONSULTANT_MANUAL',calculationProvenance:{}};
  const estimate={adjustedDailyEnergy:2130,activityAssumption:'moderate',energyAdjustmentKcal:100,methodology:'MIFFLIN_ST_JEOR_V1',formulaVersion:'MIFFLIN_ST_JEOR_V1',calculatedAt:'2026-11-08T00:00:00.000Z',inputs:{weightKg:70},bmr:{value:1500},tdee:{value:2030}};
  assert.equal(form.dailyCalories,'1800');
  const applied=applyEnergyEstimate(form,estimate);
  assert.equal(applied.dailyCalories,'2130');
  assert.equal(applied.targetMethodology,'FITEATSY_ESTIMATE');
  assert.equal(applied.calculationProvenance.inputs.weightKg,70);
});

test('manual target payload retains nullable macros and confirmation provenance',()=>{
  const payload=targetPayload({dailyCalories:'1900',dailyProtein:'90',dailyCarbohydrate:'220',dailyFat:'60',dailyFibre:'',activityLevel:'light',energyAdjustment:'-100',targetMethodology:'CONSULTANT_MANUAL',calculationProvenance:{}},'2026-11-08T01:00:00.000Z');
  assert.deepEqual(payload,{daily_calories_target:1900,daily_protein_target_g:90,daily_carbohydrate_target_g:220,daily_fat_target_g:60,daily_fibre_target_g:null,target_methodology:'CONSULTANT_MANUAL',activity_level:'light',energy_adjustment_kcal:-100,calculation_provenance:{source:'CONSULTANT_MANUAL',confirmedAt:'2026-11-08T01:00:00.000Z'}});
});

test('macro energy advisory warns without changing consultant values',()=>{
  assert.equal(macroCalories({protein:100,carbohydrate:200,fat:50}),1650);
  assert.match(macroConsistencyAdvisory({calories:2200,protein:100,carbohydrate:200,fat:50}),/differs/);
  assert.equal(macroConsistencyAdvisory({calories:1650,protein:100,carbohydrate:200,fat:50}),'');
});
