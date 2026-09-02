const DIET_TYPE_LABELS = {
  vegetarian: 'Vegetarian',
  eggetarian: 'Eggetarian',
  non_vegetarian: 'Non-Vegetarian',
  vegan: 'Vegan',
  jain: 'Jain',
};

const STAPLE_LABELS = {
  roti: 'Roti',
  rice: 'Rice',
  both: 'Roti and Rice',
  none: 'None',
};

const DAIRY_LABELS = {
  allowed: 'Allowed',
  limited: 'Limited',
  avoid: 'Avoid',
};

const list = (value) => (Array.isArray(value) ? value.map(String) : []);
const enumLabel = (labels, value) => (value == null ? null : labels[value] || String(value));

export function mapConsultantFoodPreferences(workspace) {
  const canonical = workspace?.foodPreferences;
  const profile = canonical?.profile;
  const healthProfile = workspace?.healthProfile;
  if (!profile && !healthProfile) return null;

  return {
    status: canonical?.status || 'NOT_SET',
    updatedAtISO: canonical?.updatedAtISO || null,
    source: 'Fiteatsy canonical client profile',
    hard: {
      dietPattern: enumLabel(DIET_TYPE_LABELS, profile?.dietType),
      avoidedFoods: list(profile?.foodsAvoided),
      avoidedFoodIds: list(profile?.avoidedFoodIds),
      allergies: list(healthProfile?.foodAllergies),
      intolerances: list(healthProfile?.foodIntolerances),
      restrictions: list(profile?.restrictions),
    },
    soft: {
      preferredCuisines: list(profile?.cuisines),
      staplePreference: enumLabel(STAPLE_LABELS, profile?.staplePreference),
      dairyPreference: enumLabel(DAIRY_LABELS, profile?.dairyPreference),
      preferredProteins: list(profile?.proteins),
      likes: list(profile?.foodsLiked),
      likedFoodIds: list(profile?.likedFoodIds),
      dislikes: list(profile?.foodsDisliked),
      dislikedFoodIds: list(profile?.dislikedFoodIds),
      practicality: list(profile?.practicality),
    },
  };
}

export function foodPreferenceSections(preferences) {
  const hard = preferences?.hard || {};
  const soft = preferences?.soft || {};
  return [
    {
      key: 'hard',
      title: 'Hard constraints',
      description: 'Safety, explicit exclusions, and dietary restrictions.',
      fields: [
        ['Diet Pattern', hard.dietPattern],
        ['Avoided Foods', hard.avoidedFoods],
        ['Allergies', hard.allergies],
        ['Intolerances', hard.intolerances],
        ['Dietary / Clinical Restrictions', hard.restrictions],
      ],
    },
    {
      key: 'soft',
      title: 'Preferences',
      description: 'Client preferences; these are not safety exclusions.',
      fields: [
        ['Preferred Cuisines', soft.preferredCuisines],
        ['Staple / Base Preference', soft.staplePreference],
        ['Dairy', soft.dairyPreference],
        ['Preferred Proteins', soft.preferredProteins],
        ['Likes', soft.likes],
        ['Dislikes', soft.dislikes],
        ['Practicality / Lifestyle', soft.practicality],
      ],
    },
  ];
}

export function formatFoodPreferenceValue(value) {
  if (Array.isArray(value)) return value.length ? value.join(', ') : 'Not provided';
  return value == null || value === '' ? 'Not provided' : String(value);
}
