const SHARED=['clients','consultations','followups','goals','tasks','calendar','communication','professionIntake'];
const PROFILES={
  DIETITIAN:['Dietitian','Consultation','Goal',['Nutrition','Diet Plan','Measurements','Biomarkers'],'No consultations recorded yet.'],
  NUTRITIONIST:['Nutritionist','Consultation','Goal',['Nutrition','Diet Plan','Measurements','Biomarkers'],'No consultations recorded yet.'],
  DIABETES_EDUCATOR:['Diabetes Educator','Education session','Education goal',['Metabolic Profile','Biomarkers','Education Plan','Lifestyle','Progress'],'No education sessions recorded yet.'],
  PSYCHOLOGIST:['Psychologist','Session','Therapy goal',['Assessments','Sessions','Therapy Plan','Private Notes','Progress'],'No sessions recorded yet.'],
  PHYSIOTHERAPIST:['Physiotherapist','Physio session','Rehab goal',['Pain & Function','Physical Assessment','Exercise','Rehab Plan','Progress'],'No physical assessments recorded yet.'],
  HEALTH_COACH:['Health Coach','Coaching session','Coaching goal',['Coaching Profile','Check-ins','Habits','Goals','Progress'],'No coaching check-ins yet.'],
  WELLNESS_CONSULTANT:['Wellness Consultant','Wellness review','Wellness goal',['Wellness Profile','Habits','Wellness Plan','Progress'],'No wellness reviews recorded yet.'],
  BEHAVIOURAL_THERAPIST:['Behavioural Therapist','Behaviour review','Behaviour goal',['Behaviour Profile','Behaviour Logs','Intervention Plan','Progress'],'No behaviour reviews recorded yet.'],
  OCCUPATIONAL_THERAPIST:['Occupational Therapist','OT session','Functional goal',['Functional Profile','ADL','Activities','OT Plan','Progress'],'No functional assessments recorded yet.'],
  MENTAL_WELLNESS_THERAPIST:['Mental Wellness Consultant / Therapist','Wellbeing session','Wellbeing goal',['Wellbeing','Sessions','Goals','Support Plan','Progress'],'No wellbeing sessions recorded yet.'],
};
export function resolveProfessionExperience(code='OTHER',configuration={}){
  const [label,session,goal,panels,empty]=PROFILES[code]||['Healthcare Professional','Consultation','Goal',[],'No consultations recorded yet.'];
  const capabilities=new Set(configuration.capabilities||SHARED);
  const care=['consultations','followups','goals','tasks'].filter(item=>capabilities.size===0||capabilities.has(item)||capabilities.has(item.toUpperCase()));
  return {code,label,session,goal,panels,empty,care,capabilities,terminology:{consultation:configuration.terminology?.consultation||session,goal:configuration.terminology?.goal||goal,plan:configuration.terminology?.plan||'Care Plan'}};
}
export const PROFESSION_OPTIONS=Object.entries(PROFILES).map(([value,[label]])=>[value,label]);
