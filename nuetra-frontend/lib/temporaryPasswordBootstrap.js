export const TEMPORARY_PASSWORD_BOOTSTRAP_TIMEOUT_MS = 10000;

export const TEMPORARY_PASSWORD_BOOTSTRAP_VIEW = Object.freeze({
  FORM: 'form',
  LOADING: 'loading',
  ERROR: 'error',
});

export function getTemporaryPasswordBootstrapView({ user, isLoading, timedOut }) {
  if (user) return TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.FORM;
  if (isLoading && !timedOut) return TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.LOADING;
  return TEMPORARY_PASSWORD_BOOTSTRAP_VIEW.ERROR;
}

const EXTERNAL_TEMPORARY_PASSWORD_ROLES = new Set([
  'consultant',
  'external_consultant',
  'provider',
  'dietician',
  'dietitian',
]);

export function isExternalTemporaryPasswordUser(user) {
  return EXTERNAL_TEMPORARY_PASSWORD_ROLES.has(String(user?.role || '').trim().toLowerCase());
}

export function getExternalTemporaryPasswordIdentifier(user) {
  return String(
    user?.email
      || user?.mobile_number
      || user?.mobileNumber
      || user?.phone_number
      || user?.phoneNumber
      || ''
  ).trim();
}

export function isSameTemporaryPasswordUser(expectedUser, authenticatedUser) {
  const expectedId = String(expectedUser?.id || expectedUser?.user_id || '').trim();
  const authenticatedId = String(authenticatedUser?.id || authenticatedUser?.user_id || '').trim();
  return Boolean(expectedId && authenticatedId && expectedId === authenticatedId);
}
