import { validDateOfBirth } from './externalIntakeCorrections.mjs';

export const intakeSections = [
  ['aboutYou','About you'],['medicalHistory','Medical history'],['conditionsSymptoms','Conditions & symptoms'],
  ['allergiesFamilyHistory','Allergies & family history'],['medicationsSupplements','Medicines & supplements'],
  ['lifestyle','Daily routine'],['sleepStress','Sleep & stress'],['activityHydration','Activity & hydration'],
  ['nutrition','Nutrition'],['goals','Your goals'],['measurements','Measurements'],['womensHealth',"Women's health"],
  ['reportsDocuments','Reports'],['review','Review'],['consent','Consent & submit'],
];

export const choices = {
  gender:[['FEMALE','Female'],['MALE','Male'],['OTHER','Other'],['PREFER_NOT_TO_SAY','Prefer not to say']],
  occupationActivity:[['DESK_BASED','Desk-based'],['STANDING_ACTIVE','Standing/Active'],['MANUAL_LABOUR','Manual/Labour'],['MIXED','Mixed'],['STUDENT','Student'],['HOMEMAKER','Homemaker'],['RETIRED','Retired'],['OTHER','Other']],
  conditions:['DIABETES','PRE_DIABETES','THYROID_CONDITION','PCOS','HYPERTENSION','HIGH_CHOLESTEROL','HEART_CONDITION','STROKE_HISTORY','ANAEMIA','ASTHMA','ARTHRITIS','KIDNEY_CONDITION','LIVER_CONDITION','DIGESTIVE_CONDITION','OTHER','NONE','NOT_SURE'],
  symptoms:['FATIGUE','LOW_ENERGY','WEAKNESS','DIZZINESS','HEADACHE','BLOATING','GAS','CONSTIPATION','LOOSE_MOTIONS','ACIDITY','INDIGESTION','ABDOMINAL_DISCOMFORT','LOW_APPETITE','EXCESS_HUNGER','CRAVINGS','NAUSEA','PAIN','SLEEP_DIFFICULTY','OTHER','NO_CURRENT_SYMPTOMS'],
  familyHistory:['DIABETES','HYPERTENSION','HEART_DISEASE','HIGH_CHOLESTEROL','THYROID_DISEASE','CANCER','KIDNEY_DISEASE','STROKE','OTHER','NONE','NOT_SURE'],
  supplementTypes:['VITAMIN_D','VITAMIN_B12','CALCIUM','IRON','MULTIVITAMIN','OMEGA_3','PROTEIN','PROBIOTIC','OTHER'],
  tobacco:['NEVER','PREVIOUSLY','OCCASIONALLY','DAILY'], alcohol:['NEVER','OCCASIONALLY','ONE_TWO_WEEK','THREE_FIVE_WEEK','DAILY'],
  caffeineCount:['NONE','1','2','3','4_PLUS'], caffeineTypes:['TEA','COFFEE','ENERGY_DRINK','OTHER'],
  stressLevel:['LOW','MODERATE','HIGH','VERY_HIGH'], stressSources:['WORK','FAMILY','FINANCIAL','HEALTH','RELATIONSHIPS','STUDIES','SLEEP','OTHER','PREFER_NOT_TO_ANSWER'],
  sleepDuration:['LESS_THAN_5','5_6','6_7','7_8','8_PLUS'], sleepQuality:['POOR','FAIR','GOOD','VERY_GOOD'], sleepConcerns:['DIFFICULTY_FALLING_ASLEEP','WAKE_FREQUENTLY','WAKE_TOO_EARLY','SNORING','DAYTIME_SLEEPINESS','NONE'],
  activityLevel:['MOSTLY_SEDENTARY','LIGHTLY_ACTIVE','MODERATELY_ACTIVE','VERY_ACTIVE'], exerciseTypes:['WALKING','RUNNING','GYM','STRENGTH_TRAINING','YOGA','CYCLING','SWIMMING','SPORTS','OTHER'], exerciseFrequency:['ONE_TWO_DAYS_WEEK','THREE_FOUR_DAYS_WEEK','FIVE_SIX_DAYS_WEEK','DAILY'],
  waterIntake:['LESS_THAN_1_L','1_1_5_L','1_5_2_L','2_2_5_L','2_5_3_L','3_L_PLUS'],
  dietPreference:['VEGETARIAN','EGGITARIAN','NON_VEGETARIAN','VEGAN','OTHER'], restrictions:['JAIN','NO_ONION_GARLIC','HALAL','FASTING_PRACTICES','OTHER','NONE'], intolerances:['DAIRY','GLUTEN_WHEAT','SPICY_FOOD','FRIED_FOOD','CERTAIN_PULSES','NUTS','OTHER','NONE','NOT_SURE'],
  mealsPerDay:['1','2','3','4','5_PLUS'], skipMeals:['NEVER','SOMETIMES','OFTEN'], skippedMeals:['BREAKFAST','LUNCH','DINNER'], eatingOut:['RARELY','ONE_TWO_WEEK','THREE_FOUR_WEEK','FIVE_PLUS_WEEK','MOST_MEALS'], cravings:['SWEET','SALTY','FRIED','SPICY','BAKERY','CHOCOLATE','LATE_NIGHT','OTHER'],
  goals:['LOSE_WEIGHT','GAIN_WEIGHT','GAIN_MUSCLE','MAINTAIN_WEIGHT','BLOOD_SUGAR','PCOS','THYROID','CHOLESTEROL','BLOOD_PRESSURE','DIGESTIVE_HEALTH','MORE_ENERGY','BETTER_SLEEP','BETTER_FITNESS','BETTER_EATING_HABITS','GENERAL_WELLNESS'],
  menstrualStatus:['REGULAR_PERIODS','IRREGULAR_PERIODS','PERIODS_STOPPED','PREGNANT','BREASTFEEDING','PERIMENOPAUSE','MENOPAUSE','PREFER_NOT_TO_ANSWER'], cycleLength:['LESS_THAN_21','21_24','25_28','29_32','33_35','MORE_THAN_35','NOT_SURE'], periodSymptoms:['PAIN','HEAVY_BLEEDING','MOOD_CHANGES','BLOATING','HEADACHE','CRAVINGS','NONE'],
  medicationFrequency:['ONCE_DAILY','TWICE_DAILY','THREE_TIMES_DAILY','WEEKLY','AS_NEEDED','OTHER'],
  treatments:['DIABETES_TREATMENT','THYROID_TREATMENT','BLOOD_PRESSURE_TREATMENT','CHOLESTEROL_TREATMENT','PCOS_TREATMENT','FERTILITY_TREATMENT','PREGNANCY_RELATED_CARE','MENTAL_HEALTH_TREATMENT','PHYSIOTHERAPY','POST_SURGERY_RECOVERY','PAIN_MANAGEMENT','DIGESTIVE_GASTRO_TREATMENT','KIDNEY_TREATMENT','LIVER_TREATMENT','CARDIAC_TREATMENT','RESPIRATORY_TREATMENT','CANCER_TREATMENT','HORMONAL_TREATMENT','OTHER'],
};

