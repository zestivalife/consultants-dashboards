export const COMMON_FOOD_MEALS = [
  ['EARLY_MORNING', 'Early Morning'], ['BREAKFAST', 'Breakfast'], ['MID_MORNING', 'Mid-Morning'],
  ['LUNCH', 'Lunch'], ['EVENING_SNACK', 'Evening Snack'], ['DINNER', 'Dinner'], ['BEDTIME', 'Bedtime'],
];

export const COMMON_FOOD_ERROR_MESSAGES = {
  ALLERGY_CONFLICT: 'This food conflicts with a recorded allergy.',
  INTOLERANCE_CONFLICT: 'This food conflicts with a recorded intolerance.',
  HARD_AVOID_CONFLICT: 'This food is on the client’s avoid list.',
  DIET_PATTERN_CONFLICT: 'This food does not match the client’s diet pattern.',
  MEAL_HEAD_INELIGIBLE: 'This food is not eligible for this meal.',
  FOOD_INACTIVE: 'This food is no longer active.',
  SOURCE_INVALID: 'This food does not have an eligible governed source.',
  SERVING_INVALID: 'That serving or multiplier is not available.',
  INVALID_SERVING_MULTIPLIER: 'That serving multiplier is not available.',
  SERVING_NOT_FOUND: 'That serving is not available for this food.',
  UNSAFE_OR_INELIGIBLE_FOOD: 'This food is not eligible for this client and meal.',
  MEAL_TEMPLATE_INVALID: 'This change would break the required meal structure.',
  STALE_PLAN_VERSION: 'A newer plan version exists. Reload before making further changes.',
  VEGAN_COMMON_FOOD_ENGINE_V1_NOT_SUPPORTED: 'Diet Plan generation is not yet available for this diet pattern because a governed Bedtime food source is still required.',
};

export function commonFoodErrorMessage(error, fallback = 'The common-food action could not be completed.') {
  const code = error?.data?.error || error?.data?.code || error?.code;
  if (error?.status === 401 || error?.status === 403) return 'You do not have access to generate or edit a Diet Plan for this client.';
  if (error?.status >= 500) return 'Diet Plan generation is temporarily unavailable. Try again.';
  return COMMON_FOOD_ERROR_MESSAGES[code] || error?.data?.message || error?.message || fallback;
}

export function formatNutrient(value, unit = 'g') {
  return value === null || value === undefined ? 'Not reported' : `${value} ${unit}`;
}

export function optionSummary(option) {
  return (option?.components || []).map((component) => `${component.label || `${component.multiplier} × ${component.servingDisplayNameSnapshot}`} ${component.foodDisplayNameSnapshot}`).join(' · ');
}

const LEGACY_MEAL_HEADS = {
  earlyMorning: 'EARLY_MORNING', breakfast: 'BREAKFAST', midMorningSnack: 'MID_MORNING',
  lunch: 'LUNCH', eveningSnack: 'EVENING_SNACK', dinner: 'DINNER', bedtimeNutrition: 'BEDTIME',
};

export function commonFoodOptionType(option) {
  return option?.sourceType === 'VALIDATED_RECIPE' || option?.components?.some((component) => component.sourceType === 'VALIDATED_RECIPE')
    ? 'VALIDATED_RECIPE'
    : 'GENERATED_COMBINATION';
}

export function legacyOptionsForUnifiedPlan(mealPlan = {}) {
  return Object.entries(LEGACY_MEAL_HEADS).flatMap(([mealKey, mealHead]) =>
    (mealPlan?.[mealKey]?.options || []).map((option, index) => ({
      ...option,
      combinationId: `legacy:${mealKey}:${option.id || index}`,
      mealHead,
      sourceType: 'LEGACY',
      displayName: option.meal || `Option ${index + 1}`,
      servingLabel: option.portion || 'Serving not set',
      nutrition: {
        kcal: option.approxKcal ?? null,
        protein: option.proteinGrams ?? null,
        carbohydrate: option.carbohydratesGrams ?? option.carbsGrams ?? null,
        fat: option.fatGrams ?? null,
        fibre: option.fibreGrams ?? null,
      },
    })),
  );
}
