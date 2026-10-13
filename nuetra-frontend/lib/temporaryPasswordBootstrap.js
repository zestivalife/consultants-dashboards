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
