const list = (value) => Array.isArray(value) ? value : value == null || value === '' ? [] : [value];

const deniedConnectionStates = new Set(['REVOKED', 'EXPIRED', 'DISCONNECTED', 'SUSPENDED', 'CONSENT_REVOKED', 'CONSENT_EXPIRED']);

const numericPercent = (value) => {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.max(0, Math.min(100, parsed)) : null;
};

export function canonicalOnboardingProjection(healthContext = {}) {
  const healthProfile = healthContext.profile?.healthProfile || healthContext.healthProfile || {};
  const completionPercent = numericPercent(
    healthProfile.completionPercent ?? healthProfile.completion_percent,
  );
  const completed = healthProfile.profileCompleted ?? healthProfile.profile_completed;
  const state = completed === true || completionPercent === 100
    ? 'COMPLETED'
    : completed === false || completionPercent !== null
      ? 'IN_PROGRESS'
      : 'UNAVAILABLE';
  return {
    state,
    completionPercent,
    source: 'FITEATSY_CANONICAL_PROFILE',
    updatedAt: healthProfile.updatedAt ?? healthProfile.updated_at ?? healthContext.generatedAt ?? null,
  };
}

export function hasAuthorizedHealthConnection(client = {}) {
  if (!client.connectionId) return false;
  const state = String(client.connectionState || client.relationshipStatus || client.status || '').toUpperCase();
  return !deniedConnectionStates.has(state) && state === 'ACTIVE';
}

export function projectDirectoryClient360(client) {
  return {
    overview: {
      id: client.id,
      name: client.displayName || client.name || 'Client',
      email: client.email || null,
      primaryContact: client.mobile || null,
      dateOfBirth: null,
      age: null,
      gender: null,
      status: client.status || 'ASSIGNED_CONNECTION_PENDING',
      primaryGoal: null,
      documentCount: null,
      missingRequiredFields: [],
      missingSections: [],
      dietPlanWarnings: ['CONSENT_PENDING'],
      fiteatsyAssessment: null,
    },
    sections: {
      aboutYou: {}, medicalHistory: {}, conditionsSymptoms: {}, allergiesFamilyHistory: {},
      medicationsSupplements: {}, lifestyle: {}, sleepStress: {}, activityHydration: {},
      nutrition: {}, goals: {}, measurements: {}, womensHealth: {}, reportsDocuments: {},
    },
    provenance: {},
    consent: { status: client.connectionState || client.relationshipStatus || client.status || 'ASSIGNED_CONNECTION_PENDING' },
    documents: [],
    timeline: [],
    derived: { bmi: { status: 'NOT_AVAILABLE', value: null } },
    onboarding: { state: 'ACCESS_RESTRICTED', completionPercent: null, source: 'CONSENT_REQUIRED', updatedAt: null },
  };
}

