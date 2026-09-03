export type MealHead = 'EARLY_MORNING' | 'BREAKFAST' | 'MID_MORNING' | 'LUNCH' | 'EVENING_SNACK' | 'DINNER' | 'BEDTIME';
export type CoverageStatus = 'COMPLETE' | 'SHORTAGE';
export type Nutrition = { kcal: number | null; protein: number | null; carbohydrate: number | null; fat: number | null; fibre: number | null };
export type Serving = { id: string; label: string; grams: number; allowedMultipliers: number[]; active: boolean; isDefault: boolean };
export type MealComponent = { componentId: string; foodId: string; foodDisplayNameSnapshot: string; servingId: string; servingDisplayNameSnapshot: string; multiplier: number; grams: number; label: string; nutrition: Nutrition };
export type CommonFoodOption = { combinationId: string; mealHead: MealHead; components: MealComponent[]; nutrition: Nutrition; sourceType?: 'GENERATED_COMBINATION' | 'MANUAL_COMBINATION' | 'VALIDATED_RECIPE'; snapshotVersion?: number };
export type CatalogueFood = { id: string; displayName: string; category: string; family: string; roles: string[]; mealHeads: MealHead[]; servings: Serving[]; nutritionPer100g: Nutrition };
