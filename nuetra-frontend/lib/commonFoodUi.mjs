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
  MEAL_QUALITY_SANITY_FAILED: 'This meal does not meet the serving, structure, calorie, or client-facing quality requirements.',
  COMPONENT_ROLE_MISMATCH: 'Choose a replacement from the same meal component role.',
};

export function commonFoodErrorMessage(error, fallback = 'The common-food action could not be completed.') {
  const code = error?.data?.error || error?.data?.code || error?.code;
  if (error?.status === 401 || error?.status === 403) return 'You do not have access to generate or edit a Diet Plan for this client.';
  if (error?.status >= 500) return 'Diet Plan generation is temporarily unavailable. Try again.';
  return COMMON_FOOD_ERROR_MESSAGES[code] || error?.data?.message || error?.message || fallback;
}

export function formatNutrient(value, unit = 'g') {
  if (value === null || value === undefined) return 'Not reported';
  const numeric = Number(value);
  if (!Number.isFinite(numeric)) return 'Not reported';
  return `${Number(numeric.toFixed(1))} ${unit}`;
}

export function optionSummary(option) {
  return option?.humanServingSummary || (option?.components || []).map((component) => `${component.label || `${component.multiplier} × ${component.servingDisplayNameSnapshot}`} ${component.foodDisplayNameSnapshot}`).join(' · ');
}

export function optionTitle(option) {
  const title = option?.clientTitle || (option?.components || []).map((component) => component.foodDisplayNameSnapshot).filter(Boolean).join(' + ');
  return title && !/^Option \d+$/i.test(title) ? title : 'Structured meal';
}

const LEGACY_MEAL_HEADS = {
  earlyMorning: 'EARLY_MORNING', breakfast: 'BREAKFAST', midMorningSnack: 'MID_MORNING',
  lunch: 'LUNCH', eveningSnack: 'EVENING_SNACK', dinner: 'DINNER', bedtimeNutrition: 'BEDTIME',
};

export function commonFoodOptionType(option) {
  if (['LEGACY', 'PREVIOUS_PLAN', 'MANUAL', 'BUILD_MEAL'].includes(option?.sourceType)) return option.sourceType;
  return option?.sourceType === 'VALIDATED_RECIPE' || option?.components?.some((component) => component.sourceType === 'VALIDATED_RECIPE')
    ? 'VALIDATED_RECIPE'
    : 'GENERATED_COMBINATION';
}

const normalizedOptionText = (value) => String(value || '').toLowerCase().normalize('NFKD').replace(/[^a-z0-9]+/g, ' ').trim();

export function optionSemanticIdentity(option = {}) {
  const componentIdentity = (option.components || [])
    .map((component) => [component.foodId, component.servingId, Number(component.multiplier || 1)])
    .filter(([foodId, servingId]) => foodId && servingId)
    .sort((a, b) => JSON.stringify(a).localeCompare(JSON.stringify(b)));
  if (componentIdentity.length) return `COMPONENTS:${JSON.stringify(componentIdentity)}`;
  if (option.optionHash) return `HASH:${option.optionHash}`;
  return `DISPLAY:${normalizedOptionText(option.displayName || option.meal || option.clientTitle)}:${normalizedOptionText(option.servingLabel || option.portion)}`;
}

export function previousOptionReuseState(option = {}) {
  if (option.currentSuitability === 'NOT_SUITABLE' || option.hardConstraintViolation || option.corrupt) {
    return { reusable: false, reason: option.currentSuitabilityReason || 'Not currently suitable for this client.' };
  }
  const components = Array.isArray(option.components) ? option.components : [];
  if (!components.length || components.some((component) => !component.foodId || !component.servingId || !Number.isFinite(Number(component.multiplier)) || Number(component.multiplier) <= 0)) {
    return { reusable: false, reason: 'This historical option has no reusable governed food mapping.' };
  }
  if (option.nutrition?.kcal === null || option.nutrition?.kcal === undefined) return { reusable: false, reason: 'This historical option has an incomplete nutrition snapshot.' };
  const kcal = Number(option.nutrition.kcal);
  if (!Number.isFinite(kcal) || kcal < 0) return { reusable: false, reason: 'This historical option has an invalid nutrition snapshot.' };
  return { reusable: true, reason: '' };
}

export function buildMealAuthoringPool(generated = [], previous = [], limit = 5) {
  const result = [];
  const identities = new Set();
  const append = (option, source) => {
    if (result.length >= limit) return;
    if (source === 'PREVIOUS_PLAN' && !previousOptionReuseState(option).reusable) return;
    const identity = optionSemanticIdentity(option);
    if (identities.has(identity)) return;
    identities.add(identity);
    result.push({ ...option, authoringSource: source });
  };
  generated.forEach((option) => append(option, option.authoringSource || 'GENERATED'));
  previous.forEach((option) => append(option, 'PREVIOUS_PLAN'));
  return result;
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
