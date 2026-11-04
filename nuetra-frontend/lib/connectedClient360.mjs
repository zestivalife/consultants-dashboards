const list = (value) => Array.isArray(value) ? value : value == null || value === '' ? [] : [value];

export function projectConnectedClient360(client, healthContext = {}) {
  const profile = healthContext.profile || {};
  const person = profile.client || {};
  const onboarding = profile.onboarding || {};
  const nutrition = onboarding.nutrition || {};
  const history = onboarding.healthHistory || {};
  const measurements = healthContext.measurements || {};
  const reports = list(healthContext.reports);
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
      status: client.status === 'CONNECTED_CONSENT_ACTIVE' ? 'ACTIVE' : (person.status || 'ACTIVE'),
      primaryGoal: onboarding.goal || null,
      documentCount: reports.length,
      missingRequiredFields,
      missingSections: [],
      dietPlanWarnings: missingRequiredFields.length ? ['REQUIRED_FIELDS_MISSING'] : [],
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
      nutrition: { dietPreference: nutrition.dietaryPreference || onboarding.dietPreference || null, preferredCuisines: list(nutrition.preferredCuisines), foodDislikes: list(nutrition.foodDislikes), restrictions: list(nutrition.foodAllergies) },
      goals: { primaryGoal: onboarding.goal || null, selectedGoals: list(onboarding.goal) },
      measurements: { height: onboarding.height ?? measurements.heightCm ?? null, heightCm: onboarding.height ?? measurements.heightCm ?? null, weight: onboarding.weight ?? measurements.weightKg ?? null, weightKg: onboarding.weight ?? measurements.weightKg ?? null },
      womensHealth: { pregnancy: history.pregnancy || null, breastfeeding: history.breastfeeding || null },
      reportsDocuments: {},
    },
    provenance: {},
    consent: { status: client.relationshipStatus || client.status || 'CONNECTED_CONSENT_ACTIVE' },
    documents: reports.map((report) => ({
      id: report.id,
      name: report.fileName || report.originalFilename || report.name || 'Health report',
      category: 'LAB_REPORT', sourceLabel: 'Client shared', mimeType: report.mimeType || 'application/pdf',
      status: report.status || 'AVAILABLE', processingStatus: report.processingStatus || 'COMPLETED',
      documentDate: report.reportDate || report.testDate || null, uploadedAt: report.uploadedAt || report.createdAt || new Date().toISOString(),
      providerName: report.labName || null, notes: null,
    })),
    timeline: [],
    derived: { bmi: profile.healthMetrics?.bmi || healthContext.healthMetrics?.bmi || { status: 'NOT_AVAILABLE', value: null } },
  };
}
