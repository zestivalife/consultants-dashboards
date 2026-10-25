/** MP-011 UI visibility only; APIs, data and background execution are preserved. */
const roundTwoFeaturesEnabled = process.env.NEXT_PUBLIC_EXTERNAL_ROUND2_FEATURES === 'true';

export const CONSULTANT_FEATURE_VISIBILITY = Object.freeze({
  standaloneReports: roundTwoFeaturesEnabled,
  neckMeasurement: roundTwoFeaturesEnabled,
  automations: roundTwoFeaturesEnabled,
  governedPermissionCounts: roundTwoFeaturesEnabled,
  practiceSettings: roundTwoFeaturesEnabled,
  personalHealthProfileFields: roundTwoFeaturesEnabled,
});

export const CONSULTANT_VIEW_FEATURE = Object.freeze({
  reports: 'standaloneReports',
  automations: 'automations',
  settings: 'practiceSettings',
});

export function resolveConsultantFeatureVisibility(overrides = {}) {
  return Object.freeze({ ...CONSULTANT_FEATURE_VISIBILITY, ...overrides });
}

export function isConsultantFeatureVisible(feature, visibility = CONSULTANT_FEATURE_VISIBILITY) {
  return visibility[feature] !== false;
}

export function isConsultantViewVisible(view, visibility = CONSULTANT_FEATURE_VISIBILITY) {
  const feature = CONSULTANT_VIEW_FEATURE[view];
  return !feature || isConsultantFeatureVisible(feature, visibility);
}

export function filterConsultantNavigation(items, visibility = CONSULTANT_FEATURE_VISIBILITY) {
  return items.filter(([view]) => isConsultantViewVisible(view, visibility));
}
