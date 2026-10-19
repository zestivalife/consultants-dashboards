const BASE_TABS = [
  'Overview', 'Care Team', 'Referrals', 'Progress Reports', 'Documents',
  'Resources & Homework', 'Billing', 'Health Profile', 'Health Records',
  'Reports', 'Goals / Progress', 'Timeline',
];

const PROFESSION_TABS = [
  'Overview', 'Profession', 'Care Team', 'Referrals', 'Progress Reports',
  'Documents', 'Programme', 'Resources & Homework', 'Billing',
  'Health Profile', 'Health Records', 'Reports', 'Goals / Progress', 'Biomarkers', 'Timeline',
];

const DIET_PROFESSIONS = new Set([
  'DIETITIAN', 'NUTRITIONIST', 'CLINICAL_NUTRITIONIST', 'SPORTS_NUTRITIONIST',
]);

const insertBefore = (items, before, values) => {
  const next = [...items];
  const index = next.indexOf(before);
  next.splice(index < 0 ? next.length : index, 0, ...values.filter(value => !next.includes(value)));
  return next;
};

export function resolveClient360Tabs(configuration = {}) {
  const profession = String(configuration.profession || '').toUpperCase();
  const capabilities = new Set((configuration.capabilities || []).map(value => String(value).toUpperCase()));
  const professionWorkspace = Boolean(configuration.professionWorkspace);
  let tabs = professionWorkspace ? [...PROFESSION_TABS] : [...BASE_TABS];
  const dietPlan = capabilities.has('DIET_PLAN') || capabilities.has('DIET_PLAN_AUTHORING');
  const biomarkers = capabilities.has('BIOMARKERS') || capabilities.has('LAB_ANALYSIS');
  const measurements = capabilities.has('MEASUREMENTS');
  const nutrition = DIET_PROFESSIONS.has(profession) || dietPlan;

  if (nutrition) tabs = insertBefore(tabs, 'Reports', ['Nutrition']);
  if (dietPlan) tabs = insertBefore(tabs, 'Reports', ['Diet Plan']);
  if (measurements) tabs = insertBefore(tabs, 'Reports', ['Measurements']);
  if (biomarkers) tabs = insertBefore(tabs, 'Timeline', ['Biomarkers']);
  return tabs;
}

export function client360CapabilityState(configuration = {}) {
  const capabilities = new Set((configuration.capabilities || []).map(value => String(value).toUpperCase()));
  return {
    dietPlan: capabilities.has('DIET_PLAN') || capabilities.has('DIET_PLAN_AUTHORING'),
    biomarkers: capabilities.has('BIOMARKERS') || capabilities.has('LAB_ANALYSIS'),
    measurements: capabilities.has('MEASUREMENTS'),
  };
}