export const labelFor=(value)=>String(value).toLowerCase().replaceAll('_',' ').replace(/(^|\s)\S/g,char=>char.toUpperCase()).replace('One Two','1–2').replace('Three Four','3–4').replace('Five Six','5–6').replace('4 Plus','4+').replace('5 Plus','5+');
export const optionPairs=(values)=>(values||[]).map(value=>Array.isArray(value)?value:[value,labelFor(value)]);

const exclusive=new Set(['NONE','NOT_SURE','NO_CURRENT_SYMPTOMS','PREFER_NOT_TO_ANSWER']);
export const toggleMulti=(current,next)=>{
  const values=Array.isArray(current)?current:[];
  if(exclusive.has(next))return values.includes(next)?[]:[next];
  const withoutExclusive=values.filter(value=>!exclusive.has(value));
  return withoutExclusive.includes(next)?withoutExclusive.filter(value=>value!==next):[...withoutExclusive,next];
};

export const resolveNutritionCompatibility=(diet,restrictions=[])=>{
  const clean=[...new Set(restrictions)];
  const conflict=clean.includes('JAIN')&&['NON_VEGETARIAN','EGGITARIAN'].includes(diet);
  return {diet,restrictions:clean,conflict,canChangeToVegetarian:conflict};
};

const LOCATION_MEALS={
  INDIA:{breakfast:['Poha','Upma','Idli','Dosa','Paratha','Oats','Eggs','Bread / Toast'],lunch:['Chapati + Sabzi','Dal + Rice','Khichdi','Vegetable Pulao','Curd Rice','Rajma + Rice','Chole + Rice','Home-style Thali'],dinner:['Chapati + Sabzi','Dal + Rice','Khichdi','Soup + Roti','Vegetable Pulao','Dosa','Grilled Paneer','Light Home Meal'],snacks:['Fruit','Nuts','Tea + Biscuits','Roasted Chana','Makhana','Sandwich','Sprouts','Yoghurt / Curd']},
  MAHARASHTRA:{breakfast:['Poha','Upma','Idli','Dosa','Paratha','Thalipeeth','Sabudana Khichdi','Eggs','Bread / Toast','Oats'],lunch:['Chapati + Sabzi','Dal + Rice','Khichdi','Vegetable Pulao','Curd Rice','Rajma + Rice','Chole + Rice','Non-veg Curry + Rice / Chapati','Salad + Roti','Home-style Thali'],dinner:['Chapati + Sabzi','Dal + Rice','Khichdi','Soup + Roti','Vegetable Pulao','Dosa','Grilled Paneer','Egg preparation','Chicken / Fish + Roti / Rice','Light Home Meal'],snacks:['Fruit','Nuts','Tea + Biscuits','Roasted Chana','Makhana','Chivda','Sandwich','Sprouts','Yoghurt / Curd','Protein Snack']},
};
const TAGS={
  'Eggs':['EGG'],'Egg preparation':['EGG'],'Non-veg Curry + Rice / Chapati':['MEAT'],'Chicken / Fish + Roti / Rice':['MEAT'],
  'Curd Rice':['DAIRY'],'Grilled Paneer':['DAIRY'],'Yoghurt / Curd':['DAIRY'],'Tea + Biscuits':['DAIRY','GLUTEN_WHEAT'],'Bread / Toast':['GLUTEN_WHEAT'],'Paratha':['GLUTEN_WHEAT'],'Chapati + Sabzi':['GLUTEN_WHEAT'],'Salad + Roti':['GLUTEN_WHEAT'],'Soup + Roti':['GLUTEN_WHEAT'],'Fruit':[],'Nuts':['NUTS'],'Makhana':[],
  'Sabudana Khichdi':['ROOT_VEGETABLE'],'Vegetable Pulao':['ONION_GARLIC'],'Dal + Rice':['ONION_GARLIC'],'Khichdi':['ONION_GARLIC'],'Home-style Thali':['ONION_GARLIC'],'Light Home Meal':['ONION_GARLIC'],
};
export const getTypicalMealSuggestions=({meal,location='',dietPreference='',restrictions=[],allergies=[],intolerances=[]})=>{
  const regional=/pune|maharashtra/i.test(location)?LOCATION_MEALS.MAHARASHTRA:LOCATION_MEALS.INDIA;
  const blocked=new Set([...(allergies||[]),...(intolerances||[])]);
  if(dietPreference==='VEGETARIAN'){blocked.add('MEAT');blocked.add('EGG');}
  if(dietPreference==='EGGITARIAN')blocked.add('MEAT');
  if(dietPreference==='VEGAN'){blocked.add('MEAT');blocked.add('EGG');blocked.add('DAIRY');}
  if(restrictions.includes('JAIN')){blocked.add('MEAT');blocked.add('EGG');blocked.add('ONION_GARLIC');blocked.add('ROOT_VEGETABLE');}
  if(restrictions.includes('NO_ONION_GARLIC'))blocked.add('ONION_GARLIC');
  return (regional[meal]||[]).filter(name=>!(TAGS[name]||[]).some(tag=>blocked.has(tag))).slice(0,10);
};

