const numeric = (value) => typeof value === 'number' && Number.isFinite(value) ? value : null;

export function externalDietOptionTitle(option = {}) {
  const componentTitle = Array.isArray(option.components)
    ? option.components.map((component) => component?.foodDisplayNameSnapshot).filter(Boolean).join(' + ')
    : '';
  return String(option.clientTitle || componentTitle).trim();
}

export function externalDietOptionServing(option = {}) {
  if (option.humanServingSummary) return String(option.humanServingSummary);
  if (!Array.isArray(option.components)) return '';
  return option.components
    .map((component) => component?.servingDisplayNameSnapshot)
    .filter(Boolean)
    .join(' · ');
}

export function externalDietOptionNutrition(option = {}) {
  const nutrition = option.nutrition || {};
  return {
    kcal: numeric(nutrition.kcal),
    protein: numeric(nutrition.protein),
    carbohydrate: numeric(nutrition.carbohydrate),
    fat: numeric(nutrition.fat),
  };
}

export function validateExternalDietOption(option = {}) {
  const title = externalDietOptionTitle(option);
  const nutrition = externalDietOptionNutrition(option);
  const canonicalFoodIds = Array.isArray(option.components)
    ? option.components.map((component) => component?.foodId).filter(Boolean)
    : [];
  return {
    title,
    serving: externalDietOptionServing(option),
    nutrition,
    canonicalFoodIds,
    valid: Boolean(option.combinationId && title && canonicalFoodIds.length && nutrition.kcal !== null),
  };
}
