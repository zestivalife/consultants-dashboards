const present = (value) => value !== undefined && value !== null && value !== '' && !(Array.isArray(value) && value.length === 0);
const list = (value) => Array.isArray(value) ? value.filter(Boolean).map((item) => typeof item === 'object' ? item.name || item.code || item.value : item).filter(Boolean) : present(value) ? [value] : [];
const first = (...values) => values.find((value) => present(value) || value === 0 || value === false);
const WEIGHT_GOALS = new Set(['LOSE_WEIGHT','GAIN_WEIGHT','GAIN_MUSCLE','MAINTAIN_WEIGHT']);
const ARRAY_FIELDS = new Set(['allergies_intolerances','food_restrictions','appetite_eating_patterns','food_dislikes_preferences','nutrition_medical_conditions','relevant_medications','relevant_supplements','weight_management_goals','recovery_disease_management_goals']);

export function canonicalAssessmentFromOnboarding(sections = {}) {
  const nutrition = sections.nutrition || {};
  const allergyStatus = first(sections.allergiesFamilyHistory?.hasAllergies);
  let allergies = list(sections.allergiesFamilyHistory?.foodAllergies);
  if (!allergies.length && ['NO','NOT_SURE'].includes(allergyStatus)) allergies = [allergyStatus];
  const meals = ['breakfast','lunch','dinner','snacks']
    .filter((key) => present(nutrition[key]))
    .map((key) => `${key}: ${list(nutrition[key]).join(', ')}`)
    .join('; ');
  const skip = nutrition.skipMeals;
  const patterns = skip === 'NEVER' ? ['NONE'] : ['SOMETIMES','OFTEN'].includes(skip) ? ['SKIPS_MEALS', ...list(nutrition.skippedMeals)] : [];
  const medicationRows = first(sections.medicationsSupplements?.medications, []);
  const goals = list(first(sections.goals?.goals, sections.goals?.selectedGoals));
  const waterMl = first(sections.activityHydration?.waterIntakeMl);
  return {
    dietary_preference: nutrition.dietPreference === 'EGGITARIAN' ? 'EGG' : nutrition.dietPreference,
    allergies_intolerances: allergies,
    food_restrictions: list(nutrition.restrictions),
    meal_timing_frequency: present(nutrition.mealsPerDay) ? String(nutrition.mealsPerDay) : null,
    typical_dietary_intake: first(nutrition.typicalDietaryIntake, meals),
    appetite_eating_patterns: patterns,
    water_intake: typeof waterMl === 'number' ? `${waterMl / 1000} L/day` : null,
    food_dislikes_preferences: list(first(nutrition.foodDislikesPreferences, nutrition.foodDislikes)),
    nutrition_medical_conditions: list(first(sections.conditionsSymptoms?.conditions, sections.medicalHistory?.conditions)),
    relevant_medications: list(medicationRows),
    relevant_supplements: list(first(sections.medicationsSupplements?.supplementTypes, sections.medicationsSupplements?.supplements)),
    weight_management_goals: goals.filter((goal) => WEIGHT_GOALS.has(goal)),
    recovery_disease_management_goals: goals.filter((goal) => !WEIGHT_GOALS.has(goal)),
  };
}

export function resolveNutritionAssessment(onboardingSections = {}, assessment = {}, serverProvenance = {}) {
  const onboarding = canonicalAssessmentFromOnboarding(onboardingSections);
  const keys = new Set([...Object.keys(onboarding), ...Object.keys(assessment), 'consultant_notes']);
  const values = {};
  const provenance = {};
  for (const key of keys) {
    const professional = assessment[key];
    if (present(professional) || professional === 0 || professional === false) {
      values[key] = professional;
      provenance[key] = serverProvenance[key] || {source:'CONSULTANT_ASSESSMENT', confirmed:false};
    } else if (present(onboarding[key]) || onboarding[key] === 0 || onboarding[key] === false) {
      values[key] = onboarding[key];
      provenance[key] = {source:'CLIENT_SUBMITTED', confirmed:false};
    } else {
      values[key] = ARRAY_FIELDS.has(key) ? [] : '';
      provenance[key] = {source:null, confirmed:false};
    }
  }
  return {values, provenance};
}

const FIELD_TO_ASSESSMENT = {
  dietary_preference:'dietary_preference', food_restrictions:'food_restrictions', food_allergies:'allergies_intolerances',
  allergy_status:'allergies_intolerances', meal_timing_frequency:'meal_timing_frequency', typical_dietary_intake:'typical_dietary_intake',
  appetite_eating_patterns:'appetite_eating_patterns', water_intake:'water_intake', medical_conditions:'nutrition_medical_conditions',
  medications:'relevant_medications', supplements:'relevant_supplements', health_goals:'weight_management_goals',
};

export function reconcileCompleteness(serverValue, resolved) {
  if (!serverValue?.fields) return serverValue;
  const fields = serverValue.fields.map((field) => {
    const assessmentKey = FIELD_TO_ASSESSMENT[field.field_id];
    const value = field.field_id === 'health_goals'
      ? [...list(resolved.values.weight_management_goals), ...list(resolved.values.recovery_disease_management_goals)]
      : resolved.values[assessmentKey];
    if (!present(value) && value !== 0 && value !== false) return field;
    return {...field, status: field.status === 'PENDING_CONSULTANT_REVIEW' ? field.status : 'CAPTURED', current_value:value, source:resolved.provenance[assessmentKey]?.source || 'CLIENT_SUBMITTED', reason:null, blocks_readiness:false};
  });
  const counts = Object.fromEntries(Object.keys(serverValue.counts || {}).map((status) => [status, fields.filter((field) => field.status === status).length]));
  const blocking_fields = fields.filter((field) => field.blocks_readiness).map((field) => field.field_id);
  return {...serverValue, fields, counts, blocking_fields, readiness:blocking_fields.length ? 'NEEDS_INFORMATION' : 'NEEDS_CONSULTANT_REVIEW'};
}
