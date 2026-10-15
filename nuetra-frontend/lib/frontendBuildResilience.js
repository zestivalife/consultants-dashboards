export const BUILD_RELOAD_ATTEMPT_KEY = 'nuetra_build_reload_target';
export const BUILD_SYNC_CHANNEL = 'nuetra_frontend_build_identity';

export const BUILD_GATE_STATE = Object.freeze({
  CURRENT: 'CURRENT',
  STALE: 'STALE_FRONTEND_BUILD',
  RECOVERY_REQUIRED: 'RECOVERY_REQUIRED',
  RUNTIME_UNAVAILABLE: 'RUNTIME_UNAVAILABLE',
});

function normalizeSha(value) {
  const sha = String(value || '').trim().toLowerCase();
  return /^[0-9a-f]{40}$/.test(sha) ? sha : null;
}

export function classifyFrontendBuild({ bundleSha, runtimeSha, attemptedRuntimeSha }) {
  const bundle = normalizeSha(bundleSha);
  const runtime = normalizeSha(runtimeSha);
  const attempted = normalizeSha(attemptedRuntimeSha);

  if (!bundle || !runtime) return BUILD_GATE_STATE.RUNTIME_UNAVAILABLE;
  if (bundle === runtime) return BUILD_GATE_STATE.CURRENT;
  if (attempted === runtime) return BUILD_GATE_STATE.RECOVERY_REQUIRED;
  return BUILD_GATE_STATE.STALE;
}

export function buildControlledReloadUrl(currentUrl, runtimeSha) {
  const url = new URL(currentUrl);
  url.searchParams.set('__nuetra_build', normalizeSha(runtimeSha));
  return url.toString();
}

export function shouldEnforceBuildIdentity(environment) {
  return environment === 'production';
}
