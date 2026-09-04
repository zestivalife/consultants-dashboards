const COMMON_FOOD_FLAG = process.env.NEXT_PUBLIC_COMMON_FOOD_COMBINATION_ENGINE_V1;

// Common Food V1 is the accepted production authoring path. An explicit false
// disables candidate generation without changing historical read compatibility.
export const isCommonFoodCombinationEngineEnabled = COMMON_FOOD_FLAG !== 'false';
