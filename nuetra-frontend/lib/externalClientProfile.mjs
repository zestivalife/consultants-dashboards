export const EXTERNAL_HEALTH_GOALS = [
  'Weight management', 'Improve energy', 'Better sleep', 'Stress management',
  'Improve fitness', 'Manage a health condition', 'Improve nutrition', 'Healthy ageing',
];

const EXTERNAL_HEALTH_GOAL_ALIASES = {
  GAIN_WEIGHT: 'Weight management',
  LOSE_WEIGHT: 'Weight management',
  MAINTAIN_WEIGHT: 'Weight management',
  GAIN_MUSCLE: 'Improve fitness',
  IMPROVE_ENERGY: 'Improve energy',
  BETTER_SLEEP: 'Better sleep',
  STRESS_MANAGEMENT: 'Stress management',
  IMPROVE_FITNESS: 'Improve fitness',
  MANAGE_HEALTH_CONDITION: 'Manage a health condition',
  IMPROVE_NUTRITION: 'Improve nutrition',
  HEALTHY_AGEING: 'Healthy ageing',
};

export function normalizeExternalHealthGoals(value) {
  const unwrap = (input) => {
    if (Array.isArray(input)) return input;
    if (!input || typeof input !== 'object') return input == null || input === '' ? [] : [input];
    return unwrap(input.goals ?? input.selectedGoals ?? input.healthGoals ?? input.value ?? []);
  };
  return [...new Set(unwrap(value).map((goal) => {
    const raw = String(goal?.name ?? goal?.label ?? goal?.code ?? goal ?? '').trim();
    if (!raw) return '';
    return EXTERNAL_HEALTH_GOAL_ALIASES[raw.toUpperCase()] || raw.replaceAll('_', ' ').toLowerCase().replace(/^./, (letter) => letter.toUpperCase());
  }).filter(Boolean))].slice(0, 3);
}

const present = (value) => value !== null && value !== undefined && value !== '' && value !== 0 && (!Array.isArray(value) || value.length > 0);
const number = (value) => present(value) && Number.isFinite(Number(value)) ? Number(value) : null;
const clientName = (...values) => values
  .map((value) => String(value ?? '').trim())
  .find((value) => value && !['unnamed client', 'client', 'no contact provided'].includes(value.toLowerCase())) || '';

export function formatDateOnlyDDMMYYYY(value) {
  if (!value) return 'Not available';
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : 'Not available';
}

export function normalizeExternalDateOnly(value) {
  if (!value) return null;
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? `${match[1]}-${match[2]}-${match[3]}` : null;
}

export function calculateExternalBmi(heightCm, weightKg) {
  const height = number(heightCm); const weight = number(weightKg);
  if (height === null || weight === null || height <= 0 || weight <= 0) return null;
  return Math.round((weight / ((height / 100) ** 2)) * 10) / 10;
}

export function calculateExternalWaistHipRatio(waistCm, hipCm) {
  const waist = number(waistCm); const hip = number(hipCm);
  if (waist === null || hip === null || waist <= 0 || hip <= 0) return null;
  return Math.round((waist / hip) * 100) / 100;
}

export function calculateCalendarAge(value, today = new Date()) {
  const dateOnly = normalizeExternalDateOnly(value);
  if (!dateOnly) return null;
  const [year, month, day] = dateOnly.split('-').map(Number);
  const current = [today.getUTCFullYear(), today.getUTCMonth() + 1, today.getUTCDate()];
  if ([year, month, day].some((part) => !Number.isInteger(part)) || year > current[0] || (year === current[0] && (month > current[1] || (month === current[1] && day > current[2])))) return null;
  return current[0] - year - ((current[1] < month || (current[1] === month && current[2] < day)) ? 1 : 0);
}

const measurementKeys = {
  HEIGHT_CM: ['height', 'heightCm'], WEIGHT_KG: ['weight', 'weightKg'], WAIST_CM: ['waistCm'],
  HIP_CM: ['hipCm'], NECK_CM: ['neckCm'], CHEST_CM: ['chestCm'], MID_UPPER_ARM_CM: ['midUpperArmCm'],
  THIGH_CM: ['thighCm'], CALF_CM: ['calfCm'],
};

export function measurementValues(projection = {}) {
  const result = {};
  Object.entries(projection.latest || {}).forEach(([kind, item]) => {
    (measurementKeys[kind] || []).forEach((key) => { result[key] = item.value; });
  });
  return result;
}