export const sanitiseSection=(section,data)=>{
  const value=structuredClone(data||{});
  if(section==='medicalHistory'){
    if(value.hadSurgery!=='YES')delete value.surgeryProcedure;
    if(value.hospitalised!=='YES')delete value.hospitalisationReason;
    if(value.underTreatment!=='YES'){delete value.treatments;delete value.otherTreatment;delete value.treatmentNote;delete value.treatmentDetails;}
  }
  if(section==='allergiesFamilyHistory'&&value.hasAllergies!=='YES')for(const key of ['allergyTypes','foodAllergies','medicationAllergies','environmentalAllergies','otherAllergy'])delete value[key];
  if(section==='medicationsSupplements'){
    if(value.takesMedication!=='YES')delete value.medications;
    if(value.takesSupplements!=='YES')delete value.supplements;
  }
  if(section==='activityHydration'&&value.intentionalExercise!=='YES'){delete value.exerciseTypes;delete value.exerciseFrequency;}
  if(section==='nutrition'){
    if(value.skipMeals==='NEVER')delete value.skippedMeals;
    if(value.hasCravings!=='YES')delete value.cravings;
  }
  return value;
};

export const validateSection=(section,data,allAnswers={})=>{
  if(section==='aboutYou'){
    if(!data.firstName?.trim()||!data.lastName?.trim()||!data.gender)return 'First name, last name, and gender are required.';
    if(!data.mobile?.trim()&&!data.email?.trim())return 'Add at least one contact method.';
    if(!data.dateOfBirth)return 'Date of birth is required.';
    if(!validDateOfBirth(data.dateOfBirth))return 'Enter a valid date of birth that is not in the future.';
  }
  if(section==='allergiesFamilyHistory'&&data.hasAllergies==='YES'&&!(data.allergyTypes?.length))return 'Choose at least one allergy type.';
  if(section==='medicationsSupplements'&&data.takesMedication==='YES'&&!(data.medications||[]).some(row=>row.name?.trim()))return 'Add the name of each prescribed medicine.';
  if(section==='nutrition'&&resolveNutritionCompatibility(data.dietPreference,data.restrictions).conflict)return 'Resolve the Jain and primary diet selection before continuing.';
  if(section==='goals'&&(!data.goals?.length||!data.primaryGoal))return 'Choose at least one goal and your main priority.';
  if(section==='consent'&&!allAnswers.consent)return 'Please provide consent before submitting.';
  return '';
};

export const auditFields = {
  PILL_SINGLE:21,PILL_MULTI:19,YES_NO:7,SEGMENTED_SCALE:1,STRUCTURED_NUMBER:8,DATE:3,TIME:2,
  SEARCHABLE_SELECT:0,REPEATABLE_STRUCTURED:2,FREE_TEXT_REQUIRED:3,OPTIONAL_NOTES:14,FILE_UPLOAD:1,CONDITIONAL:18,
  OLD_REQUIRED:3,NEW_REQUIRED:7,OPTIONAL:67,
};
