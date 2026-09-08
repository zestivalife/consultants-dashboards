import { COMMON_FOOD_MEALS } from './commonFoodUi.mjs';

export function buildDailyCalorieModel({ dailyTargetKcal = null, mealTargets = {}, options = [] }) {
  const extrema = COMMON_FOOD_MEALS.map(([mealHead]) => {
    const values = options.filter((option) => option.mealHead === mealHead).map((option) => option.nutrition?.kcal ?? null);
    return values.length && values.every((value) => value !== null)
      ? { mealHead, minimumKcal: Math.min(...values), maximumKcal: Math.max(...values) }
      : { mealHead, minimumKcal: null, maximumKcal: null };
  });
  const rangeComplete = extrema.every(({ minimumKcal, maximumKcal }) => minimumKcal !== null && maximumKcal !== null);
  const minimumDailyKcal = rangeComplete ? extrema.reduce((total, { minimumKcal }) => total + minimumKcal, 0) : null;
  const maximumDailyKcal = rangeComplete ? extrema.reduce((total, { maximumKcal }) => total + maximumKcal, 0) : null;
  const chosen = COMMON_FOOD_MEALS.map(([mealHead]) => options.filter((option) => option.mealHead === mealHead && option.authoritativeDailyChoice === true));
  const selectedDailyComplete = chosen.every((mealOptions) => mealOptions.length === 1 && mealOptions[0].nutrition?.kcal != null);
  const selectedDailyKcal = selectedDailyComplete ? chosen.reduce((total, mealOptions) => total + mealOptions[0].nutrition.kcal, 0) : null;
  const maximumDifferenceKcal = maximumDailyKcal !== null && dailyTargetKcal !== null ? maximumDailyKcal - dailyTargetKcal : null;
  const selectedDifferenceKcal = selectedDailyKcal !== null && dailyTargetKcal !== null ? selectedDailyKcal - dailyTargetKcal : null;
  return {
    dailyTargetKcal,
    mealTargets,
    minimumDailyKcal,
    maximumDailyKcal,
    rangeComplete,
    rangeAdvisory: maximumDifferenceKcal > 0 ? `Some meal combinations may exceed the daily target. Maximum planned combination is ${maximumDifferenceKcal} kcal above target.` : null,
    selectedDailyKcal,
    selectedDailyComplete,
    selectedDailyAdvisory: selectedDifferenceKcal > 0 ? `Daily calorie target exceeded by ${selectedDifferenceKcal} kcal.` : null,
  };
}