export function externalClient360Base(client = {}, healthContext = null) {
  const context = healthContext && typeof healthContext === 'object' ? healthContext : {};
  const profileEnvelope = context.profile && typeof context.profile === 'object' ? context.profile : {};
  const profile = profileEnvelope.client && typeof profileEnvelope.client === 'object' ? profileEnvelope.client : profileEnvelope;
  const onboarding = profileEnvelope.onboarding && typeof profileEnvelope.onboarding === 'object' ? profileEnvelope.onboarding : {};
  const healthProfile = profileEnvelope.healthProfile && typeof profileEnvelope.healthProfile === 'object'
    ? profileEnvelope.healthProfile
    : context.healthProfile && typeof context.healthProfile === 'object' ? context.healthProfile : {};
  const suppliedSections = context.sections && typeof context.sections === 'object' ? context.sections : {};
  const reports = Array.isArray(context.reports) ? context.reports : [];
  const profileName = [profile.firstName || profile.first_name, profile.lastName || profile.last_name].filter(Boolean).join(' ');
  const authorisedProfileName = clientName(profile.displayName, profile.display_name, profile.name, profileName);
  const directoryName = clientName(client.displayName, client.display_name, client.clientName, client.name);
  const displayName = authorisedProfileName || directoryName || 'Unnamed client';
  const history = onboarding.healthHistory && typeof onboarding.healthHistory === 'object' ? onboarding.healthHistory : {};
  const lifestyle = onboarding.lifestyle && typeof onboarding.lifestyle === 'object' ? onboarding.lifestyle : {};
  const nutrition = onboarding.nutrition && typeof onboarding.nutrition === 'object' ? onboarding.nutrition : {};
  const bodyComposition = onboarding.bodyComposition && typeof onboarding.bodyComposition === 'object' ? onboarding.bodyComposition : {};
  const work = onboarding.work && typeof onboarding.work === 'object' ? onboarding.work : {};
  const measurements = context.measurements && typeof context.measurements === 'object' ? context.measurements : {};
  const healthMetrics = context.healthMetrics && typeof context.healthMetrics === 'object' ? context.healthMetrics : {};

  return {
    overview: {
      name: displayName,
      status: client.status || 'ACTIVE',
      primaryContact: client.email || client.mobile || profile.email || profile.mobile || null,
      dateOfBirth: profile.dateOfBirth || profile.date_of_birth || profile.dob || null,
      gender: profile.gender || null,
      missingSections: [],
      missingRequiredFields: [],
      documentCount: reports.length,
      dietPlanWarnings: [],
      primaryGoal: onboarding.goal || null,
    },
    basicProfile: Object.fromEntries(
      Object.entries({
        name: displayName,
        email: client.email || profile.email || null,
        mobile: client.mobile || profile.mobile || null,
        dateOfBirth: profile.dateOfBirth || profile.date_of_birth || profile.dob || null,
        gender: profile.gender || null,
      }).map(([key, value]) => [key, { value, sourceLabel: healthContext ? 'Fiteatsy' : 'Practice directory' }]),
    ),
    sections: {
      ...suppliedSections,
      aboutYou: suppliedSections.aboutYou || { ...profile, ...work },
      medicalHistory: suppliedSections.medicalHistory || healthProfile.medicalHistory || history,
      conditionsSymptoms: suppliedSections.conditionsSymptoms || healthProfile.conditionsSymptoms || { conditions: onboarding.medicalConditions || history.previousConditions },
      allergiesFamilyHistory: suppliedSections.allergiesFamilyHistory || healthProfile.allergiesFamilyHistory || { allergies: nutrition.foodAllergies, familyMedicalHistory: history.familyMedicalHistory },
      medicationsSupplements: suppliedSections.medicationsSupplements || healthProfile.medicationsSupplements || { medications: history.medications, supplements: nutrition.supplements || history.supplements },
      lifestyle: suppliedSections.lifestyle || healthProfile.lifestyle || { ...lifestyle, ...work },
      sleepStress: suppliedSections.sleepStress || healthProfile.sleepStress || { sleepHours: lifestyle.sleepHours, stressLevel: lifestyle.stressLevel },
      activityHydration: suppliedSections.activityHydration || healthProfile.activityHydration || { activityLevel: onboarding.activityLevel, exerciseFrequency: lifestyle.exerciseFrequency, waterIntakeLiters: nutrition.waterIntakeLiters },
      nutrition: suppliedSections.nutrition || context.nutritionSnapshot || nutrition,
      goals: suppliedSections.goals || healthProfile.goals || { primaryGoal: onboarding.goal, selectedGoals: onboarding.goals || [onboarding.goal].filter(Boolean) },
      measurements: suppliedSections.measurements || { ...bodyComposition, ...measurements },
      womensHealth: suppliedSections.womensHealth || healthProfile.womensHealth || {},
      reportsDocuments: suppliedSections.reportsDocuments || {},
    },
    documents: reports.map((report) => ({
      ...report,
      id: report.id || report.reportId || report.report_id,
      name: report.name || report.originalFilename || report.fileName || report.reportType || 'Health report',
      category: report.category || report.reportType || 'LAB_REPORT',
      sourceLabel: report.sourceLabel || 'Fiteatsy',
      mimeType: report.mimeType || report.contentType || 'application/octet-stream',
      status: report.status || 'ACTIVE',
      documentDate: report.documentDate || report.reportDate || null,
      uploadedAt: report.uploadedAt || report.createdAt || report.reportDate || null,
      processingStatus: report.processingStatus || 'COMPLETED',
      source: 'FITEATSY_CONNECTION',
    })),
    timeline: Array.isArray(context.timeline) ? context.timeline : [],
    provenance: context.provenance || {},
    consent: {
      source: healthContext ? 'FITEATSY_CONNECTION' : 'PRACTICE_DIRECTORY',
      scopes: Array.isArray(client.consentedScopes) ? client.consentedScopes : [],
      status: context.consent?.status || client.consentStatus || (client.healthDataAuthorized ? 'ACTIVE' : null),
    },
    healthMetrics,
  };
}

