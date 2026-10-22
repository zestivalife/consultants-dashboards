export const EXTERNAL_HEALTH_GOALS = [
  'Weight management', 'Improve energy', 'Better sleep', 'Stress management',
  'Improve fitness', 'Manage a health condition', 'Improve nutrition', 'Healthy ageing',
];

const present = (value) => value !== null && value !== undefined && value !== '' && value !== 0 && (!Array.isArray(value) || value.length > 0);
const number = (value) => present(value) && Number.isFinite(Number(value)) ? Number(value) : null;

export function formatDateOnlyDDMMYYYY(value) {
  if (!value) return 'Not available';
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : 'Not available';
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

export function composeExternalClientProfile(baseProfile, enrichment = {}) {
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
  };
  if (Object.prototype.hasOwnProperty.call(enrichment, 'goals')) {
    sections.goals = { ...(sections.goals || {}), selectedGoals: enrichment.goals, primaryGoal: enrichment.goals[0] || null };
  }
  if (Object.prototype.hasOwnProperty.call(enrichment, 'medical_history_narrative')) {
    sections.medicalHistory = { ...(sections.medicalHistory || {}), narrative: enrichment.medical_history_narrative };
  }
  if (Object.prototype.hasOwnProperty.call(enrichment, 'sleep_stress_narrative')) {
    sections.sleepStress = { ...(sections.sleepStress || {}), narrative: enrichment.sleep_stress_narrative };
  }
  const overview = { ...(profile.overview || {}) };
  if (Object.prototype.hasOwnProperty.call(enrichment, 'date_of_birth')) overview.dateOfBirth = enrichment.date_of_birth;
  const height = sections.measurements.heightCm ?? sections.measurements.height;
  const weight = sections.measurements.weightKg ?? sections.measurements.weight;
  const bmi = calculateExternalBmi(height, weight);
  const waistHipRatio = calculateExternalWaistHipRatio(sections.measurements.waistCm, sections.measurements.hipCm);
  const required = [
    overview.dateOfBirth,
    height,
    weight,
    sections.goals?.selectedGoals?.length || sections.goals?.primaryGoal,
    sections.medicalHistory?.narrative || sections.medicalHistory?.conditions,
    sections.sleepStress?.narrative || sections.sleepStress?.sleepQuality,
    sections.measurements.waistCm,
    sections.measurements.hipCm,
  ];
  const completed = required.filter(present).length;
  overview.profileCompleteness = Math.round((completed / required.length) * 100);
  const datedRecords = Object.values(enrichment.health_record_dates || {}).filter((item) => item?.report_date && item?.confirmation_date).length;
  const evidenceUnits = [present(height) && present(weight), present(sections.measurements.waistCm) && present(sections.measurements.hipCm), datedRecords > 0];
  const evidenceCompleteness = Math.round((evidenceUnits.filter(Boolean).length / evidenceUnits.length) * 100);
  return {
    ...profile,
    overview,
    sections,
    derived: {
      ...(profile.derived || {}),
      bmi: bmi === null ? { status: 'NOT_AVAILABLE', value: null } : { status: 'AVAILABLE', value: bmi, unit: 'kg/m²', source: 'EXTERNAL_CLIENT360_MEASUREMENTS' },
      waistHipRatio,
    },
    externalEnrichment: enrichment,
    evidenceCompleteness,
  };
}
