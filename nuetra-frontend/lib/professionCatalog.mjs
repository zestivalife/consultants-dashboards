export const PROFESSION_CATALOG = Object.freeze([
  { id: 'DIETITIAN', label: 'Dietitian / Nutritionist', eligibility: 'ENABLED', compatibleIds: ['NUTRITIONIST', 'CLINICAL_NUTRITIONIST', 'SPORTS_NUTRITIONIST'] },
  { id: 'HEALTH_COACH', label: 'Health Coach', eligibility: 'ENABLED' },
  { id: 'WELLNESS_COACH', label: 'Wellness Coach', eligibility: 'ENABLED' },
  { id: 'PSYCHOLOGIST', label: 'Psychologist', eligibility: 'DISABLED' },
  { id: 'COUNSELLOR', label: 'Counsellor / Therapist', eligibility: 'DISABLED' },
  { id: 'PHYSIOTHERAPIST', label: 'Physiotherapist', eligibility: 'OPTIONAL' },
  { id: 'FITNESS_TRAINER', label: 'Fitness Trainer', eligibility: 'ENABLED' },
  { id: 'YOGA_MEDITATION_COACH', label: 'Yoga / Meditation Coach', eligibility: 'OPTIONAL' },
  { id: 'DIABETES_EDUCATOR', label: 'Diabetes Educator', eligibility: 'ENABLED' },
  { id: 'WOMENS_HEALTH_PRACTITIONER', label: "Women's Health Practitioner", eligibility: 'ENABLED' },
  { id: 'LIFESTYLE_MEDICINE_PRACTITIONER', label: 'Lifestyle Medicine Practitioner', eligibility: 'ENABLED' },
  { id: 'MENTOR', label: 'Mentor', eligibility: 'DISABLED' },
  { id: 'DOCTOR_PHYSICIAN', label: 'Doctor / Physician', eligibility: 'ENABLED' },
  { id: 'OTHER', label: 'Other Healthcare Professional', eligibility: 'OPTIONAL' },
  { id: 'WELLNESS_CONSULTANT', label: 'Wellness Consultant', eligibility: 'ENABLED' },
  { id: 'BEHAVIOURAL_THERAPIST', label: 'Behavioural Therapist', eligibility: 'DISABLED' },
  { id: 'OCCUPATIONAL_THERAPIST', label: 'Occupational Therapist', eligibility: 'DISABLED' },
  { id: 'MENTAL_WELLNESS_THERAPIST', label: 'Mental Wellness Therapist', eligibility: 'DISABLED' },
]);

export const LEGACY_PROFESSION_ACCESS_ROLES = new Set(['dietician', 'dietitian', 'nutritionist']);

export function professionOption(value) {
  return PROFESSION_CATALOG.find((item) => item.id === value || item.compatibleIds?.includes(value)) || null;
}

export function dietEligibilityLabel(configuration) {
  if (!configuration || configuration.state !== 'CONFIGURED') return 'Profession not configured';
  if (configuration.diet_chart_authoring_enabled) return 'Standard draft authoring eligible';
  if (configuration.diet_chart_eligibility === 'OPTIONAL') return 'Administrator entitlement required';
  return 'Not eligible';
}