export function externalConnectedBiomarkers(healthContext = {}) {
  return (Array.isArray(healthContext.biomarkers) ? healthContext.biomarkers : []).map((item, index) => ({
    ...item,
    id: item.id || item.biomarkerId || `connected-biomarker-${index}`,
    canonicalBiomarkerId: item.canonicalBiomarkerId || item.biomarkerId || item.canonicalMarkerName || item.name || `connected-biomarker-${index}`,
    name: item.name || item.canonicalMarkerName || 'Biomarker',
    observationDate: item.observationDate || item.testDate || item.measuredAt || null,
    reviewStatus: item.reviewStatus || item.review_status || 'CONFIRMED',
    flag: item.flag || item.clinicalStatus || item.validationStatus || 'UNKNOWN',
    referenceText: item.referenceText || item.referenceRange || null,
    reportDownloadPath: item.reportDownloadPath || item.source?.filePath || null,
    source: 'FITEATSY_CONNECTION',
  }));
}

export function externalConnectedBiomarkerHistory(healthContext = {}, biomarker = {}) {
  const canonicalId = biomarker.canonicalBiomarkerId || biomarker.biomarkerId || biomarker.id;
  const matches = externalConnectedBiomarkers(healthContext).filter((item) =>
    (item.canonicalBiomarkerId || item.id) === canonicalId,
  );
  const rows = matches.flatMap((item) => Array.isArray(item.history) && item.history.length
    ? item.history.map((observation, index) => ({
      ...item,
      ...observation,
      id: observation.observationId || observation.id || `${item.id}-history-${index}`,
      observationDate: observation.observationDate || observation.testDate || observation.measuredAt || null,
      reviewStatus: observation.reviewStatus || observation.validationStatus || 'CONFIRMED',
      flag: observation.flag || observation.clinicalStatus || item.flag,
      source: 'FITEATSY_CONNECTION',
      sourceDetail: observation.source || item.sourceDetail || null,
    }))
    : [
      item,
      ...(item.previousValue == null ? [] : [{
        ...item,
        id: `${item.id}-previous`,
        value: item.previousValue,
        unit: item.previousUnit || item.unit,
        observationDate: item.previousTestDate || item.previousObservationDate || null,
        reviewStatus: 'CONFIRMED',
      }]),
    ]);
  return [...new Map(rows.filter((item) => item.observationDate).map((item) => [item.id, item])).values()]
    .sort((a, b) => String(b.observationDate).localeCompare(String(a.observationDate)));
}

