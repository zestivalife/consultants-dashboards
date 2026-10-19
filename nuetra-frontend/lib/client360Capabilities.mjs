const DIET_PROFESSIONS = new Set([
  'DIETITIAN', 'NUTRITIONIST', 'CLINICAL_NUTRITIONIST', 'SPORTS_NUTRITIONIST',
]);

const capabilitySet = (configuration = {}) => new Set(
  (configuration.capabilities || []).map(value => String(value).toUpperCase()),
);

export function client360CapabilityState(configuration = {}) {
  const capabilities = capabilitySet(configuration);
  return {
    dietPlan: capabilities.has('DIET_PLAN') || capabilities.has('DIET_PLAN_AUTHORING'),
    biomarkers: capabilities.has('BIOMARKERS') || capabilities.has('LAB_ANALYSIS'),
    measurements: capabilities.has('MEASUREMENTS'),
  };
}

export function resolveClient360Navigation(configuration = {}) {
  const profession = String(configuration.profession || '').toUpperCase();
  const capabilities = capabilitySet(configuration);
  const state = client360CapabilityState(configuration);
  const nutrition = DIET_PROFESSIONS.has(profession) || state.dietPlan;
  const professionWorkspace = Boolean(configuration.professionWorkspace);
  const progressReports = capabilities.has('PROGRESS_REPORTS') || capabilities.has('GOALS_PROGRESS');
  const careModules = [
    ...(professionWorkspace ? ['Profession', 'Programme'] : []),
    ...(nutrition ? ['Nutrition'] : []),
    ...(state.dietPlan ? ['Diet Plan'] : []),
    'Resources & Homework',
  ];

  return [
    { id: 'overview', label: 'Overview', modules: ['Overview'] },
    { id: 'health', label: 'Health', modules: ['Health Profile', ...(state.biomarkers ? ['Biomarkers'] : []), 'Health Records', ...(state.measurements ? ['Measurements'] : []), 'Reports'] },
    { id: 'care', label: nutrition ? 'Nutrition & Care' : 'Care', modules: careModules },
    { id: 'progress', label: 'Progress', modules: ['Goals / Progress', ...(progressReports ? ['Progress Reports'] : []), 'Timeline'] },
    { id: 'documents-admin', label: 'Documents & Admin', modules: ['Documents', 'Care Team', 'Referrals', 'Billing'] },
  ];
}

// Compatibility projection for callers that need the accessible module list.
export function resolveClient360Tabs(configuration = {}) {
  return resolveClient360Navigation(configuration).flatMap(section => section.modules);
}
