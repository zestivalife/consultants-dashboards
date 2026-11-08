const optionalNumber=(value)=>value===''||value==null?null:Number(value);

export const macroCalories=({protein,carbohydrate,fat})=>{
  const values=[protein,carbohydrate,fat].map(optionalNumber);
  if(values.some((value)=>value==null||!Number.isFinite(value)||value<0))return null;
  return values[0]*4+values[1]*4+values[2]*9;
};

export const macroConsistencyAdvisory=(targets)=>{
  const target=optionalNumber(targets.calories);
  const calculated=macroCalories(targets);
  if(target==null||calculated==null||target<=0)return '';
  const difference=Math.abs(calculated-target);
  return difference/target>0.1
    ?`Macro energy is ${Math.round(calculated)} kcal, which differs from the daily target by ${Math.round(difference)} kcal. Review before saving.`
    :'';
};

export const applyEnergyEstimate=(form,estimate)=>({
  ...form,
  dailyCalories:String(estimate.adjustedDailyEnergy),
  activityLevel:estimate.activityAssumption,
  energyAdjustment:String(estimate.energyAdjustmentKcal),
  targetMethodology:'FITEATSY_ESTIMATE',
  calculationProvenance:{
    source:'FITEATSY_AUTHORITATIVE_HEALTH_CALCULATION',
    methodology:estimate.methodology,
    formulaVersion:estimate.formulaVersion,
    calculatedAt:estimate.calculatedAt,
    inputs:estimate.inputs,
    basalMetabolicRate:estimate.bmr,
    estimatedTdee:estimate.tdee,
  },
});

export const targetPayload=(form,confirmedAt)=>({
  daily_calories_target:Number(form.dailyCalories),
  daily_protein_target_g:Number(form.dailyProtein),
  daily_carbohydrate_target_g:optionalNumber(form.dailyCarbohydrate),
  daily_fat_target_g:optionalNumber(form.dailyFat),
  daily_fibre_target_g:optionalNumber(form.dailyFibre),
  target_methodology:form.targetMethodology,
  activity_level:form.activityLevel||null,
  energy_adjustment_kcal:optionalNumber(form.energyAdjustment),
  calculation_provenance:form.targetMethodology==='FITEATSY_ESTIMATE'
    ?form.calculationProvenance
    :{source:'CONSULTANT_MANUAL',confirmedAt},
});