export function externalConnectedHealthRecords(healthContext = {}) {
  const reports = Array.isArray(healthContext.reports) ? healthContext.reports : [];
  const biomarkers = externalConnectedBiomarkers(healthContext);
  return reports.map((report) => {
    const reportId = report.id || report.reportId || report.report_id;
    const observations = Array.isArray(report.biomarkers)
      ? report.biomarkers
      : biomarkers.filter((item) => (item.reportId || item.report_id || item.source?.reportId) === reportId);
    return {
      id: reportId,
      recordType: report.reportType || report.category || 'LAB_REPORT',
      sampleDate: report.reportDate || report.sampleDate || report.uploadedAt || report.createdAt || observations[0]?.observationDate || null,
      reportDate: report.reportDate || report.uploadedAt || report.createdAt || null,
      confirmedAt: report.confirmedAt || report.reviewedAt || report.completedAt || report.updatedAt || null,
      providerName: report.labName || report.providerName || null,
      biomarkerCount: observations.length,
      uploadedByType: report.uploadedByType || 'FITEATSY_CLIENT',
      reviewStatus: report.reviewStatus || (report.processingStatus === 'COMPLETED' ? 'CONFIRMED' : 'PENDING'),
      processingStatus: report.processingStatus || 'COMPLETED',
      status: 'ACTIVE',
      provenance: 'FITEATSY_CONNECTION',
      observations,
      connectionScoped: true,
    };
  });
}