export function projectAuthorizedHealthContext(client, healthContext = {}) {
  const profile = healthContext.profile || {};
  const person = profile.client || {};
  const onboarding = profile.onboarding || {};
  const nutrition = onboarding.nutrition || {};
  const foodPreferences = healthContext.foodPreferences?.profile || {};
  const history = onboarding.healthHistory || {};
  const measurements = healthContext.measurements || {};
  const reports = list(healthContext.reports);
  const biomarkers = list(healthContext.biomarkers);
  const missingRequiredFields = [
    !person.dob && 'dateOfBirth',
    onboarding.height == null && 'height',
    onboarding.weight == null && 'weight',
    !onboarding.goal && 'primaryGoal',
  ].filter(Boolean);

  return {
    overview: {
      id: client.id,
      name: person.name || client.displayName || client.name || 'Client',
      email: person.email || client.email || null,
      primaryContact: person.mobile || client.mobile || null,
      dateOfBirth: person.dob || null,
      age: person.age ?? onboarding.age ?? null,
      gender: person.gender || onboarding.gender || null,
      status: 'ACTIVE',
      primaryGoal: onboarding.goal || null,
      documentCount: reports.length,
      missingRequiredFields,
      missingSections: [],
      dietPlanWarnings: missingRequiredFields.length ? ['REQUIRED_FIELDS_MISSING'] : [],
      fiteatsyAssessment: healthContext.assessment || null,
    },
    sections: {
      aboutYou: { dateOfBirth: person.dob || null, gender: person.gender || onboarding.gender || null },
      medicalHistory: { conditions: list(onboarding.medicalConditions), previousConditions: list(history.previousConditions), previousSurgeries: list(history.previousSurgeries), notes: history.medicalNotes || null },
      conditionsSymptoms: { conditions: list(onboarding.medicalConditions) },
      allergiesFamilyHistory: { allergies: list(nutrition.foodAllergies), familyMedicalHistory: list(history.familyMedicalHistory) },
      medicationsSupplements: { medications: list(history.medications) },
      lifestyle: { ...(onboarding.lifestyle || {}), activityLevel: onboarding.activityLevel || null },
      sleepStress: { sleepHours: onboarding.lifestyle?.sleepHours ?? null, sleepQuality: onboarding.lifestyle?.sleepQuality || null, stressLevel: onboarding.lifestyle?.stressLevel || null },
      activityHydration: { activityLevel: onboarding.activityLevel || null, waterIntakeLiters: nutrition.waterIntakeLiters ?? null },
      nutrition: {
        dietPreference: foodPreferences.dietType || nutrition.dietaryPreference || onboarding.dietPreference || null,
        proteins: list(foodPreferences.proteins),
        preferredCuisines: list(foodPreferences.cuisines).length ? list(foodPreferences.cuisines) : list(nutrition.preferredCuisines),
        foodsLiked: list(foodPreferences.foodsLiked),
        foodDislikes: list(foodPreferences.foodsDisliked).length ? list(foodPreferences.foodsDisliked) : list(nutrition.foodDislikes),
        foodsAvoided: list(foodPreferences.foodsAvoided),
        restrictions: list(foodPreferences.restrictions).length ? list(foodPreferences.restrictions) : list(nutrition.foodAllergies),
        staplePreference: foodPreferences.staplePreference || null,
        dairyPreference: foodPreferences.dairyPreference || null,
        practicality: list(foodPreferences.practicality),
      },
      goals: { primaryGoal: onboarding.goal || null, selectedGoals: list(onboarding.goal) },
      measurements: { height: onboarding.height ?? measurements.heightCm ?? null, heightCm: onboarding.height ?? measurements.heightCm ?? null, weight: onboarding.weight ?? measurements.weightKg ?? null, weightKg: onboarding.weight ?? measurements.weightKg ?? null },
      womensHealth: { pregnancy: history.pregnancy || null, breastfeeding: history.breastfeeding || null },
      reportsDocuments: {},
    },
    provenance: {},
    consent: { status: 'ACTIVE' },
    documents: reports.map((report) => ({
      id: report.id,
      name: report.fileName || report.originalFilename || report.name || 'Health report',
      category: 'LAB_REPORT',
      sourceLabel: 'Client shared',
      mimeType: report.mimeType || 'application/pdf',
      status: report.status || 'AVAILABLE',
      processingStatus: report.processingStatus || 'COMPLETED',
      documentDate: report.reportDate || report.testDate || null,
      uploadedAt: report.uploadedAt || report.createdAt || null,
      providerName: report.labName || null,
      notes: null,
    })),
    biomarkers: {
      latest: biomarkers,
      pendingReviewCount: biomarkers.filter((item) => String(item.reviewStatus || item.review_status || '').toUpperCase() === 'REVIEW_REQUIRED').length,
    },
    timeline: [],
    derived: { bmi: profile.healthMetrics?.bmi || healthContext.healthMetrics?.bmi || { status: 'NOT_AVAILABLE', value: null } },
    onboarding: canonicalOnboardingProjection(healthContext),
  };
}

export function reconcileAuthorizedMeasurements(client360 = {}, practiceMeasurements = {}) {
  const next = {
    ...practiceMeasurements,
    latest: { ...(practiceMeasurements.latest || {}) },
    history: Array.isArray(practiceMeasurements.history) ? practiceMeasurements.history : [],
    calculations: { ...(practiceMeasurements.calculations || {}) },
  };
  const canonical = client360.sections?.measurements || {};
  const occurredAt = client360.onboarding?.updatedAt || null;
  const addCanonical = (key, value, unit) => {
    if (next.latest[key] || value === null || value === undefined || value === '') return;
    next.latest[key] = {
      measurement_type: key,
      value: Number(value),
      unit,
      measured_at: occurredAt,
      source: 'FITEATSY_ONBOARDING',
      read_only: true,
    };
  };
  addCanonical('HEIGHT_CM', canonical.heightCm ?? canonical.height, 'cm');
  addCanonical('WEIGHT_KG', canonical.weightKg ?? canonical.weight, 'kg');
  return next;
}

export async function hydrateDirectoryOnboarding(clients = [], getHealthContext) {
  return Promise.all(clients.map(async (client) => {
    if (!hasAuthorizedHealthConnection(client)) {
      return { ...client, mobileOnboardingState: 'ACCESS_RESTRICTED', mobileOnboardingCompletionPercent: null };
    }
    const scopes = Array.isArray(client.consentedScopes) ? client.consentedScopes : [];
    if (scopes.length && !scopes.includes('PROFILE')) {
      return { ...client, mobileOnboardingState: 'ACCESS_RESTRICTED', mobileOnboardingCompletionPercent: null };
    }
    try {
      const projection = canonicalOnboardingProjection(await getHealthContext(client.connectionId));
      return {
        ...client,
        mobileOnboardingState: projection.state,
        mobileOnboardingCompletionPercent: projection.completionPercent,
        mobileOnboardingUpdatedAt: projection.updatedAt,
      };
    } catch {
      return { ...client, mobileOnboardingState: 'UNAVAILABLE', mobileOnboardingCompletionPercent: null };
    }
  }));
}

export async function loadAuthorizedClient360(client, getHealthContext) {
  if (!hasAuthorizedHealthConnection(client)) return projectDirectoryClient360(client);
  const healthContext = await getHealthContext(client.connectionId);
  return projectAuthorizedHealthContext(client, healthContext);
}
