export const INTERNAL_HEALTH_GOALS = [
  'Weight management', 'Improve energy', 'Better sleep', 'Stress management',
  'Improve fitness', 'Manage a health condition', 'Improve nutrition', 'Healthy ageing',
];

const has = (object, key) => Object.prototype.hasOwnProperty.call(object || {}, key);
const validNumber = (value) => value !== null && value !== '' && Number.isFinite(Number(value));

export function formatDateOnlyDDMMYYYY(value) {
  if (!value) return 'Not available';
  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? `${match[3]}/${match[2]}/${match[1]}` : 'Not available';
}

export function calculateBmi(heightCm, weightKg) {
  if (!validNumber(heightCm) || !validNumber(weightKg) || Number(heightCm) <= 0 || Number(weightKg) <= 0) return null;
  return Math.round((Number(weightKg) / ((Number(heightCm) / 100) ** 2)) * 10) / 10;
}

export function calculateWaistHipRatio(waistCm, hipCm) {
  if (!validNumber(waistCm) || !validNumber(hipCm) || Number(waistCm) <= 0 || Number(hipCm) <= 0) return null;
  return Math.round((Number(waistCm) / Number(hipCm)) * 100) / 100;
}

function enrichmentMeasurementsAreCurrent(profile, enrichment) {
  const recorded = enrichment?.measurements?.recorded_at;
  const baseUpdated = profile?.healthProfile?.updatedAtISO || profile?.onboarding?.updatedAtISO || profile?.syncMetadata?.lastSyncedAt;
  if (!recorded || !baseUpdated) return true;
  return Date.parse(recorded) >= Date.parse(baseUpdated);
}

export function calculateInternalProfileCompleteness(profile) {
  const fields = [
    profile?.client?.dateOfBirth || profile?.client?.dob,
    profile?.onboarding?.height,
    profile?.onboarding?.weight,
    (profile?.onboarding?.goals || []).length,
    profile?.onboarding?.medicalHistoryNarrative,
    profile?.onboarding?.sleepStressNarrative,
    profile?.onboarding?.bodyComposition?.waistCm,
    profile?.onboarding?.bodyComposition?.hipCm,
  ];
  const completed = fields.filter((value) => value !== null && value !== undefined && value !== '' && value !== 0).length;
  return Math.round((completed / fields.length) * 100);
}

export function composeInternalClientProfile(baseProfile, enrichment = {}) {
  const base = structuredClone(baseProfile || {});
  const measurements = enrichment.measurements || {};
  const currentMeasurements = enrichmentMeasurementsAreCurrent(base, enrichment) ? measurements : {};
  const onboarding = { ...(base.onboarding || {}) };
  const healthProfile = { ...(base.healthProfile || {}) };
  const bodyComposition = { ...(onboarding.bodyComposition || {}) };

  if (has(enrichment, 'goals')) {
    onboarding.goals = enrichment.goals;
    onboarding.goal = enrichment.goals?.[0] || null;
  }
  const map = {
    height_cm: 'height', weight_kg: 'weight', waist_cm: 'waistCm', hip_cm: 'hipCm',
    neck_cm: 'neckCm', goal_weight_kg: 'goalWeightKg', body_fat_percent: 'bodyFat',
  };
  Object.entries(map).forEach(([source, target]) => {
    if (!has(currentMeasurements, source)) return;
    if (source === 'height_cm' || source === 'weight_kg') onboarding[target] = currentMeasurements[source];
    else bodyComposition[target] = currentMeasurements[source];
  });
  if (has(enrichment, 'medical_history_narrative')) onboarding.medicalHistoryNarrative = enrichment.medical_history_narrative;
  if (has(enrichment, 'sleep_stress_narrative')) onboarding.sleepStressNarrative = enrichment.sleep_stress_narrative;
  onboarding.bodyComposition = bodyComposition;

  const derivedBmi = calculateBmi(onboarding.height, onboarding.weight);
  const derivedWhr = calculateWaistHipRatio(bodyComposition.waistCm, bodyComposition.hipCm);
  const reports = (base.reports || []).map((report) => {
    const id = String(report.id || report.reportId || '');
    const dates = enrichment.health_record_dates?.[id];
    return dates ? { ...report, enrichmentDates: dates } : report;
  });
  const composed = {
    ...base,
    onboarding,
    healthProfile,
    bodyMetrics: { ...(base.bodyMetrics || {}), ...(derivedBmi !== null ? { bmi: derivedBmi } : {}), ...(derivedWhr !== null ? { waistHipRatio: derivedWhr } : {}) },
    healthMetrics: { ...(base.healthMetrics || {}), ...(derivedBmi !== null ? { bmi: { status: 'AVAILABLE', value: derivedBmi, source: 'DERIVED_INTERNAL_MEASUREMENTS' } } : {}) },
    reports,
    internalEnrichment: enrichment,
    fieldProvenance: {
      ...(base.fieldProvenance || {}),
      ...(Object.keys(enrichment).length ? { internalEnrichment: enrichment.provenance || { source: 'INTERNAL_ENRICHMENT' } } : {}),
    },
  };
  composed.internalProfileCompleteness = calculateInternalProfileCompleteness(composed);
  return composed;
}
