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

export function composeExternalClientProfile(baseProfile, enrichment = {}, measurementProjection = {}) {
  const profile = structuredClone(baseProfile || {});
  const sections = { ...(profile.sections || {}) };
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
    medicalBackground: [['Medical history', sections.medicalHistory?.narrative || sections.medicalHistory?.conditions]],
    bodyMeasurements: [['Height', height], ['Weight', weight], ['Waist', sections.measurements.waistCm], ['Hip', sections.measurements.hipCm]],
    lifestyle: [['Sleep & stress', sections.sleepStress?.narrative || sections.sleepStress?.sleepQuality]],
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
    derived: {
      ...(profile.derived || {}),
      bmi: measurementProjection.calculations?.bmi || (bmi === null ? { status: 'NOT_AVAILABLE', value: null } : { status: 'AVAILABLE', value: bmi, unit: 'kg/m²', methodology: 'bmi.metric.v1' }),
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