export function composeExternalClientProfile(baseProfile, enrichment = {}, measurementProjection = {}) {
  const profile = structuredClone(baseProfile || {});
  const sectionKeys = [
    'aboutYou', 'medicalHistory', 'conditionsSymptoms', 'allergiesFamilyHistory',
    'medicationsSupplements', 'lifestyle', 'sleepStress', 'activityHydration',
    'nutrition', 'goals', 'measurements', 'womensHealth', 'reportsDocuments',
  ];
  const sections = Object.fromEntries(sectionKeys.map((key) => [key, { ...(profile.sections?.[key] || {}) }]));
  Object.entries(profile.sections || {}).forEach(([key, value]) => {
    if (!Object.prototype.hasOwnProperty.call(sections, key)) sections[key] = value || {};
  });
  const provenance = Object.fromEntries(sectionKeys.map((key) => [key, { ...(profile.provenance?.[key] || {}) }]));
  Object.entries(profile.provenance || {}).forEach(([key, value]) => {
    if (!Object.prototype.hasOwnProperty.call(provenance, key)) provenance[key] = value || {};
  });
  const baseMeasurements = sections.measurements || {};
  const measurements = enrichment.measurements || {};
  sections.measurements = {
    ...baseMeasurements,
    ...(present(measurements.height_cm) ? { height: measurements.height_cm, heightCm: measurements.height_cm } : {}),
    ...(present(measurements.weight_kg) ? { weight: measurements.weight_kg, weightKg: measurements.weight_kg } : {}),
    ...(present(measurements.waist_cm) ? { waistCm: measurements.waist_cm } : {}),
    ...(present(measurements.hip_cm) ? { hipCm: measurements.hip_cm } : {}),
    ...(present(measurements.neck_cm) ? { neckCm: measurements.neck_cm } : {}),
    ...(present(measurements.chest_cm) ? { chestCm: measurements.chest_cm } : {}),
    ...(present(measurements.mid_upper_arm_cm) ? { midUpperArmCm: measurements.mid_upper_arm_cm } : {}),
    ...(present(measurements.thigh_cm) ? { thighCm: measurements.thigh_cm } : {}),
    ...(present(measurements.calf_cm) ? { calfCm: measurements.calf_cm } : {}),
    ...(measurements.recorded_at ? { recordedAt: measurements.recorded_at } : {}),
    ...measurementValues(measurementProjection),
  };
  if (Object.prototype.hasOwnProperty.call(enrichment, 'goals')) {
    const goals = normalizeExternalHealthGoals(enrichment.goals);
    sections.goals = { ...(sections.goals || {}), selectedGoals: goals, primaryGoal: goals[0] || null };
  }
  if (Object.prototype.hasOwnProperty.call(enrichment, 'medical_history_narrative')) {
    sections.medicalHistory = { ...(sections.medicalHistory || {}), narrative: enrichment.medical_history_narrative };
  }
  if (Object.prototype.hasOwnProperty.call(enrichment, 'sleep_stress_narrative')) {
    sections.sleepStress = { ...(sections.sleepStress || {}), narrative: enrichment.sleep_stress_narrative };
  }
  const sectionOverlays = {
    allergies_family_history: 'allergiesFamilyHistory',
    activity_hydration: 'activityHydration',
    medications_supplements: 'medicationsSupplements',
    lifestyle: 'lifestyle',
  };
  Object.entries(sectionOverlays).forEach(([source, target]) => {
    if (Object.prototype.hasOwnProperty.call(enrichment, source)) {
      sections[target] = { ...(sections[target] || {}), ...(enrichment[source] || {}) };
    }
  });
  const overview = { ...(profile.overview || {}) };
  const canonicalDateOfBirth = normalizeExternalDateOnly(
    Object.prototype.hasOwnProperty.call(enrichment, 'date_of_birth')
      ? enrichment.date_of_birth
      : overview.dateOfBirth,
  );
  overview.dateOfBirth = canonicalDateOfBirth;
  overview.age = calculateCalendarAge(canonicalDateOfBirth);
  const height = sections.measurements.heightCm ?? sections.measurements.height;
  const weight = sections.measurements.weightKg ?? sections.measurements.weight;
  const bmi = calculateExternalBmi(height, weight);
  const waistHipRatio = calculateExternalWaistHipRatio(sections.measurements.waistCm, sections.measurements.hipCm);
  const categories = {
    personalProfile: [['Date of birth', overview.dateOfBirth], ['Health goals', sections.goals?.selectedGoals?.length || sections.goals?.primaryGoal]],
    medicalBackground: [
      ['Medical history', sections.medicalHistory?.narrative || sections.medicalHistory?.conditions],
      ['Allergy status', sections.allergiesFamilyHistory?.hasAllergies || sections.allergiesFamilyHistory?.allergies],
    ],
    bodyMeasurements: [['Height', height], ['Weight', weight], ['Waist', sections.measurements.waistCm], ['Hip', sections.measurements.hipCm]],
    lifestyle: [
      ['Sleep & stress', sections.sleepStress?.narrative || sections.sleepStress?.sleepQuality],
      ['Activity', sections.activityHydration?.activityLevel || sections.lifestyle?.physicalActivity],
      ['Hydration', sections.activityHydration?.waterIntakeMl || sections.activityHydration?.hydration || sections.activityHydration?.waterIntake || sections.lifestyle?.hydration],
    ],
  };
  const missingChecklist = Object.entries(categories).flatMap(([category, items]) => items.filter(([, value]) => !present(value)).map(([label]) => ({ category, label })));
  const requiredCount = Object.values(categories).flat().length;
  overview.profileCompleteness = Math.round(((requiredCount - missingChecklist.length) / requiredCount) * 100);
  overview.completeness = {categories, missingChecklist, clinicalEvidenceOptional: true};
  const datedRecords = Object.values(enrichment.health_record_dates || {}).filter((item) => item?.report_date && item?.confirmation_date).length;
  const evidenceUnits = [present(height) && present(weight), present(sections.measurements.waistCm) && present(sections.measurements.hipCm), datedRecords > 0];
  const evidenceCompleteness = Math.round((evidenceUnits.filter(Boolean).length / evidenceUnits.length) * 100);
  return {
    ...profile,
    overview,
    sections,
    provenance,
    derived: {
      ...(profile.derived || {}),
      healthMetrics: profile.healthMetrics || {},
      bmi: measurementProjection.calculations?.bmi || (bmi === null ? { status: 'NOT_AVAILABLE', value: null } : { status: 'AVAILABLE', value: bmi, unit: 'kg/m²', methodology: 'bmi.metric.v1' }),
      bmr: profile.healthMetrics?.bmr || null,
      tdee: profile.healthMetrics?.tdee || null,
      bodyFat: profile.healthMetrics?.bodyFat || null,
      targetHeartRate: profile.healthMetrics?.targetHeartRate || null,
      waistHipRatio,
      waistHipRatioMetric: measurementProjection.calculations?.waist_to_hip_ratio || (waistHipRatio == null ? null : {value: waistHipRatio, methodology: 'whr.metric.v1'}),
      waistToHeightRatio: measurementProjection.calculations?.waist_to_height_ratio || null,
      weightChange: measurementProjection.calculations?.weight_change || null,
      weightChangePercentage: measurementProjection.calculations?.weight_change_percentage || null,
      weightTrend: measurementProjection.calculations?.weight_trend || null,
    },
    externalEnrichment: enrichment,
    measurementProjection,
    evidenceCompleteness,
  };
}
